"""Unit tests for vep.core.normalization (Phase 4 / M4.1)."""

import pytest

from vep.core.normalization import (
    normalize_cwe_id,
    normalize_testcase_id,
    normalize_truth_value,
    safe_int,
    short_cwe_id,
)


class TestNormalizeCweId:
    @pytest.mark.parametrize(
        "raw,expected",
        [
            ("CWE-022", "CWE-022"),
            ("022", "CWE-022"),
            ("22", "CWE-022"),
            ("cwe022", "CWE-022"),
            ("cwe-022", "CWE-022"),
            ("CWE_022", "CWE-022"),
            ("cwe 89", "CWE-089"),
            ("328S", "CWE-328S"),           # suffix variant is preserved here
            ("CWE-328s", "CWE-328S"),
        ],
    )
    def test_documented_formats(self, raw, expected):
        assert normalize_cwe_id(raw) == expected

    def test_codeql_328_dir_special_case(self):
        # CodeQL rule directory "CWE-328_328S" normalizes to CWE-328
        # (manifest convention); see normalize_cwe_id docstring.
        assert normalize_cwe_id("CWE-328_328S") == "CWE-328"

    def test_empty_returns_empty(self):
        assert normalize_cwe_id("") == ""

    def test_no_match_returns_original(self):
        assert normalize_cwe_id("hello") == "hello"


class TestShortCweId:
    @pytest.mark.parametrize(
        "raw,expected",
        [
            ("CWE-022", "022"),
            ("cwe022", "022"),
            ("22", "022"),
            ("CWE-328S", "328"),
            ("CWE-328_328S", "328"),
        ],
    )
    def test_short_id(self, raw, expected):
        assert short_cwe_id(raw) == expected

    def test_no_match_returns_empty(self):
        assert short_cwe_id("java") == ""


class TestNormalizeTestcaseId:
    def test_benchmark_name(self):
        assert normalize_testcase_id("BenchmarkTest00001") == "BenchmarkTest00001"

    def test_from_file_path(self):
        path = "org/owasp/benchmark/testcode/BenchmarkTest00123.java"
        assert normalize_testcase_id(path) == "BenchmarkTest00123"

    def test_from_absolute_path(self):
        assert normalize_testcase_id("/tmp/x/BenchmarkTest00456.java") == "BenchmarkTest00456"

    def test_no_match_returns_stripped_original(self):
        assert normalize_testcase_id("  SomeOtherCase  ") == "SomeOtherCase"

    def test_empty_returns_empty(self):
        assert normalize_testcase_id("") == ""


class TestSafeInt:
    @pytest.mark.parametrize(
        "raw,expected",
        [("88", 88), (" 7 ", 7), (None, None), ("abc", None), ("", None), (12, 12)],
    )
    def test_values(self, raw, expected):
        assert safe_int(raw) == expected


class TestNormalizeTruthValue:
    @pytest.mark.parametrize(
        "raw,expected",
        [
            ("true", True), ("TRUE", True), ("1", True), ("vulnerable", True),
            ("yes", True), ("real", True), ("tp", True),
            ("false", False), ("0", False), ("safe", False), ("no", False),
            ("not vulnerable", False), ("fp", False),
        ],
    )
    def test_known_values(self, raw, expected):
        assert normalize_truth_value(raw) is expected

    @pytest.mark.parametrize("raw", ["", "maybe", "unknown", None])
    def test_ambiguous_returns_none(self, raw):
        assert normalize_truth_value(raw) is None
