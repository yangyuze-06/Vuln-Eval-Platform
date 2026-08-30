"""Unit tests for vep.evaluation.ground_truth (Phase 4 / M4.2)."""

from pathlib import Path

import pytest

from vep.evaluation.ground_truth import load_expected_cases

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def write_csv(tmp_path, content):
    path = tmp_path / "gt.csv"
    path.write_text(content, encoding="utf-8")
    return path


class TestLoadExpectedCases:
    def test_cwe_filter_and_polarity(self, tmp_path):
        gt = write_csv(tmp_path,
            "# comment line\n"
            "BenchmarkTest00001,cmdi,true,CWE-078\n"
            "BenchmarkTest00002,cmdi,false,CWE-078\n"
            "BenchmarkTest00003,xss,true,CWE-079\n"
        )
        cases = load_expected_cases(gt, cwe="CWE-078")
        assert len(cases) == 2
        assert cases[0].is_vulnerable is True
        assert cases[1].is_vulnerable is False

    def test_token_cwe_filter(self, tmp_path):
        gt = write_csv(tmp_path, "BenchmarkTest00001,x,true,078\n")
        assert len(load_expected_cases(gt, cwe="cwe-078")) == 1

    def test_328s_row_maps_to_cwe328(self, tmp_path):
        # Scope-semantics guard (Phase 3 M3.4 parity audit): ground truth rows
        # carrying the "328S" suffix belong to CWE-328 and must be loaded.
        gt = write_csv(tmp_path,
            "BenchmarkTest00003,hash,true,328S\n"
            "BenchmarkTest00004,hash,false,328S\n"
        )
        cases = load_expected_cases(gt, cwe="CWE-328")
        assert len(cases) == 2
        assert all(case.cwe == "CWE-328" for case in cases)
        assert cases[0].is_vulnerable is True
        assert cases[1].is_vulnerable is False

    def test_ambiguous_truth_skipped(self, tmp_path):
        gt = write_csv(tmp_path,
            "BenchmarkTest00001,x,maybe,CWE-078\n"
            "BenchmarkTest00002,x,true,CWE-078\n"
        )
        cases = load_expected_cases(gt, cwe="CWE-078")
        assert [c.testcase for c in cases] == ["BenchmarkTest00002"]

    def test_raw_fields_preserved(self, tmp_path):
        gt = write_csv(tmp_path, "BenchmarkTest00001,cmdi,true,CWE-078\n")
        case = load_expected_cases(gt, cwe="CWE-078")[0]
        assert case.raw["cwe_raw"] == "CWE-078"
        assert case.raw["vulnerable_raw"] == "true"

    def test_missing_file_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_expected_cases(tmp_path / "nope.csv")

    def test_real_benchmark_328s_row(self):
        # Guard against the real ground truth file losing the 328S row —
        # the row behind the CWE-328 scope-semantics fix (M3.4 parity audit).
        gt = PROJECT_ROOT / "expectedresults-1.2.csv"
        cases = load_expected_cases(gt, cwe="CWE-328")
        by_testcase = {c.testcase: c for c in cases}
        assert by_testcase["BenchmarkTest00003"].is_vulnerable is True
        assert by_testcase["BenchmarkTest00003"].cwe == "CWE-328"
