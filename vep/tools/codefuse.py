"""CodeFuse-Query (Godel) adapter: environment checks for Phase 3 / M3.1.

run()/standardize() are implemented in M3.2; the discovery and environment
gate here port scripts/evaluation/eval_checker.sh and reuse
scripts/check_codefuse_java_env.py as-is (no second JAVA_HOME implementation).
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import List, Optional

from vep.tools.base import ToolRunResult, WARN_MARKER
from vep.tools.config import (
    CodeFusePaths,
    discover_codefuse,
    ToolsConfig,
)

JAVA_ENV_CHECK_SCRIPT = Path("scripts/check_codefuse_java_env.py")
JAVA_ENV_TIMEOUT_SECONDS = 120


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
    ):
        self.config = config
        self.project_root = project_root
        self.home_override = home
        self.godel_bin_override = godel_bin
        self.official_lib_override = official_lib

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

    def run(self, cwe: object, db: Path, out_dir: Path) -> ToolRunResult:
        """Run the Godel checker for one CWE (implemented in Phase 3 / M3.2)."""
        raise NotImplementedError("CodeFuseTool.run lands in Phase 3 / M3.2")

    def standardize(self, run: ToolRunResult, out_csv: Path) -> Path:
        """Convert Godel JSON to normalized findings CSV (Phase 3 / M3.2)."""
        raise NotImplementedError("CodeFuseTool.standardize lands in Phase 3 / M3.2")


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
