#!/usr/bin/env python3
"""VEP SARIF Evaluation CLI - Phase 2C Entry Point.

Evaluate CodeQL SARIF results against OWASP Benchmark ground truth.
Converts SARIF to normalized CSV, then evaluates using v2 evaluator.

Usage:
    python scripts/evaluation/eval_sarif_findings.py \\
        --sarif experiments/cwe-079/results/codeql/cwe079.sarif \\
        --ground-truth expectedresults-1.2.csv \\
        --tool codeql \\
        --cwe CWE-079 \\
        --out experiments/cwe-079/eval/codeql_eval_v2/metrics.json

Phase 2C: SARIF Integration
Does NOT replace existing CodeQL evaluation scripts.
"""

import argparse
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from vep.evaluation.sarif import load_sarif_findings, write_findings_csv
from vep.evaluation.ground_truth import load_expected_cases
from vep.evaluation.evaluator import evaluate_findings_with_details
from vep.evaluation.metrics import write_metrics_json, write_evaluation_details
from vep.core.normalization import normalize_cwe_id


def build_parser() -> argparse.ArgumentParser:
    """Build argument parser."""
    parser = argparse.ArgumentParser(
        description="Evaluate CodeQL SARIF results against OWASP Benchmark ground truth."
    )
    parser.add_argument(
        "--sarif",
        required=True,
        help="Path to SARIF file"
    )
    parser.add_argument(
        "--ground-truth",
        required=True,
        help="Path to ground truth CSV (e.g., expectedresults-1.2.csv)"
    )
    parser.add_argument(
        "--tool",
        default="codeql",
        help="Tool name (default: codeql)"
    )
    parser.add_argument(
        "--cwe",
        required=True,
        help="Target CWE (e.g., CWE-079, 079, cwe-079)"
    )
    parser.add_argument(
        "--out",
        required=True,
        help="Output metrics.json path"
    )
    parser.add_argument(
        "--fp-mode",
        choices=["all_non_gt", "in_scope"],
        default="all_non_gt",
        help="FP calculation mode (default: all_non_gt)"
    )
    parser.add_argument(
        "--csv-out",
        help="Path to write normalized findings CSV (default: same dir as --out)"
    )
    parser.add_argument(
        "--details-dir",
        help="Directory for detail CSVs (default: same as --out parent dir)"
    )
    parser.add_argument(
        "--no-details",
        action="store_true",
        help="Do not output detail CSVs"
    )
    parser.add_argument(
        "--manifest",
        help="Path to cwe_manifest.yml (optional, for validation)"
    )
    parser.add_argument(
        "--no-tn",
        action="store_true",
        help="Do not calculate true negatives"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Verbose output"
    )
    return parser


def validate_cwe_in_manifest(cwe: str, manifest_path: Path) -> bool:
    """Validate CWE exists in manifest."""
    if not manifest_path or not manifest_path.exists():
        return True

    try:
        import yaml
        with manifest_path.open("r") as f:
            manifest = yaml.safe_load(f)
        cwe_ids = [normalize_cwe_id(c["id"]) for c in manifest.get("cwes", [])]
        return cwe in cwe_ids
    except Exception:
        return True


def main() -> int:
    """Main entry point."""
    parser = build_parser()
    args = parser.parse_args()

    # Normalize paths
    sarif_path = Path(args.sarif).resolve()
    ground_truth_path = Path(args.ground_truth).resolve()
    out_path = Path(args.out).resolve()
    manifest_path = Path(args.manifest).resolve() if args.manifest else None

    # Determine CSV output path
    if args.csv_out:
        csv_out_path = Path(args.csv_out).resolve()
    else:
        csv_out_path = out_path.parent / "findings.csv"

    # Determine details directory
    if args.details_dir:
        details_dir = Path(args.details_dir).resolve()
    else:
        details_dir = out_path.parent

    # Normalize CWE
    cwe_normalized = normalize_cwe_id(args.cwe)

    if args.verbose:
        print(f"SARIF: {sarif_path}")
        print(f"Ground truth: {ground_truth_path}")
        print(f"Tool: {args.tool}")
        print(f"CWE: {cwe_normalized}")
        print(f"FP mode: {args.fp_mode}")
        print(f"Output: {out_path}")
        print(f"CSV output: {csv_out_path}")
        if not args.no_details:
            print(f"Details dir: {details_dir}")

    # Validate CWE in manifest
    if manifest_path:
        if not validate_cwe_in_manifest(cwe_normalized, manifest_path):
            print(f"⚠️  Warning: CWE {cwe_normalized} not found in manifest")

    # Convert SARIF to findings
    try:
        if args.verbose:
            print("\n[1/5] Loading SARIF...")
        findings = load_sarif_findings(sarif_path, tool=args.tool, cwe=cwe_normalized)
        if args.verbose:
            print(f"  Loaded {len(findings)} findings from SARIF")

        if args.verbose:
            print(f"\n[2/5] Writing normalized CSV to {csv_out_path}...")
        write_findings_csv(findings, csv_out_path)

        if args.verbose:
            print("\n[3/5] Loading ground truth...")
        expected_cases = load_expected_cases(ground_truth_path, cwe=cwe_normalized)
        if args.verbose:
            vulnerable_count = sum(1 for e in expected_cases if e.is_vulnerable)
            print(f"  Loaded {len(expected_cases)} expected cases ({vulnerable_count} vulnerable)")

        if args.verbose:
            print("\n[4/5] Evaluating...")
        result, details = evaluate_findings_with_details(
            findings=findings,
            expected_cases=expected_cases,
            tool=args.tool,
            cwe=cwe_normalized,
            include_tn=not args.no_tn,
            fp_mode=args.fp_mode
        )

        if args.verbose:
            print("\n[5/5] Writing outputs...")
        write_metrics_json(result, out_path)

        if not args.no_details:
            write_evaluation_details(details, details_dir)
            if args.verbose:
                print(f"  Written detail CSVs to: {details_dir}")

    except FileNotFoundError as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1

    # Print summary
    print("\n" + "=" * 60)
    print("VEP SARIF Evaluation Result (v2)")
    print("=" * 60)
    print(f"Tool: {result.tool}")
    print(f"CWE: {result.cwe}")
    print(f"FP mode: {result.fp_mode}")
    print(f"Raw findings: {result.total_findings}")
    print(f"Dedup findings: {result.dedup_findings}")
    print(f"Ground truth vulnerable: {result.total_expected_vulnerable}")
    print("")
    print(f"TP: {result.tp}")
    print(f"FP: {result.fp}")
    print(f"FN: {result.fn}")
    if result.tn is not None:
        print(f"TN: {result.tn}")
    print("")
    print(f"Precision: {result.precision:.4f}")
    print(f"Recall: {result.recall:.4f}")
    print(f"F1: {result.f1:.4f}")
    print("=" * 60)
    print(f"✅ CSV written to: {csv_out_path}")
    print(f"✅ Metrics written to: {out_path}")
    if not args.no_details:
        print(f"✅ Details written to: {details_dir}/")
    print("")

    return 0


if __name__ == "__main__":
    sys.exit(main())
