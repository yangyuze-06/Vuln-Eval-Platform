"""Unit tests for vep.tools.codefuse (Phase 4 / M4.3).

Uses a fake `godel` executable to verify command assembly and the godel 2.1.0
package-root workaround (official lib + repo-local lib merged into one root).
"""

import json
import os
import stat
import subprocess
import textwrap
from pathlib import Path
from types import SimpleNamespace

import pytest

from vep.core.manifest import CweEntry
from vep.tools.codefuse import CodeFuseTool, run_java_env_gate
from vep.tools.config import load_tools_config

# Tools need the real repo root: local_lib and the converter script live there.
REPO_ROOT = Path(__file__).resolve().parents[2]

FAKE_GODEL = textwrap.dedent("""\
    #!/bin/bash
    # fake godel: snapshot the package root and emit deterministic findings JSON
    mkdir -p "$FAKE_GODEL_SNAPSHOT"
    pkg=""; rule=""; out=""; prev=""
    for a in "$@"; do
      case "$prev" in
        -p) pkg="$a";;
        -r) rule="$a";;
        --output-json) out="$a";;
      esac
      prev="$a"
    done
    printf '%s\\n' "$@" > "$FAKE_GODEL_SNAPSHOT/args.txt"
    echo "$rule" > "$FAKE_GODEL_SNAPSHOT/invoked-rule.txt"
    cp -R "$pkg" "$FAKE_GODEL_SNAPSHOT/package-root"
    cat > "$out" <<'JSON'
    [
      {"testcase": "BenchmarkTest00001", "ruleId": "CWE-999",
       "sinkFile": "org/x/BenchmarkTest00001.java", "sinkLine": 10, "reason": "fake finding"},
      {"testcase": "BenchmarkTest00001", "ruleId": "CWE-999",
       "sinkFile": "org/x/BenchmarkTest00001.java", "sinkLine": 11, "reason": "duplicate"},
      {"testcase": "BenchmarkTest00002", "ruleId": "CWE-999",
       "sinkFile": "org/x/BenchmarkTest00002.java", "sinkLine": 20, "reason": "second"}
    ]
    JSON
""")


def make_fake_install(tmp_path, with_godel=True, with_lib=True):
    home = tmp_path / "sparrow-cli"
    official_lib = home / "lib"
    godel = home / "godel-script" / "usr" / "bin" / "godel"
    if with_godel:
        godel.parent.mkdir(parents=True, exist_ok=True)
        # fake godel body: snapshots the package root, emits fixed JSON;
        # harmless for check_environment, required for run() tests
        godel.write_text(FAKE_GODEL, encoding="utf-8")
        godel.chmod(godel.stat().st_mode | stat.S_IXUSR)
    if with_lib:
        official_lib.mkdir(parents=True, exist_ok=True)
        (official_lib / "official-marker.txt").write_text("official", encoding="utf-8")
    return home, godel, official_lib


def make_tool(tmp_path, config, **kwargs):
    home, godel, official_lib = make_fake_install(
        tmp_path,
        with_godel=kwargs.pop("with_godel", True),
        with_lib=kwargs.pop("with_lib", True),
    )
    tool = CodeFuseTool(
        config,
        REPO_ROOT,
        home=str(home),
        godel_bin=str(godel),
        official_lib=str(official_lib),
        **kwargs,
    )
    return tool, home, godel, official_lib


@pytest.fixture
def config():
    cfg = load_tools_config(config_file=Path("/nonexistent/tools.yml"))
    cfg.env_checks.codefuse_java_env = False
    return cfg


@pytest.fixture
def entry(tmp_path):
    rule_file = tmp_path / "checker999.gdl"
    rule_file.write_text("// fake rule\n", encoding="utf-8")
    return CweEntry(
        id="999", name="CWE-999", slug="cwe-999", slug_compact="cwe999",
        codefuse_rule_file=rule_file,
        experiments_directory=tmp_path / "experiments" / "cwe-999",
    )


@pytest.fixture
def db(tmp_path):
    db_dir = tmp_path / "db"
    db_dir.mkdir()
    return db_dir


