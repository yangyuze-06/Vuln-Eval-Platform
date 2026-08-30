"""CodeFuse-Query (Godel) adapter: environment checks for Phase 3 / M3.1,
run + standardization for M3.2.

run() ports the godel invocation from scripts/evaluation/eval_checker.sh,
including the godel 2.1.0 package-root workaround (official lib and the
repo-local lib are merged into one temporary package root). standardize()
reuses scripts/converters/codefuse_json_to_csv.py as-is. The JAVA_HOME gate
reuses scripts/check_codefuse_java_env.py as-is (no second implementation).
"""

import csv
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
from functools import lru_cache
from pathlib import Path
from typing import List, Optional

from vep.core.manifest import CweEntry
from vep.tools.base import ToolRunResult, WARN_MARKER
from vep.tools.config import (
    CodeFusePaths,
    discover_codefuse,
    ToolsConfig,
)

JAVA_ENV_CHECK_SCRIPT = Path("scripts/check_codefuse_java_env.py")
JAVA_ENV_TIMEOUT_SECONDS = 120
CODEFUSE_CONVERTER_SCRIPT = Path("scripts/converters/codefuse_json_to_csv.py")


class CodeFuseTool:
    """Adapter for the CodeFuse-Query / Godel checker runner."""

    name = "codefuse"

    def __init__(
        self,
        config: ToolsConfig,
        project_root: Path,
        home: Optional[str] = None,
        godel_bin: Optional[str] = None,
        official_lib: Optional[str] = None,
        run_timeout_seconds: int = 3600,
    ):
        self.config = config
        self.project_root = project_root
        self.home_override = home
        self.godel_bin_override = godel_bin
        self.official_lib_override = official_lib
        self.run_timeout_seconds = run_timeout_seconds

    def check_environment(self) -> List[str]:
        problems: List[str] = []
        paths, notes = discover_codefuse(
            self.config,
            self.project_root,
            home_override=self.home_override,
            godel_bin_override=self.godel_bin_override,
            official_lib_override=self.official_lib_override,
        )
        problems.extend(note for note in notes if note.startswith(WARN_MARKER))

        if paths is None:
            problems.append(
                "❌ 找不到 CodeFuse/Sparrow 安装目录。"
                "请设置 CODEFUSE_HOME 环境变量，或在 configs/tools.yml 的 codefuse.home 指定。"
            )
            return problems

        problems.extend(_check_codefuse_paths(paths))
        if self.config.env_checks.codefuse_java_env:
            problems.extend(run_java_env_gate(self.project_root))
        return problems

    def run(self, cwe: CweEntry, db: Path, out_dir: Path) -> ToolRunResult:
        """Run the Godel checker for one CWE. Raises on configuration errors;
        tool failures are reported via ToolRunResult.returncode."""
        paths = self._discover_paths()
        rule_file = _require_rule_file(cwe)
        db_path = _resolve_db(db, self.project_root)

        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        out_json = out_dir / f"checker{cwe.id}.json"
        log_file = out_dir / f"{cwe.slug}_godel.log"

        # godel 2.1.0 resolves modules from one package root; merge official
        # and local libs into a temporary root (port of eval_checker.sh).
        package_root = Path(tempfile.mkdtemp(prefix="vep-godel-pkg-"))
        try:
            shutil.copytree(paths.official_lib, package_root, dirs_exist_ok=True)
            shutil.copytree(paths.local_lib, package_root, dirs_exist_ok=True)

            cmd = [
                str(paths.godel_bin),
                "-p", str(package_root),
                "-f", str(db_path),
                "-Of",
                "-r", str(rule_file),
                "--output-json", str(out_json),
            ]
            try:
                proc = subprocess.run(
                    cmd,
                    check=False,
                    text=True,
                    capture_output=True,
                    timeout=self.run_timeout_seconds,
                    cwd=str(self.project_root),
                )
                stdout, stderr, returncode = proc.stdout, proc.stderr, proc.returncode
            except subprocess.TimeoutExpired as exc:
                stdout = exc.stdout if isinstance(exc.stdout, str) else ""
                stderr = exc.stderr if isinstance(exc.stderr, str) else ""
                stderr = (stderr + f"\n[vep] timed out after {self.run_timeout_seconds}s").strip()
                returncode = 124

            log_file.write_text(
                f"$ {' '.join(cmd)}\n\n--- stdout ---\n{stdout}\n--- stderr ---\n{stderr}\n",
                encoding="utf-8",
            )
            raw_output = out_json if out_json.is_file() else None
            return ToolRunResult(
                tool=self.name,
                cwe=cwe.name,
                raw_output=raw_output,
                returncode=returncode,
                log_file=log_file,
            )
        finally:
            shutil.rmtree(package_root, ignore_errors=True)

    def standardize(self, run: ToolRunResult, out_csv: Path) -> Path:
        """Convert Godel JSON to the normalized findings CSV (dedup by
        testcase, reason column kept — same semantics as eval_checker.sh)."""
        if run.raw_output is None:
            raise RuntimeError(
                f"No raw output for {run.cwe} (tool returncode={run.returncode});"
                f" see log: {run.log_file}"
            )
        converter = _load_converter(self.project_root)
        records = converter.load_records(run.raw_output)
        rows = converter.build_rows(
            records,
            default_rule=run.cwe,
            include_reason=True,
            unknown_label="UNKNOWN",
        )
        rows = converter.dedup_by_testcase(rows)

        out_csv = Path(out_csv)
        out_csv.parent.mkdir(parents=True, exist_ok=True)
        with out_csv.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(["testcase", "ruleId", "file", "line", "reason"])
            writer.writerows(rows)
        return out_csv

    def _discover_paths(self) -> CodeFusePaths:
        paths, _notes = discover_codefuse(
            self.config,
            self.project_root,
            home_override=self.home_override,
            godel_bin_override=self.godel_bin_override,
            official_lib_override=self.official_lib_override,
        )
        if paths is None:
            raise RuntimeError(
                "CodeFuse home not found; run check_environment() for details."
            )
        if not (paths.godel_bin.is_file() and os.access(paths.godel_bin, os.X_OK)):
            raise RuntimeError(f"godel executable missing: {paths.godel_bin}")
        if not paths.official_lib.is_dir():
            raise RuntimeError(f"official CodeFuse lib missing: {paths.official_lib}")
        if not paths.local_lib.is_dir():
            raise RuntimeError(f"local rule lib missing: {paths.local_lib}")
        return paths


