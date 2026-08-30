"""VEP Tools: tool protocol shared by CodeFuse and CodeQL adapters.

Phase 3 / M3.1: protocol and result types. Concrete implementations live in
vep.tools.codefuse and vep.tools.codeql.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Protocol

# Problem strings returned by check_environment():
#   - unprefixed entries are fatal and must block the tool run;
#   - entries prefixed with WARN_MARKER are advisory and must not block.
WARN_MARKER = "⚠️"


@dataclass
class ToolRunResult:
    """Outcome of a single tool invocation on one CWE.

    Attributes:
        tool: Tool name ("codefuse" or "codeql")
        cwe: CWE identifier (e.g., "CWE-022")
        raw_output: Path of the tool-native output (Godel JSON or SARIF)
        returncode: Tool process exit code
        log_file: Path of the captured tool log, if any
    """
    tool: str
    cwe: str
    raw_output: Optional[Path]
    returncode: int
    log_file: Optional[Path] = None


class Tool(Protocol):
    """Protocol implemented by every static-analysis tool adapter.

    check_environment() returns a list of human-readable problem strings;
    an empty list means the tool can run on this machine. Entries prefixed
    with WARN_MARKER are warnings; unprefixed entries are fatal.
    """

    name: str

    def check_environment(self) -> List[str]:
        """Validate tool availability and runtime environment."""
        ...

    def run(self, cwe: object, db: Path, out_dir: Path) -> ToolRunResult:
        """Run the tool for one CWE against a database."""
        ...

    def standardize(self, run: ToolRunResult, out_csv: Path) -> Path:
        """Convert the tool-native output into a normalized findings CSV."""
        ...
