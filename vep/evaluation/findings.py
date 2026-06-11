"""VEP Evaluation: Load findings from normalized CSV files.

Phase 2: Unified Evaluation Core
"""

import csv
from pathlib import Path
from typing import List, Optional

from vep.core.models import Finding
from vep.core.normalization import normalize_testcase_id, safe_int


def load_findings_csv(
    path: Path,
    tool: Optional[str] = None,
    cwe: Optional[str] = None
) -> List[Finding]:
    """Load findings from normalized CSV file.

    Expected CSV columns (flexible):
        - testcase (or: name, className, class)
        - ruleId (or: rule_id, rule, cwe, cweid)
        - file (or: path, filename, srcFile, sinkFile)
        - line (optional)
        - reason / message (optional)

    Args:
        path: Path to normalized findings CSV
        tool: Tool name to assign to findings (optional)
        cwe: CWE filter (not implemented, for future use)

    Returns:
        List of Finding objects

    Note:
        If testcase column is missing, attempts to extract from file column.
        Extra columns are preserved in Finding.raw dict.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Findings CSV not found: {path}")

    findings = []

    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)

        for row in reader:
            # Normalize field names (case-insensitive lookup)
            row_lower = {k.lower(): v for k, v in row.items()}

            # Extract testcase (try multiple field names)
            testcase = (
                row.get("testcase") or row.get("name") or
                row.get("className") or row.get("class") or
                row_lower.get("testcase") or row_lower.get("classname") or ""
            )

            # If still empty, try to extract from file field
            if not testcase:
                file_field = (
                    row.get("file") or row.get("path") or
                    row.get("srcFile") or row.get("sinkFile") or ""
                )
                testcase = normalize_testcase_id(file_field)

            # Normalize testcase
            testcase = normalize_testcase_id(testcase)

            # Extract rule_id
            rule_id = (
                row.get("ruleId") or row.get("rule_id") or
                row.get("rule") or row.get("cwe") or
                row.get("cweid") or row_lower.get("ruleid") or ""
            )

            # Extract file
            file = (
                row.get("file") or row.get("path") or
                row.get("filename") or row.get("srcFile") or
                row.get("sinkFile") or ""
            )

            # Extract line
            line_str = row.get("line") or row.get("startLine") or ""
            line = safe_int(line_str)

            # Extract message/reason
            message = row.get("reason") or row.get("message") or row.get("msg") or ""

            # Create Finding
            finding = Finding(
                testcase=testcase,
                rule_id=rule_id,
                file=file,
                line=line,
                tool=tool,
                cwe=cwe,
                message=message,
                raw=dict(row)  # Preserve all original fields
            )

            findings.append(finding)

    return findings
