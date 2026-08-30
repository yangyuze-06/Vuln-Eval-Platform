"""Unit tests for vep.core.manifest (Phase 4 / M4.1)."""

import pytest

from vep.core.manifest import load_manifest

PROJECT_ROOT_MARKER = "cwe_manifest.yml"


@pytest.fixture(scope="module")
def manifest():
    return load_manifest()


class TestLoadManifest:
    def test_loads_all_eleven_cwes(self, manifest):
        assert len(manifest.cwes) == 11

    def test_ground_truth(self, manifest):
        assert manifest.ground_truth_file.name == "expectedresults-1.2.csv"
        assert manifest.ground_truth_file.is_file()

    def test_databases(self, manifest):
        assert manifest.codefuse_db is not None
        assert manifest.codeql_db is not None

    def test_local_lib(self, manifest):
        assert manifest.local_lib is not None
        assert manifest.local_lib.is_dir()

    def test_entry_fields(self, manifest):
        entry = manifest.find("022")
        assert entry.name == "CWE-022"
        assert entry.slug == "cwe-022"
        assert entry.slug_compact == "cwe022"
        assert entry.codefuse_rule_file.name == "checker022.gdl"
        assert entry.codefuse_rule_file.is_file()
        assert entry.experiments_directory.name == "cwe-022"

    def test_cwe328_codeql_directory_special_case(self, manifest):
        # CodeQL uses the CWE-328_328S directory (includes the 328S variant);
        # the manifest must keep carrying this special case.
        entry = manifest.find("328")
        assert entry.codeql_rule_directory.name == "CWE-328_328S"
        assert entry.codefuse_rule_file.name == "checker328.gdl"


class TestResolve:
    @pytest.mark.parametrize(
        "token,expected_name",
        [("022", "CWE-022"), ("CWE-022", "CWE-022"), ("cwe-022", "CWE-022"),
         ("cwe022", "CWE-022")],
    )
    def test_token_forms(self, manifest, token, expected_name):
        assert manifest.resolve([token])[0].name == expected_name

    def test_all_returns_every_entry(self, manifest):
        assert len(manifest.resolve(["all"])) == 11

    def test_mixed_tokens_keep_order(self, manifest):
        resolved = manifest.resolve(["cwe-089", "022"])
        assert [entry.name for entry in resolved] == ["CWE-089", "CWE-022"]

    def test_unknown_token_raises(self, manifest):
        with pytest.raises(ValueError, match="999"):
            manifest.resolve(["999"])


class TestMatches:
    def test_positive_forms(self):
        entry = load_manifest().find("022")
        assert entry.matches("022")
        assert entry.matches("CWE-022")
        assert entry.matches("cwe-022")
        assert entry.matches("cwe022")

    def test_negative(self):
        entry = load_manifest().find("022")
        assert not entry.matches("078")
        assert not entry.matches("java")
