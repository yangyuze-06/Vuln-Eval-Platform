#!/usr/bin/env python3
"""VEP Unified Pipeline CLI - Phase 3 / M3.3 Entry Point.

One command for: tool execution -> normalization -> v2 evaluation ->
multi-CWE aggregation -> v2 reporting. Manifest-driven.

Usage:
    # Full CodeFuse regression (run + evaluate + aggregate)
    python3 scripts/evaluation/run_pipeline.py --tool codefuse --cwe all \
        --db dataset/codefuse-db-mac-fixed

    # Evaluate existing findings only (no analysis tools needed)
    python3 scripts/evaluation/run_pipeline.py --tool codefuse --cwe all \
        --stages evaluate,aggregate

    # Both tools, with reports
    python3 scripts/evaluation/run_pipeline.py --tool both --cwe all \
        --stages run,evaluate,aggregate,report

Phase 3 / M3.3: the run_eval.sh / eval_checker.sh entries are switched over
to this pipeline in M3.4 after the parity gate.
"""

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from vep.pipeline import STAGES, PipelineOptions, run_pipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="VEP unified experiment pipeline (Phase 3 / M3.3)."
    )
    parser.add_argument(
        "--tool",
        required=True,
        choices=["codefuse", "codeql", "both"],
        help="Which analysis tool(s) to drive.",
    )
    parser.add_argument(
        "--cwe",
        nargs="+",
        required=True,
        help='CWE tokens (id / CWE-XXX / cwe-xxx / cweXXX), or the single token "all".',
    )
    parser.add_argument(
        "--stages",
        default="run,evaluate,aggregate",
        help=f"Comma-separated stages subset of {','.join(STAGES)} (default: run,evaluate,aggregate).",
    )
    parser.add_argument(
        "--db",
        help="Database path override for the selected tool (not allowed with --tool both).",
    )
    parser.add_argument(
        "--db-codefuse",
        help="Database path override for CodeFuse (takes precedence over --db for codefuse).",
    )
    parser.add_argument(
        "--db-codeql",
        help="Database path override for CodeQL (takes precedence over --db for codeql).",
    )
    parser.add_argument(
        "--fp-mode",
        choices=["all_non_gt", "in_scope"],
        default="all_non_gt",
        help="FP calculation mode (default: all_non_gt).",
    )
    parser.add_argument(
        "--eval-dir-name",
        help="Eval output directory name override (single-tool runs only; "
             "defaults: codefuse_eval_v2 / codeql_eval_v2).",
    )
    parser.add_argument(
        "--out-root",
        default="reports/data",
        help="Directory for the aggregate JSON (default: reports/data).",
    )
    parser.add_argument(
        "--aggregate-name",
        help="Aggregate JSON filename override (default: metrics_v2_<tool>_all|subset.json).",
    )
    parser.add_argument(
        "--report-out-dir",
        default="reports",
        help="Directory for the v2 report (default: reports).",
    )
    parser.add_argument(
        "--manifest",
        default="configs/cwe_manifest.yml",
        help="Path to cwe_manifest.yml (default: configs/cwe_manifest.yml).",
    )
    parser.add_argument(
        "--tools-config",
        default="configs/tools.yml",
        help="Path to tools.yml (default: configs/tools.yml).",
    )
    parser.add_argument(
        "--keep-going",
        action="store_true",
        help="Continue with remaining CWEs when one fails.",
    )
    parser.add_argument(
        "--no-skip-existing",
        action="store_true",
        help="Re-run/evaluate even when metrics.json already exists.",
    )
    parser.add_argument(
        "--run-timeout",
        type=int,
        default=3600,
        help="Per-CWE tool run timeout in seconds (default: 3600).",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()

    stages = [stage.strip() for stage in args.stages.split(",") if stage.strip()]
    invalid = [stage for stage in stages if stage not in STAGES]
    if invalid:
        print(f"❌ Unknown stages: {', '.join(invalid)} (valid: {', '.join(STAGES)})")
        return 2
    if not stages:
        print("❌ No stages selected.")
        return 2
    if args.db and args.tool == "both":
        print("❌ --db 不能与 --tool both 同用；请使用 --db-codefuse / --db-codeql。")
        return 2
    if args.eval_dir_name and args.tool == "both":
        print("❌ --eval-dir-name 不能与 --tool both 同用。")
        return 2

    db_overrides = {"codefuse": None, "codeql": None}
    if args.db:
        db_overrides[args.tool] = Path(args.db)
    if args.db_codefuse:
        db_overrides["codefuse"] = Path(args.db_codefuse)
    if args.db_codeql:
        db_overrides["codeql"] = Path(args.db_codeql)

    eval_dir_names = {}
    if args.eval_dir_name:
        eval_dir_names[args.tool] = args.eval_dir_name

    options = PipelineOptions(
        tool=args.tool,
        cwe_tokens=args.cwe,
        stages=stages,
        manifest_file=Path(args.manifest),
        tools_config_file=Path(args.tools_config),
        db_overrides=db_overrides,
        fp_mode=args.fp_mode,
        eval_dir_names=eval_dir_names,
        aggregate_out_root=Path(args.out_root),
        aggregate_name=args.aggregate_name,
        report_out_dir=Path(args.report_out_dir),
        keep_going=args.keep_going,
        skip_existing=not args.no_skip_existing,
        run_timeout_seconds=args.run_timeout,
    )
    try:
        return run_pipeline(options, PROJECT_ROOT)
    except ValueError as exc:
        print(f"❌ {exc}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
