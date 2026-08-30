"""Unit tests for vep.evaluation.metrics (Phase 4 / M4.2)."""

import csv
import json

from vep.core.models import EvalResult
from vep.evaluation.metrics import (
    eval_result_to_dict,
    write_evaluation_details,
    write_metrics_json,
)


def make_result(**overrides):
    defaults = dict(
        tool="codefuse",
        cwe="CWE-999",
        tp=2, fp=2, fn=1, tn=2,
        precision=0.5, recall=0.6667, f1=0.5714,
        fnr=0.3333, fpr=0.5, fdr=0.5,
        total_findings=5, dedup_findings=4,
        total_expected_vulnerable=3, total_expected_cases=5,
        in_scope_findings=2, outside_scope_findings=2,
        outside_scope_ratio=0.5,
        fp_in_scope=0, fp_all_non_gt=2,
        fp_mode="all_non_gt",
    )
    defaults.update(overrides)
    return EvalResult(**defaults)


class TestEvalResultToDict:
    def test_core_and_extended_fields(self):
        metrics = eval_result_to_dict(make_result())
        assert metrics["schema_version"] == "vep.eval.v2"
        assert metrics["tp"] == 2 and metrics["fp"] == 2 and metrics["fn"] == 1
        assert metrics["tn"] == 2
        assert metrics["raw_findings"] == 5
        assert metrics["dedup_findings"] == 4
        assert metrics["ground_truth_total"] == 3
        assert metrics["cwe_scope_total"] == 5
        assert metrics["fp_mode"] == "all_non_gt"
        assert metrics["fp_in_scope"] == 0
        assert metrics["fp_all_non_gt"] == 2

    def test_optional_fields_omitted(self):
        metrics = eval_result_to_dict(make_result(tn=None, total_expected_cases=None))
        assert "tn" not in metrics
        assert "cwe_scope_total" not in metrics
        assert "total_expected_cases" not in metrics


class TestWriters:
    def test_write_metrics_json_roundtrip(self, tmp_path):
        out = tmp_path / "nested" / "metrics.json"
        write_metrics_json(make_result(), out)
        data = json.loads(out.read_text(encoding="utf-8"))
        assert data["tp"] == 2
        assert data["schema_version"] == "vep.eval.v2"

    def test_write_evaluation_details_writes_four_csvs(self, tmp_path):
        from vep.core.models import EvaluationDetails

        details = EvaluationDetails(
            tp_rows=[{"testcase": "BenchmarkTest00001", "testcaseId": "00001",
                      "sinkFile": "a.java", "line": 1, "ruleId": "CWE-999",
                      "findingCount": 1}],
            fp_rows=[], fn_rows=[], outside_scope_rows=[],
        )
        write_evaluation_details(details, tmp_path)
        for name in ("tp.csv", "fp.csv", "fn.csv", "outside_scope.csv"):
            assert (tmp_path / name).is_file(), name

        with (tmp_path / "tp.csv").open(newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        assert len(rows) == 1
        assert rows[0]["testcase"] == "BenchmarkTest00001"

    def test_write_detail_csv_writes_header_even_when_empty(self, tmp_path):
        from vep.evaluation.metrics import write_detail_csv

        path = tmp_path / "empty.csv"
        write_detail_csv([], path, ["a", "b"])
        assert path.read_text(encoding="utf-8").strip() == "a,b"
