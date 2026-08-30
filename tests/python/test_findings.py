"""Unit tests for vep.evaluation.findings (Phase 4 / M4.2)."""

import pytest

from vep.evaluation.findings import load_findings_csv


def write_csv(tmp_path, name, content):
    path = tmp_path / name
    path.write_text(content, encoding="utf-8")
    return path


class TestLoadFindingsCsv:
    def test_codefuse_five_column_format(self, tmp_path):
        csv_path = write_csv(tmp_path, "codefuse.csv",
            "testcase,ruleId,file,line,reason\n"
            "BenchmarkTest00001,CWE-022,org/x/BenchmarkTest00001.java,88,some reason\n"
            "BenchmarkTest00002,CWE-022,org/x/BenchmarkTest00002.java,12,\n"
        )
        findings = load_findings_csv(csv_path, tool="codefuse", cwe="CWE-022")
        assert len(findings) == 2
        assert findings[0].testcase == "BenchmarkTest00001"
        assert findings[0].rule_id == "CWE-022"
        assert findings[0].line == 88
        assert findings[0].tool == "codefuse"
        assert findings[1].message == ""

    def test_codeql_legacy_four_column_format(self, tmp_path):
        # Old sarif_to_csv.py output: testcase,ruleId,file,line (no reason)
        csv_path = write_csv(tmp_path, "codeql.csv",
            "testcase,ruleId,file,line\n"
            "BenchmarkTest00012,java/ldap-injection,src/main/java/x.java,68\n"
        )
        findings = load_findings_csv(csv_path, tool="codeql")
        assert len(findings) == 1
        assert findings[0].testcase == "BenchmarkTest00012"
        assert findings[0].rule_id == "java/ldap-injection"
        assert findings[0].line == 68
        assert findings[0].message == ""

    def test_missing_testcase_extracted_from_file(self, tmp_path):
        csv_path = write_csv(tmp_path, "no_tc.csv",
            "testcase,ruleId,file,line\n"
            ",CWE-089,org/owasp/benchmark/testcode/BenchmarkTest00042.java,7\n"
        )
        findings = load_findings_csv(csv_path)
        assert findings[0].testcase == "BenchmarkTest00042"

    def test_v2_sarif_csv_format(self, tmp_path):
        # vep.evaluation.sarif.write_findings_csv output (testcaseId/sinkFile order)
        csv_path = write_csv(tmp_path, "v2.csv",
            "testcase,ruleId,file,line,message\n"
            "BenchmarkTest00003,java/xss,src/x.java,5,hello\n"
        )
        findings = load_findings_csv(csv_path)
        assert findings[0].testcase == "BenchmarkTest00003"
        assert findings[0].message == "hello"

    def test_missing_file_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_findings_csv(tmp_path / "nope.csv")
