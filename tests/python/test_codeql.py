"""Unit tests for vep.tools.codeql (Phase 4 / M4.3).

Uses a fake `codeql` executable that writes a deterministic SARIF file, then
verifies the run -> standardize path end-to-end through the real SARIF parser.
"""

import textwrap
from pathlib import Path

import pytest

from vep.core.manifest import CweEntry
from vep.tools.codeql import CodeQLTool
from vep.tools.config import load_tools_config

REPO_ROOT = Path(__file__).resolve().parents[2]

FAKE_CODEQL = textwrap.dedent("""\
    #!/bin/bash
    # fake codeql: emit a deterministic SARIF at the --output target
    out=""
    for a in "$@"; do
      case "$a" in --output=*) out="${a#--output=}";; esac
    done
    cat > "$out" <<'JSON'
    {
      "version": "2.1.0",
      "runs": [{
        "tool": {"driver": {"name": "fake-codeql"}},
        "results": [{
          "ruleId": "java/ldap-injection",
          "message": {"text": "ldap injection"},
          "locations": [{
            "physicalLocation": {
              "artifactLocation": {
                "uri": "src/main/java/org/owasp/benchmark/testcode/BenchmarkTest00012.java"
              },
              "region": {"startLine": 68}
            }
          }]
        }]
      }]
    }
    JSON
""")


def make_fake_codeql(tmp_path):
    fake = tmp_path / "codeql"
    fake.write_text(FAKE_CODEQL, encoding="utf-8")
    fake.chmod(0o755)
    return fake


@pytest.fixture
def config():
    return load_tools_config(config_file=Path("/nonexistent/tools.yml"))


@pytest.fixture
def entry(tmp_path):
    rule_dir = tmp_path / "rules" / "CWE-999"
    rule_dir.mkdir(parents=True)
    (rule_dir / "query.ql").write_text("// fake query\n", encoding="utf-8")
    return CweEntry(
        id="999", name="CWE-999", slug="cwe-999", slug_compact="cwe999",
        codeql_rule_directory=rule_dir,
        experiments_directory=tmp_path / "experiments" / "cwe-999",
    )


@pytest.fixture
def db(tmp_path):
    db_dir = tmp_path / "db"
    db_dir.mkdir()
    return db_dir


class TestCheckEnvironment:
    def test_clean_with_fake_bin(self, tmp_path, config):
        tool = CodeQLTool(config, REPO_ROOT, bin_path=str(make_fake_codeql(tmp_path)))
        assert tool.check_environment() == []

    def test_bin_not_found(self, tmp_path, config):
        tool = CodeQLTool(config, REPO_ROOT, bin_path="definitely-not-codeql-xyz")
        problems = tool.check_environment()
        assert any("找不到 codeql CLI" in p for p in problems)

    def test_bin_path_not_executable(self, tmp_path, config):
        fake = tmp_path / "codeql-broken"
        fake.write_text("#!/bin/sh\n", encoding="utf-8")  # not executable
        tool = CodeQLTool(config, REPO_ROOT, bin_path=str(fake))
        problems = tool.check_environment()
        assert any("不可执行" in p for p in problems)


class TestRun:
    def test_run_writes_sarif_and_log(self, tmp_path, config, entry, db):
        tool = CodeQLTool(config, REPO_ROOT, bin_path=str(make_fake_codeql(tmp_path)))
        out_dir = tmp_path / "out"

        result = tool.run(entry, db, out_dir)

        assert result.returncode == 0
        assert result.raw_output == out_dir / "cwe999.sarif"
        assert result.raw_output.is_file()
        assert result.log_file.is_file()
        assert "database" in result.log_file.read_text(encoding="utf-8")

    def test_missing_rule_directory_raises(self, tmp_path, config, db):
        tool = CodeQLTool(config, REPO_ROOT, bin_path=str(make_fake_codeql(tmp_path)))
        broken = CweEntry(id="999", name="CWE-999", slug="cwe-999", slug_compact="cwe999")
        with pytest.raises(ValueError, match="rule_directory"):
            tool.run(broken, db, tmp_path / "out")

    def test_missing_db_raises(self, tmp_path, config, entry):
        tool = CodeQLTool(config, REPO_ROOT, bin_path=str(make_fake_codeql(tmp_path)))
        with pytest.raises(FileNotFoundError, match="database"):
            tool.run(entry, tmp_path / "no-db", tmp_path / "out")

    def test_tool_failure_reported_via_returncode(self, tmp_path, config, entry, db):
        failing = tmp_path / "codeql-failing"
        failing.write_text("#!/bin/sh\nexit 2\n", encoding="utf-8")
        failing.chmod(0o755)
        tool = CodeQLTool(config, REPO_ROOT, bin_path=str(failing))
        result = tool.run(entry, db, tmp_path / "out")
        assert result.returncode == 2
        assert result.raw_output is None


class TestStandardize:
    def test_sarif_roundtrip(self, tmp_path, config, entry, db):
        tool = CodeQLTool(config, REPO_ROOT, bin_path=str(make_fake_codeql(tmp_path)))
        result = tool.run(entry, db, tmp_path / "out")

        out_csv = tool.standardize(result, tmp_path / "findings.csv")
        assert out_csv.is_file()

        from vep.evaluation.findings import load_findings_csv
        findings = load_findings_csv(out_csv, tool="codeql", cwe="CWE-999")
        assert len(findings) == 1
        assert findings[0].testcase == "BenchmarkTest00012"
        assert findings[0].rule_id == "java/ldap-injection"
        assert findings[0].line == 68

    def test_missing_raw_output_raises(self, tmp_path, config):
        tool = CodeQLTool(config, REPO_ROOT)
        from types import SimpleNamespace
        run = SimpleNamespace(
            tool="codeql", cwe="CWE-999", raw_output=None, returncode=1, log_file=None,
        )
        with pytest.raises(RuntimeError, match="No raw output"):
            tool.standardize(run, tmp_path / "x.csv")
