"""Report orchestration and user-facing tool label tests."""

from pathlib import Path
from types import SimpleNamespace

from vep.pipeline import (
    PipelineOptions,
    ToolPipelineResult,
    _generate_reports,
    _run_report,
    run_pipeline,
)
from vep.reporting.report_generator import ReportData, ToolMetrics, tool_display_name
from vep.reporting.text_report import generate_english_report, generate_chinese_report


def _options(tmp_path):
    return PipelineOptions(
        tool="both",
        stages=["aggregate", "report"],
        report_out_dir=tmp_path / "reports",
    )


def test_single_tool_report_keeps_root_output(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(
        "vep.pipeline._run_report",
        lambda paths, out_dir, root: calls.append((paths, out_dir)) or None,
    )
    metric = tmp_path / "codefuse.json"
    results = {"codefuse": ToolPipelineResult("codefuse", aggregate_path=metric)}

    failures = _generate_reports(
        ["codefuse"], results, _options(tmp_path), tmp_path
    )

    assert failures == []
    assert calls == [([metric], tmp_path / "reports")]


def test_both_tools_generate_standalone_and_combined_reports(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(
        "vep.pipeline._run_report",
        lambda paths, out_dir, root: calls.append((paths, out_dir)) or None,
    )
    codefuse = tmp_path / "codefuse.json"
    codeql = tmp_path / "codeql.json"
    results = {
        "codefuse": ToolPipelineResult("codefuse", aggregate_path=codefuse),
        "codeql": ToolPipelineResult("codeql", aggregate_path=codeql),
    }

    failures = _generate_reports(
        ["codefuse", "codeql"], results, _options(tmp_path), tmp_path
    )

    assert failures == []
    assert calls == [
        ([codefuse], tmp_path / "reports" / "codefuse"),
        ([codeql], tmp_path / "reports" / "codeql"),
        ([codefuse, codeql], tmp_path / "reports"),
    ]


def test_missing_tool_skips_combined_report(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(
        "vep.pipeline._run_report",
        lambda paths, out_dir, root: calls.append((paths, out_dir)) or None,
    )
    codefuse = tmp_path / "codefuse.json"
    results = {
        "codefuse": ToolPipelineResult("codefuse", aggregate_path=codefuse),
        "codeql": ToolPipelineResult("codeql"),
    }

    failures = _generate_reports(
        ["codefuse", "codeql"], results, _options(tmp_path), tmp_path
    )

    assert calls == [([codefuse], tmp_path / "reports" / "codefuse")]
    assert failures == [
        "combined report not generated; missing aggregate output for: codeql"
    ]


def test_report_process_failure_is_returned(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "vep.pipeline.subprocess.run",
        lambda *args, **kwargs: SimpleNamespace(returncode=7),
    )

    failure = _run_report([tmp_path / "metrics.json"], tmp_path / "out", tmp_path)

    assert "returncode=7" in failure
    assert str(tmp_path / "out") in failure


def test_report_failure_makes_pipeline_fail(monkeypatch, tmp_path):
    from tests.python.test_pipeline_golden import build_workspace

    workspace = build_workspace(tmp_path)
    monkeypatch.setattr(
        "vep.pipeline._run_report",
        lambda paths, out_dir, root: "synthetic report failure",
    )
    options = PipelineOptions(
        tool="codefuse",
        cwe_tokens=["all"],
        stages=["evaluate", "aggregate", "report"],
        manifest_file=workspace / "manifest.yml",
        aggregate_out_root=tmp_path / "aggregates",
        report_out_dir=tmp_path / "reports",
    )

    assert run_pipeline(options, tmp_path) == 1


def test_display_names_do_not_change_machine_ids():
    metrics = ToolMetrics(tp=1, precision=1.0, recall=1.0, f1=1.0)
    report = ReportData(
        schema="test",
        tools=["codefuse", "codeql"],
        overall={"codefuse": metrics, "codeql": metrics},
    )

    english = generate_english_report(report)
    chinese = generate_chinese_report(report)

    assert report.tools == ["codefuse", "codeql"]
    assert tool_display_name("codefuse") == "CodeFuse-Query"
    assert tool_display_name("codeql") == "CodeQL"
    assert "Tools evaluated:** CodeFuse-Query, CodeQL" in english
    assert "评估工具：** CodeFuse-Query, CodeQL" in chinese
