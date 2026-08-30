"""Unit tests for vep.evaluation.sarif (Phase 4 / M4.2)."""

import json

import pytest

from vep.evaluation.findings import load_findings_csv
from vep.evaluation.sarif import load_sarif_findings, write_findings_csv

URI_TEMPLATE = "src/main/java/org/owasp/benchmark/testcode/{}.java"


def make_sarif(tmp_path, results):
    sarif = {"version": "2.1.0", "runs": [{"results": results}]}
    path = tmp_path / "findings.sarif"
    path.write_text(json.dumps(sarif), encoding="utf-8")
    return path


def result_for(testcase, line, rule="java/xss"):
    return {
        "ruleId": rule,
        "message": {"text": f"finding in {testcase}"},
        "locations": [{
            "physicalLocation": {
                "artifactLocation": {"uri": URI_TEMPLATE.format(testcase)},
                "region": {"startLine": line},
            }
        }],
    }


class TestLoadSarifFindings:
    def test_extracts_testcase_file_line(self, tmp_path):
        sarif = make_sarif(tmp_path, [result_for("BenchmarkTest00001", 88)])
        findings = load_sarif_findings(sarif, tool="codeql", cwe="CWE-079")
        assert len(findings) == 1
        assert findings[0].testcase == "BenchmarkTest00001"
        assert findings[0].rule_id == "java/xss"
        assert findings[0].line == 88
        assert findings[0].tool == "codeql"

    def test_result_without_locations_kept_with_empty_testcase(self, tmp_path):
        sarif = make_sarif(tmp_path, [{
            "ruleId": "java/xss",
            "message": {"text": "no location"},
            "locations": [],
        }])
        findings = load_sarif_findings(sarif)
        assert len(findings) == 1
        assert findings[0].testcase == ""
        assert findings[0].file == ""
        assert findings[0].line is None

    def test_testcase_fallback_from_message(self, tmp_path):
        sarif = make_sarif(tmp_path, [{
            "ruleId": "java/xss",
            "message": {"text": "issue at BenchmarkTest00077"},
            "locations": [{
                "physicalLocation": {"artifactLocation": {"uri": "unknown/path.java"}}
            }],
        }])
        findings = load_sarif_findings(sarif)
        assert findings[0].testcase == "BenchmarkTest00077"

    def test_empty_runs_returns_empty(self, tmp_path):
        sarif = make_sarif(tmp_path, [])
        assert load_sarif_findings(sarif) == []

    def test_missing_file_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_sarif_findings(tmp_path / "nope.sarif")


class TestWriteFindingsCsv:
    def test_roundtrip_through_findings_loader(self, tmp_path):
        sarif = make_sarif(tmp_path, [
            result_for("BenchmarkTest00001", 88),
            result_for("BenchmarkTest00002", 12, rule="java/sql-injection"),
        ])
        findings = load_sarif_findings(sarif, tool="codeql", cwe="CWE-079")
        csv_path = tmp_path / "findings.csv"
        write_findings_csv(findings, csv_path)

        reloaded = load_findings_csv(csv_path, tool="codeql", cwe="CWE-079")
        assert {(f.testcase, f.rule_id, f.line) for f in reloaded} == {
            ("BenchmarkTest00001", "java/xss", 88),
            ("BenchmarkTest00002", "java/sql-injection", 12),
        }

    def test_csv_header_and_columns(self, tmp_path):
        sarif = make_sarif(tmp_path, [result_for("BenchmarkTest00001", 88)])
        csv_path = tmp_path / "findings.csv"
        write_findings_csv(load_sarif_findings(sarif), csv_path)
        header = csv_path.read_text(encoding="utf-8").splitlines()[0]
        assert header == "testcase,ruleId,file,line,message"
