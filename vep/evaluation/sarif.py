"""VEP Evaluation: SARIF parser for CodeQL results.

Phase 2C: SARIF Integration
Parse CodeQL SARIF files and convert to Finding objects.
"""

import json
import re
from pathlib import Path
from typing import List

from vep.core.models import Finding
from vep.core.normalization import normalize_testcase_id, safe_int


# Pattern to extract BenchmarkTest from file paths
BENCHMARK_PATTERN = re.compile(r"(BenchmarkTest\d+)")


def load_sarif_findings(
    sarif_path: Path,
    tool: str = "codeql",
    cwe: str = None
) -> List[Finding]:
    """Load findings from CodeQL SARIF file.

    Args:
        sarif_path: Path to SARIF file
        tool: Tool name (default: codeql)
        cwe: Optional CWE filter

    Returns:
        List of Finding objects

    Note:
        Extracts testcase from file URI using BenchmarkTest pattern.
        If no testcase can be extracted, uses file stem or empty string.
    """
    sarif_path = Path(sarif_path)
    if not sarif_path.exists():
        raise FileNotFoundError(f"SARIF file not found: {sarif_path}")

    with sarif_path.open("r", encoding="utf-8") as f:
        sarif = json.load(f)

    findings = []
    runs = sarif.get("runs", [])

    if not runs:
        # Empty SARIF, return empty list
        return findings

    for run in runs:
        results = run.get("results", [])

        for result in results:
            # Extract ruleId
            rule_id = result.get("ruleId", "")

            # Extract message
            message_obj = result.get("message", {})
            message = message_obj.get("text", "") or message_obj.get("markdown", "")

            # Extract locations
            locations = result.get("locations", [])
            if not locations:
                # No location, create finding with minimal info
                finding = Finding(
                    testcase="",
                    rule_id=rule_id,
                    file="",
                    line=None,
                    tool=tool,
                    cwe=cwe,
                    message=message,
                    raw={"sarif_result": result}
                )
                findings.append(finding)
                continue

            for loc in locations:
                phys = loc.get("physicalLocation", {})
                artifact = phys.get("artifactLocation", {})
                uri = artifact.get("uri", "")

                region = phys.get("region", {})
                line = safe_int(region.get("startLine"))

                # Extract testcase from URI
                match = BENCHMARK_PATTERN.search(uri)
                if match:
                    testcase = match.group(1)
                else:
                    # Try to extract from message
                    msg_match = BENCHMARK_PATTERN.search(message)
                    if msg_match:
                        testcase = msg_match.group(1)
                    else:
                        # Use file stem or empty
                        testcase = Path(uri).stem if uri else ""

                # Normalize testcase
                testcase = normalize_testcase_id(testcase) if testcase else ""

                finding = Finding(
                    testcase=testcase,
                    rule_id=rule_id,
                    file=uri,
                    line=line,
                    tool=tool,
                    cwe=cwe,
                    message=message,
                    raw={"sarif_result": result}
                )
                findings.append(finding)

    return findings


def write_findings_csv(findings: List[Finding], csv_path: Path) -> None:
    """Write findings to normalized CSV file.

    Args:
        findings: List of Finding objects
        csv_path: Output CSV path

    Note:
        Output format: testcase,ruleId,file,line,message
    """
    import csv

    csv_path = Path(csv_path)
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["testcase", "ruleId", "file", "line", "message"])

        for finding in findings:
            writer.writerow([
                finding.testcase,
                finding.rule_id,
                finding.file,
                finding.line if finding.line is not None else "",
                finding.message or ""
            ])