def _require_rule_file(cwe: CweEntry) -> Path:
    if cwe.codefuse_rule_file is None:
        raise ValueError(f"CWE {cwe.id} has no codefuse.rule_file in the manifest")
    if not cwe.codefuse_rule_file.is_file():
        raise FileNotFoundError(f"Rule file not found: {cwe.codefuse_rule_file}")
    return cwe.codefuse_rule_file


def _resolve_db(db: Path, project_root: Path) -> Path:
    db_path = Path(db)
    if not db_path.is_absolute():
        db_path = project_root / db_path
    if not db_path.is_dir():
        raise FileNotFoundError(f"CodeFuse database not found: {db_path}")
    return db_path


@lru_cache(maxsize=None)
def _load_converter(project_root: Path):
    script = project_root / CODEFUSE_CONVERTER_SCRIPT
    if not script.is_file():
        raise FileNotFoundError(f"Converter script not found: {script}")
    spec = importlib.util.spec_from_file_location("vep_codefuse_json_to_csv", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _check_codefuse_paths(paths: CodeFusePaths) -> List[str]:
    problems: List[str] = []
    if not (paths.godel_bin.is_file() and os.access(paths.godel_bin, os.X_OK)):
        problems.append(f"❌ godel 可执行文件缺失或不可执行: {paths.godel_bin}")
    if not paths.official_lib.is_dir():
        problems.append(
            f"❌ 找不到官方 CodeFuse-Query lib 目录: {paths.official_lib}"
            "（确认 CODEFUSE_HOME 指向 sparrow-cli 根目录）"
        )
    if not paths.local_lib.is_dir():
        problems.append(f"❌ 找不到仓库本地规则库: {paths.local_lib}")
    return problems


def run_java_env_gate(
    project_root: Path,
    python_executable: Optional[str] = None,
) -> List[str]:
    """Run scripts/check_codefuse_java_env.py and map its findings to problems.

    Exit codes follow the script's own contract: 0=PASS, 1=FAIL, 2=WARN.
    """
    script = project_root / JAVA_ENV_CHECK_SCRIPT
    if not script.is_file():
        return [f"❌ JAVA_HOME 检查脚本缺失: {script}"]

    cmd = [
        python_executable or sys.executable,
        str(script),
        "--json",
        "--quiet",
    ]
    try:
        proc = subprocess.run(
            cmd,
            check=False,
            text=True,
            capture_output=True,
            timeout=JAVA_ENV_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return [f"❌ JAVA_HOME 检查脚本执行失败: {exc}"]

    if proc.returncode not in (0, 1, 2):
        stderr = (proc.stderr or "").strip()
        return [
            f"❌ JAVA_HOME 检查脚本异常退出 (returncode={proc.returncode}): {stderr[:300]}"
        ]
    if proc.returncode == 0:
        return []

    try:
        evidence = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return [f"❌ JAVA_HOME 检查脚本输出无法解析: {proc.stdout[:300]}"]

    problems: List[str] = []
    for item in evidence.get("results", []):
        level = item.get("level")
        message = item.get("message", "")
        detail = item.get("detail", "")
        text = f"{message}（{detail}）" if detail else message
        if level == "FAIL":
            problems.append(f"❌ JAVA_HOME 检查: {text}")
        elif level == "WARN":
            problems.append(f"{WARN_MARKER} JAVA_HOME 检查: {text}")
    if not problems:
        problems.append(f"❌ JAVA_HOME 检查未通过 (returncode={proc.returncode})，但未返回明细。")
    recommendations = evidence.get("recommendations") or []
    if recommendations:
        problems.append("ℹ️  建议修复: " + "; ".join(recommendations))
    return problems