class TestCheckEnvironment:
    def test_clean_fake_install(self, tmp_path, config):
        tool, *_ = make_tool(tmp_path, config)
        assert tool.check_environment() == []

    def test_missing_godel_reported(self, tmp_path, config):
        tool, *_ = make_tool(tmp_path, config, with_godel=False)
        problems = tool.check_environment()
        assert any("godel" in p and p.startswith("❌") for p in problems)

    def test_missing_official_lib_reported(self, tmp_path, config):
        tool, *_ = make_tool(tmp_path, config, with_lib=False)
        problems = tool.check_environment()
        assert any("lib" in p and p.startswith("❌") for p in problems)

    def test_home_not_found(self, tmp_path, config, monkeypatch):
        monkeypatch.delenv("CODEFUSE_HOME", raising=False)
        monkeypatch.setattr("vep.tools.config.shutil.which", lambda name: None)
        monkeypatch.setenv("HOME", str(tmp_path / "empty"))
        tool = CodeFuseTool(config, tmp_path)
        problems = tool.check_environment()
        assert any("找不到 CodeFuse/Sparrow 安装目录" in p for p in problems)

    def test_java_gate_wiring(self, tmp_path, config, monkeypatch):
        cfg = load_tools_config(config_file=Path("/nonexistent/tools.yml"))
        cfg.env_checks.codefuse_java_env = True
        tool, *_ = make_tool(tmp_path, cfg)
        monkeypatch.setattr(
            "vep.tools.codefuse.run_java_env_gate",
            lambda root: ["❌ JAVA_HOME 检查: fake failure"],
        )
        problems = tool.check_environment()
        assert "❌ JAVA_HOME 检查: fake failure" in problems


class TestRun:
    def test_run_merges_package_root_and_emits_json(
        self, tmp_path, config, entry, db, monkeypatch
    ):
        tool, home, godel, official_lib = make_tool(tmp_path, config)
        snapshot = tmp_path / "snapshot"
        monkeypatch.setenv("FAKE_GODEL_SNAPSHOT", str(snapshot))
        out_dir = tmp_path / "out"

        result = tool.run(entry, db, out_dir)

        assert result.returncode == 0
        assert result.raw_output == out_dir / "checker999.json"
        assert result.raw_output.is_file()
        assert result.log_file is not None and result.log_file.is_file()
        assert result.cwe == "CWE-999"

        # godel 2.1.0 package-root workaround: official AND local libs merged
        package_root = snapshot / "package-root"
        assert (package_root / "official-marker.txt").is_file()
        assert (package_root / "security" / "java" / "TaintTracking.gdl").is_file()
        # "$@" excludes the script itself, so args[0] is the first CLI flag
        args = (snapshot / "args.txt").read_text(encoding="utf-8").splitlines()
        assert args[0] == "-p"
        assert str(entry.codefuse_rule_file) in args
        assert str(db.resolve()) in args
        assert "-Of" in args

    def test_missing_rule_file_raises(self, tmp_path, config, db):
        tool, *_ = make_tool(tmp_path, config)
        broken = CweEntry(id="999", name="CWE-999", slug="cwe-999", slug_compact="cwe999")
        with pytest.raises(ValueError, match="rule_file"):
            tool.run(broken, db, tmp_path / "out")

    def test_missing_db_raises(self, tmp_path, config, entry):
        tool, *_ = make_tool(tmp_path, config)
        with pytest.raises(FileNotFoundError, match="database"):
            tool.run(entry, tmp_path / "no-db", tmp_path / "out")

    def test_tool_failure_reported_via_returncode(
        self, tmp_path, config, entry, db, monkeypatch
    ):
        tool, home, godel, official_lib = make_tool(tmp_path, config)
        failing = tmp_path / "failing-godel"
        failing.write_text("#!/bin/sh\nexit 3\n", encoding="utf-8")
        failing.chmod(failing.stat().st_mode | stat.S_IXUSR)
        tool.godel_bin_override = str(failing)
        monkeypatch.setenv("FAKE_GODEL_SNAPSHOT", str(tmp_path / "unused"))

        result = tool.run(entry, db, tmp_path / "out")
        assert result.returncode == 3
        assert result.raw_output is None


