"""Unit tests for vep.evaluation.evaluator (Phase 4 / M4.2).

Synthetic scenario (CWE-999):
    ground truth : V1 V2 V3 vulnerable; N1 N2 safe
    findings     : V1, V1 (duplicate), V2, O1, O2 (O1/O2 outside scope)
    expected     : tp=2 fn=1 tn=2; fp_in_scope=0 fp_all_non_gt=2
"""

from vep.core.models import ExpectedCase, Finding
from vep.evaluation.evaluator import evaluate_findings_with_details


def make_fixtures():
    findings = [
        Finding(testcase="BenchmarkTest00001", rule_id="CWE-999", file="a.java", line=1),
        Finding(testcase="BenchmarkTest00001", rule_id="CWE-999", file="a.java", line=2),  # dup
        Finding(testcase="BenchmarkTest00002", rule_id="CWE-999", file="b.java", line=3),
        Finding(testcase="BenchmarkTest00010", rule_id="CWE-999", file="o1.java", line=4),
        Finding(testcase="BenchmarkTest00011", rule_id="CWE-999", file="o2.java", line=5),
    ]
    expected = [
        ExpectedCase(testcase="BenchmarkTest00001", cwe="CWE-999", is_vulnerable=True),
        ExpectedCase(testcase="BenchmarkTest00002", cwe="CWE-999", is_vulnerable=True),
        ExpectedCase(testcase="BenchmarkTest00003", cwe="CWE-999", is_vulnerable=True),
        ExpectedCase(testcase="BenchmarkTest00004", cwe="CWE-999", is_vulnerable=False),
        ExpectedCase(testcase="BenchmarkTest00005", cwe="CWE-999", is_vulnerable=False),
    ]
    return findings, expected


class TestMetrics:
    def test_all_non_gt_mode(self):
        result, details = evaluate_findings_with_details(
            *make_fixtures(), tool="codefuse", cwe="CWE-999", fp_mode="all_non_gt"
        )
        assert (result.tp, result.fp, result.fn, result.tn) == (2, 2, 1, 2)
        assert result.fp_in_scope == 0
        assert result.fp_all_non_gt == 2
        assert result.precision == 0.5
        assert result.recall == 0.6667
        assert result.f1 == 0.5714
        assert result.fnr == 0.3333
        assert result.fpr == 0.5
        assert result.fdr == 0.5
        assert result.total_findings == 5          # raw, including duplicate
        assert result.dedup_findings == 4
        assert result.in_scope_findings == 2
        assert result.outside_scope_findings == 2
        assert result.outside_scope_ratio == 0.5
        assert result.total_expected_vulnerable == 3
        assert result.total_expected_cases == 5
        assert result.fp_mode == "all_non_gt"
        assert result.schema_version == "vep.eval.v2"

    def test_in_scope_mode_excludes_outside_scope(self):
        result, _ = evaluate_findings_with_details(
            *make_fixtures(), tool="codefuse", cwe="CWE-999", fp_mode="in_scope"
        )
        assert result.fp == 0                      # outside-scope findings not counted
        assert result.fp_in_scope == 0
        assert result.fp_all_non_gt == 2           # still reported
        assert result.precision == 1.0
        assert result.recall == 0.6667
        assert result.f1 == 0.8

    def test_tn_optional(self):
        findings, expected = make_fixtures()
        result, _ = evaluate_findings_with_details(
            findings, expected, tool="codefuse", cwe="CWE-999", include_tn=False
        )
        assert result.tn is None
        assert result.fpr == 0.0                   # fpr undefined without tn


class TestDetails:
    def test_row_counts_and_sorting(self):
        _, details = evaluate_findings_with_details(
            *make_fixtures(), tool="codefuse", cwe="CWE-999"
        )
        assert [row["testcase"] for row in details.tp_rows] == [
            "BenchmarkTest00001", "BenchmarkTest00002",
        ]
        assert [row["testcase"] for row in details.fn_rows] == ["BenchmarkTest00003"]
        assert details.fp_rows == []
        assert [row["testcase"] for row in details.outside_scope_rows] == [
            "BenchmarkTest00010", "BenchmarkTest00011",
        ]

    def test_tp_row_fields(self):
        _, details = evaluate_findings_with_details(
            *make_fixtures(), tool="codefuse", cwe="CWE-999"
        )
        row = details.tp_rows[0]
        assert row["testcaseId"] == "00001"
        assert row["sinkFile"] == "a.java"
        assert row["line"] == 1
        assert row["ruleId"] == "CWE-999"
        assert row["findingCount"] == 1

    def test_duplicate_finding_kept_first(self):
        _, details = evaluate_findings_with_details(
            *make_fixtures(), tool="codefuse", cwe="CWE-999"
        )
        # first occurrence (line=1) wins over the duplicate (line=2)
        assert details.tp_rows[0]["line"] == 1


class TestEdgeCases:
    def test_no_findings(self):
        expected = [ExpectedCase(testcase="BenchmarkTest00001", cwe="CWE-999", is_vulnerable=True)]
        result, details = evaluate_findings_with_details(
            [], expected, tool="codefuse", cwe="CWE-999"
        )
        assert (result.tp, result.fp, result.fn) == (0, 0, 1)
        assert result.precision == 0.0
        assert result.recall == 0.0
        assert result.f1 == 0.0
        assert len(details.fn_rows) == 1

    def test_empty_ground_truth_all_findings_outside_scope(self):
        findings = [Finding(testcase="BenchmarkTest00001", rule_id="CWE-999", file="a.java")]
        result, details = evaluate_findings_with_details(
            findings, [], tool="codefuse", cwe="CWE-999", fp_mode="all_non_gt"
        )
        assert (result.tp, result.fp, result.fn) == (0, 1, 0)
        assert result.outside_scope_findings == 1
        assert len(details.outside_scope_rows) == 1
