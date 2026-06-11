#!/usr/bin/env python3
"""VEP Unified Evaluation CLI - Phase 2 Entry Point.

Evaluate normalized findings CSV against OWASP Benchmark ground truth.
This is the v2 evaluation path, independent of existing eval_checker.sh.

Usage:
    python scripts/evaluation/eval_findings.py \\
        --findings experiments/cwe-022/results/codefuse-query/cwe022_codefuse.csv \\
        --ground-truth expectedresults-1.2.csv \\
        --tool codefuse \\
        --cwe CWE-022 \\
        --out experiments/cwe-022/eval/codefuse_eval_v2/metrics.json

Phase 2: Unified Evaluation Core
Does NOT replace existing evaluation scripts.
"""

import argparse
import sys
from pathlib import Path

# Add project root to path for vep imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from vep.evaluation.findings import load_findings_csv
from vep.evaluation.ground_truth import load_expected_cases
from vep.evaluation.evaluator import evaluate_findings
from vep.evaluation.metrics import write_metrics_json
from vep.core.normalization import normalize_cwe_id


def build_parser() -> argparse.ArgumentParser:
    """Build argument parser."""
    parser = argparse.ArgumentParser(
        description="Evaluate vulnerability findings against OWASP Benchmark ground truth."
    )
    parser.add_argument(
        "--findings",
        required=True,
        help="Path to normalized findings CSV"
    )
    parser.add_argument(
        "--ground-truth",
        required=True,
        help="Path to ground truth CSV (e.g., expectedresults-1.2.csv)"
    )
    parser.add_argument(
        "--tool",
        required=True,
        help="Tool name (e.g., codefuse, codeql)"
    )
    parser.add_argument(
        "--cwe",
        required=True,
        help="Target CWE (e.g., CWE-022, 022, cwe-022)"
    )
    parser.add_argument(
        "--out",
        required=True,
        help="Output metrics.json path"
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
    """Validate CWE exists in manifest (optional check).

    Args:
        cwe: Normalized CWE ID
        manifest_path: Path to cwe_manifest.yml

    Returns:
        True if CWE found or manifest not provided, False otherwise
    """
    if not manifest_path or not manifest_path.exists():
        return True  # Skip validation if no manifest

    try:
        import yaml
        with manifest_path.open("r") as f:
            manifest = yaml.safe_load(f)

        cwe_ids = [normalize_cwe_id(c["id"]) for c in manifest.get("cwes", [])]
        return cwe in cwe_ids
    except Exception:
        return True  # Skip validation on error


def main() -> int:
    """Main entry point."""
    parser = build_parser()
    args = parser.parse_args()

    # Normalize paths
    findings_path = Path(args.findings).resolve()
    ground_truth_path = Path(args.ground_truth).resolve()
    out_path = Path(args.out).resolve()
    manifest_path = Path(args.manifest).resolve() if args.manifest else None

    # Normalize CWE
    cwe_normalized = normalize_cwe_id(args.cwe)

    if args.verbose:
        print(f"Findings: {findings_path}")
        print(f"Ground truth: {ground_truth_path}")
        print(f"Tool: {args.tool}")
        print(f"CWE: {cwe_normalized}")
        print(f"Output: {out_path}")

    # Validate CWE in manifest (optional)
    if manifest_path:
        if not validate_cwe_in_manifest(cwe_normalized, manifest_path):
            print(f"⚠️  Warning: CWE {cwe_normalized} not found in manifest")

    # Load data
    try:
        if args.verbose:
            print("\n[1/4] Loading findings...")
        findings = load_findings_csv(findings_path, tool=args.tool, cwe=cwe_normalized)
        if args.verbose:
            print(f"  Loaded {len(findings)} findings")

        if args.verbose:
            print("\n[2/4] Loading ground truth...")
        expected_cases = load_expected_cases(ground_truth_path, cwe=cwe_normalized)
        if args.verbose:
            vulnerable_count = sum(1 for e in expected_cases if e.is_vulnerable)
            print(f"  Loaded {len(expected_cases)} expected cases ({vulnerable_count} vulnerable)")

        if args.verbose:
            print("\n[3/4] Evaluating...")
        result = evaluate_findings(
            findings=findings,
            expected_cases=expected_cases,
            tool=args.tool,
            cwe=cwe_normalized,
            include_tn=not args.no_tn
        )

        if args.verbose:
            print("\n[4/4] Writing metrics...")
        write_metrics_json(result, out_path)

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
    print("VEP Unified Evaluation Result (v2)")
    print("=" * 60)
    print(f"Tool: {result.tool}")
    print(f"CWE: {result.cwe}")
    print(f"Total findings: {result.total_findings}")
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
    print(f"✅ Metrics written to: {out_path}")
    print("")

    return 0


if __name__ == "__main__":
    sys.exit(main())