class TestStandardize:
    def test_expected_csv_content(self, tmp_path, config):
        tool, *_ = make_tool(tmp_path, config)
        raw = tmp_path / "checker999.json"
        raw.write_text(
            '[{"testcase":"BenchmarkTest00001","ruleId":"CWE-999",'
            '"sinkFile":"org/x/BenchmarkTest00001.java","sinkLine":10,"reason":"fake finding"},'
            '{"testcase":"BenchmarkTest00001","ruleId":"CWE-999",'
            '"sinkFile":"org/x/BenchmarkTest00001.java","sinkLine":11,"reason":"duplicate"},'
            '{"testcase":"BenchmarkTest00002","ruleId":"CWE-999",'
            '"sinkFile":"org/x/BenchmarkTest00002.java","sinkLine":20,"reason":"second"}]',
            encoding="utf-8",
        )
        run = SimpleNamespace(
            tool="codefuse", cwe="CWE-999", raw_output=raw, returncode=0, log_file=None,
        )
        out_csv = tool.standardize(run, tmp_path / "findings.csv")
        # compare bytes: read_text() would normalize the \r\n line endings
        assert out_csv.read_bytes() == (
            "testcase,ruleId,file,line,reason\r\n"
            "BenchmarkTest00001,CWE-999,org/x/BenchmarkTest00001.java,10,fake finding\r\n"
            "BenchmarkTest00002,CWE-999,org/x/BenchmarkTest00002.java,20,second\r\n"
        ).encode("utf-8")

    def test_missing_raw_output_raises(self, tmp_path, config):
        tool, *_ = make_tool(tmp_path, config)
        run = SimpleNamespace(
            tool="codefuse", cwe="CWE-999", raw_output=None, returncode=1, log_file=None,
        )
        with pytest.raises(RuntimeError, match="No raw output"):
            tool.standardize(run, tmp_path / "x.csv")


class TestRunJavaEnvGate:
    def _gate(self, monkeypatch, returncode, stdout="", stderr=""):
        calls = {}

        def fake_run(cmd, **kwargs):
            calls["cmd"] = cmd
            return SimpleNamespace(returncode=returncode, stdout=stdout, stderr=stderr)

        monkeypatch.setattr(subprocess, "run", fake_run)
        return calls

    def test_pass_returns_empty(self, tmp_path, monkeypatch):
        self._gate(monkeypatch, 0)
        assert run_java_env_gate(REPO_ROOT) == []

    def test_fail_and_warn_mapped(self, tmp_path, monkeypatch):
        payload = {
            "results": [
                {"level": "FAIL",
                 "message": "JAVA_HOME points to Homebrew keg prefix, not real JDK home.",
                 "detail": "Expected: /real/home"},
                {"level": "WARN", "message": "Missing $JAVA_HOME/lib/ct.sym.",
                 "detail": "/x/ct.sym"},
            ],
            "recommendations": ['export JAVA_HOME="/real/home"'],
        }
        self._gate(monkeypatch, 1, stdout=json.dumps(payload))
        problems = run_java_env_gate(REPO_ROOT)
        assert any(p.startswith("❌") and "Homebrew keg prefix" in p for p in problems)
        assert any(p.startswith("⚠️") and "ct.sym" in p for p in problems)
        assert any(p.startswith("ℹ️") and "export JAVA_HOME" in p for p in problems)

    def test_abnormal_exit(self, tmp_path, monkeypatch):
        self._gate(monkeypatch, 5, stderr="boom")
        problems = run_java_env_gate(REPO_ROOT)
        assert any("异常退出" in p and "5" in p for p in problems)

    def test_unparseable_json(self, tmp_path, monkeypatch):
        self._gate(monkeypatch, 1, stdout="not-json")
        problems = run_java_env_gate(REPO_ROOT)
        assert any("无法解析" in p for p in problems)

    def test_missing_script(self, tmp_path):
        problems = run_java_env_gate(tmp_path / "no-scripts-here")
        assert any("缺失" in p for p in problems)
