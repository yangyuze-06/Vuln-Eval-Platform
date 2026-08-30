"""CodeQL adapter: environment checks for Phase 3 / M3.1.

run()/standardize() are implemented in M3.2 (database analyze + SARIF
standardization via vep.evaluation.sarif).
"""

import os
from pathlib import Path
from typing import List, Optional

from vep.tools.base import ToolRunResult
from vep.tools.config import discover_codeql, ToolsConfig


class CodeQLTool:
    """Adapter for `codeql database analyze`."""

    name = "codeql"

    def __init__(
        self,
        config: ToolsConfig,
        project_root: Path,
        bin_path: Optional[str] = None,
    ):
        self.config = config
        self.project_root = project_root
        self.bin_override = bin_path

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

    def run(self, cwe: object, db: Path, out_dir: Path) -> ToolRunResult:
        """Run `codeql database analyze` for one CWE (Phase 3 / M3.2)."""
        raise NotImplementedError("CodeQLTool.run lands in Phase 3 / M3.2")

    def standardize(self, run: ToolRunResult, out_csv: Path) -> Path:
        """Convert SARIF to normalized findings CSV (Phase 3 / M3.2)."""
        raise NotImplementedError("CodeQLTool.standardize lands in Phase 3 / M3.2")
