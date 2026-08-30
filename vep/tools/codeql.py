"""CodeQL adapter: environment checks for Phase 3 / M3.1, run +
standardization for M3.2.

run() ports `codeql database analyze` from scripts/run_codeql_experiments.py
(query directory comes from the manifest, which handles the CWE-328_328S
special case). standardize() reuses vep.evaluation.sarif.
"""

import os
import subprocess
from pathlib import Path
from typing import List, Optional

from vep.core.manifest import CweEntry
from vep.evaluation.sarif import load_sarif_findings, write_findings_csv
from vep.tools.base import ToolRunResult
from vep.tools.config import discover_codeql, ToolsConfig

SARIF_FORMAT = "sarifv2.1.0"


class CodeQLTool:
    """Adapter for `codeql database analyze`."""

    name = "codeql"

    def __init__(
        self,
        config: ToolsConfig,
        project_root: Path,
        bin_path: Optional[str] = None,
        run_timeout_seconds: int = 3600,
    ):
        self.config = config
        self.project_root = project_root
        self.bin_override = bin_path
        self.run_timeout_seconds = run_timeout_seconds

    def check_environment(self) -> List[str]:
        problems: List[str] = []
        bin_path, _notes = discover_codeql(
            self.config,
            self.project_root,
            bin_override=self.bin_override,
        )
        if bin_path is None:
            problems.append(
                "❌ 找不到 codeql CLI。请安装 CodeQL 并加入 PATH，"
                "或设置 CODEQL_BIN 环境变量 / configs/tools.yml 的 codeql.bin。"
            )
            return problems
        if not (bin_path.is_file() and os.access(bin_path, os.X_OK)):
            problems.append(f"❌ codeql 可执行文件缺失或不可执行: {bin_path}")
        return problems

    def run(self, cwe: CweEntry, db: Path, out_dir: Path) -> ToolRunResult:
        """Run `codeql database analyze` for one CWE. Raises on configuration
        errors; tool failures are reported via ToolRunResult.returncode."""
        bin_path, _notes = discover_codeql(
            self.config,
            self.project_root,
            bin_override=self.bin_override,
        )
        if bin_path is None:
            raise RuntimeError("codeql CLI not found; run check_environment() for details.")
        if cwe.codeql_rule_directory is None:
            raise ValueError(f"CWE {cwe.id} has no codeql.rule_directory in the manifest")
        if not cwe.codeql_rule_directory.is_dir():
            raise FileNotFoundError(f"CodeQL rule directory not found: {cwe.codeql_rule_directory}")

        db_path = Path(db)
        if not db_path.is_absolute():
            db_path = self.project_root / db_path
        if not db_path.is_dir():
            raise FileNotFoundError(f"CodeQL database not found: {db_path}")

        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        sarif_out = out_dir / f"cwe{cwe.id}.sarif"
        log_file = out_dir / f"{cwe.slug}_codeql.log"

        cmd = [
            str(bin_path),
            "database", "analyze",
            str(db_path),
            str(cwe.codeql_rule_directory),
            f"--format={SARIF_FORMAT}",
            f"--output={sarif_out}",
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
        raw_output = sarif_out if sarif_out.is_file() else None
        return ToolRunResult(
            tool=self.name,
            cwe=cwe.name,
            raw_output=raw_output,
            returncode=returncode,
            log_file=log_file,
        )

    def standardize(self, run: ToolRunResult, out_csv: Path) -> Path:
        """Convert SARIF to the normalized findings CSV via vep.evaluation.sarif."""
        if run.raw_output is None:
            raise RuntimeError(
                f"No raw output for {run.cwe} (tool returncode={run.returncode});"
                f" see log: {run.log_file}"
            )
        findings = load_sarif_findings(run.raw_output, tool=self.name, cwe=run.cwe)
        out_csv = Path(out_csv)
        out_csv.parent.mkdir(parents=True, exist_ok=True)
        write_findings_csv(findings, out_csv)
        return out_csv
