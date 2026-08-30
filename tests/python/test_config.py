"""Unit tests for vep.tools.config discovery (Phase 4 / M4.3)."""

import os
import stat
from pathlib import Path

import pytest
import yaml

from vep.tools.config import (
    discover_codefuse,
    discover_codeql,
    load_tools_config,
)

MISSING_CONFIG = Path("/nonexistent/tools.yml")


def make_fake_sparrow_home(tmp_path, complete=True):
    """Create a fake sparrow-cli installation directory."""
    home = tmp_path / "sparrow-cli"
    godel = home / "godel-script" / "usr" / "bin" / "godel"
    godel.parent.mkdir(parents=True, exist_ok=True)
    if complete:
        godel.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        godel.chmod(godel.stat().st_mode | stat.S_IXUSR)
        (home / "lib" / "coref").mkdir(parents=True, exist_ok=True)
    return home


@pytest.fixture
def config():
    cfg = load_tools_config(config_file=MISSING_CONFIG)
    cfg.env_checks.codefuse_java_env = False
    return cfg


class TestLoadToolsConfig:
    def test_missing_file_returns_defaults(self, tmp_path):
        cfg = load_tools_config(config_file=tmp_path / "nope.yml")
        assert cfg.codefuse.home is None
        assert cfg.codeql.bin == "codeql"
        assert str(cfg.databases.codeql) == "dataset/codeql-db/benchmark-java"
        assert cfg.env_checks.codefuse_java_env is True
        assert cfg.source_file is None

    def test_yaml_overrides(self, tmp_path):
        cfg_file = tmp_path / "tools.yml"
        cfg_file.write_text(yaml.safe_dump({
            "codefuse": {"home": "/opt/cf", "godel_bin": "/opt/cf/godel"},
            "codeql": {"bin": "/usr/local/bin/codeql"},
            "databases": {"codefuse": "dataset/cf", "codeql": "dataset/ql"},
            "env_checks": {"codefuse_java_env": False},
        }), encoding="utf-8")
        cfg = load_tools_config(config_file=cfg_file)
        assert cfg.codefuse.home == "/opt/cf"
        assert cfg.codefuse.godel_bin == "/opt/cf/godel"
        assert cfg.codeql.bin == "/usr/local/bin/codeql"
        assert str(cfg.databases.codefuse) == "dataset/cf"
        assert cfg.env_checks.codefuse_java_env is False
        assert cfg.source_file == cfg_file

    def test_repo_config_shape(self):
        # The committed tools.yml must keep the corrected CodeQL DB path.
        cfg = load_tools_config()
        assert cfg.source_file is not None
        assert str(cfg.databases.codeql).endswith("codeql-db/benchmark-java")
        assert cfg.env_checks.codefuse_java_env is True


class TestDiscoverCodefusePrecedence:
    def test_explicit_override_beats_everything(self, tmp_path, config, monkeypatch):
        fake = make_fake_sparrow_home(tmp_path)
        monkeypatch.setenv("CODEFUSE_HOME", "/nonexistent/env")
        paths, _ = discover_codefuse(config, tmp_path, home_override=str(fake))
        assert paths.home == fake.resolve()

    def test_env_used_when_no_override(self, tmp_path, config, monkeypatch):
        fake = make_fake_sparrow_home(tmp_path)
        monkeypatch.setenv("CODEFUSE_HOME", str(fake))
        paths, _ = discover_codefuse(config, tmp_path)
        assert paths.home == fake.resolve()

    def test_config_used_when_no_env(self, tmp_path, monkeypatch):
        fake = make_fake_sparrow_home(tmp_path)
        monkeypatch.delenv("CODEFUSE_HOME", raising=False)
        cfg = load_tools_config(config_file=MISSING_CONFIG)
        cfg.codefuse.home = str(fake)
        paths, _ = discover_codefuse(cfg, tmp_path)
        assert paths.home == fake.resolve()

    def test_sparrow_in_path(self, tmp_path, config, monkeypatch):
        fake = make_fake_sparrow_home(tmp_path)
        sparrow = fake / "sparrow"
        sparrow.write_text("#!/bin/sh\n", encoding="utf-8")
        monkeypatch.delenv("CODEFUSE_HOME", raising=False)
        monkeypatch.setattr("vep.tools.config.shutil.which", lambda name: str(sparrow))
        paths, _ = discover_codefuse(config, tmp_path)
        # eval_checker.sh semantics: home = dirname(realpath(sparrow))
        assert paths.home == fake.resolve()

    def test_builtin_fallback_candidates(self, tmp_path, config, monkeypatch):
        base = tmp_path / "Workspace/Tools/static-analysis-tools/codefuse"
        fake = make_fake_sparrow_home(base)
        monkeypatch.delenv("CODEFUSE_HOME", raising=False)
        monkeypatch.setattr("vep.tools.config.shutil.which", lambda name: None)
        monkeypatch.setenv("HOME", str(tmp_path))
        paths, notes = discover_codefuse(config, tmp_path)
        assert paths.home == fake.resolve()
        assert any("⚠️" in note for note in notes)

    def test_no_home_found(self, tmp_path, config, monkeypatch):
        monkeypatch.delenv("CODEFUSE_HOME", raising=False)
        monkeypatch.setattr("vep.tools.config.shutil.which", lambda name: None)
        monkeypatch.setenv("HOME", str(tmp_path / "empty-home"))
        paths, _ = discover_codefuse(config, tmp_path)
        assert paths is None

    def test_godel_bin_env_override(self, tmp_path, config, monkeypatch):
        fake = make_fake_sparrow_home(tmp_path)
        custom_godel = tmp_path / "custom-godel"
        custom_godel.write_text("#!/bin/sh\n", encoding="utf-8")
        monkeypatch.setenv("GODEL_BIN", str(custom_godel))
        paths, _ = discover_codefuse(config, tmp_path, home_override=str(fake))
        assert paths.godel_bin == custom_godel.resolve()

    def test_godel_bin_defaults_to_home_layout(self, tmp_path, config, monkeypatch):
        fake = make_fake_sparrow_home(tmp_path)
        monkeypatch.delenv("GODEL_BIN", raising=False)
        paths, _ = discover_codefuse(config, tmp_path, home_override=str(fake))
        assert paths.godel_bin == fake / "godel-script" / "usr" / "bin" / "godel"

    def test_local_lib_points_to_repo(self, tmp_path, config, monkeypatch):
        fake = make_fake_sparrow_home(tmp_path)
        monkeypatch.delenv("GODEL_BIN", raising=False)
        repo_root = Path(__file__).resolve().parents[2]
        paths, _ = discover_codefuse(config, repo_root, home_override=str(fake))
        assert paths.local_lib.name == "lib"
        assert paths.local_lib.parent.name == "codefuse-query"
        assert paths.local_lib.parent.parent.name == "rules"


class TestDiscoverCodeql:
    def test_resolved_from_path(self, config, monkeypatch):
        monkeypatch.setattr(
            "vep.tools.config.shutil.which",
            lambda name: "/usr/local/bin/codeql" if name == "codeql" else None,
        )
        path, _ = discover_codeql(config, os.getcwd())
        assert str(path) == "/usr/local/bin/codeql"

    def test_absolute_path_passes_through(self, tmp_path, config):
        fake = tmp_path / "codeql"
        fake.write_text("#!/bin/sh\n", encoding="utf-8")
        path, _ = discover_codeql(config, tmp_path, bin_override=str(fake))
        assert path == fake.resolve()

    def test_not_found_returns_none(self, config):
        path, _ = discover_codeql(config, os.getcwd(), bin_override="definitely-not-codeql-xyz")
        assert path is None
