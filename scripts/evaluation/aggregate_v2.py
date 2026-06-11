#!/usr/bin/env python3
"""VEP Aggregate v2 CLI - Phase 2D Entry Point.

Aggregate multiple CWE v2 metrics.json files into overall summary.

Usage:
    # Aggregate specific metrics
    python scripts/evaluation/aggregate_v2.py \\
        --metrics experiments/cwe-022/eval/codefuse_eval_v2b/metrics.json \\
                  experiments/cwe-089/eval/codefuse_eval_v2b/metrics.json \\
        --out reports/data/metrics_v2_codefuse_subset.json

    # Auto-discover from eval root
    python scripts/evaluation/aggregate_v2.py \\
        --eval-root experiments \\
        --tool codefuse \\
        --eval-dir-name codefuse_eval_v2b \\
        --out reports/data/metrics_v2_codefuse.json \\
        --manifest configs/cwe_manifest.yml

Phase 2D: Multi-CWE Aggregator
Does NOT replace existing aggregate_results.py.
"""

import argparse
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from vep.evaluation.aggregate import load_metrics_json, aggregate_metrics, write_aggregate_json
from vep.core.normalization import normalize_cwe_id


def build_parser() -> argparse.ArgumentParser:
    """Build argument parser."""
    parser = argparse.ArgumentParser(
        description="Aggregate multiple CWE v2 metrics into overall summary."
    )
    parser.add_argument(
        "--metrics",
        nargs="+",
        help="List of metrics.json files to aggregate"
    )
    parser.add_argument(
        "--eval-root",
        help="Root directory to search for metrics (e.g., experiments)"
    )
    parser.add_argument(
        "--tool",
        help="Tool name filter (used with --eval-root)"
    )
    parser.add_argument(
        "--eval-dir-name",
        help="Eval directory name pattern (e.g., codefuse_eval_v2b)"
    )
    parser.add_argument(
        "--out",
        required=True,
        help="Output aggregate JSON path"
    )
    parser.add_argument(
        "--manifest",
        help="Path to cwe_manifest.yml (for CWE discovery)"
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Strict mode: fail on missing metrics or inconsistencies"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Verbose output"
    )
    return parser


def discover_metrics_from_root(
    eval_root: Path,
    eval_dir_name: str,
    manifest_path: Path = None,
    verbose: bool = False
) -> list:
    """Discover metrics files from eval root.

    Args:
        eval_root: Root directory (e.g., experiments)
        eval_dir_name: Eval directory name (e.g., codefuse_eval_v2b)
        manifest_path: Optional manifest for CWE list
        verbose: Verbose output

    Returns:
        List of (cwe, metrics_path) tuples
    """
    discovered = []
    missing = []

    # Get CWE list from manifest if provided
    if manifest_path and manifest_path.exists():
        try:
            import yaml
            with manifest_path.open("r") as f:
                manifest = yaml.safe_load(f)
            cwe_ids = [c["id"] for c in manifest.get("cwes", [])]
        except Exception as e:
            if verbose:
                print(f"⚠️  Warning: Could not load manifest: {e}")
            cwe_ids = []
    else:
        cwe_ids = []

    # Try to discover from manifest CWEs
    if cwe_ids and eval_dir_name:
        for cwe_id in cwe_ids:
            cwe_normalized = normalize_cwe_id(cwe_id)
            # Try common path patterns
            patterns = [
                eval_root / f"cwe-{cwe_id}" / "eval" / eval_dir_name / "metrics.json",
                eval_root / f"CWE-{cwe_id}" / "eval" / eval_dir_name / "metrics.json",
            ]
            found = False
            for pattern in patterns:
                if pattern.exists():
                    discovered.append((cwe_normalized, pattern))
                    found = True
                    break
            if not found:
                missing.append(cwe_normalized)

    # Also scan eval_root directly
    if not discovered:
        if eval_dir_name:
            pattern = f"**/eval/{eval_dir_name}/metrics.json"
        else:
            pattern = "**/eval/**/metrics.json"

        for metrics_path in eval_root.glob(pattern):
            # Try to extract CWE from path
            parts = metrics_path.parts
            for part in parts:
                if part.startswith("cwe-") or part.startswith("CWE-"):
                    cwe_normalized = normalize_cwe_id(part)
                    discovered.append((cwe_normalized, metrics_path))
                    break

    return discovered, missing


def main() -> int:
    """Main entry point."""
    parser = build_parser()
    args = parser.parse_args()

    # Validate arguments
    if not args.metrics and not args.eval_root:
        print("❌ Error: Must provide either --metrics or --eval-root", file=sys.stderr)
        return 1

    out_path = Path(args.out).resolve()
    manifest_path = Path(args.manifest).resolve() if args.manifest else None

    metrics_to_aggregate = []
    missing_cwes = []

    # Collect metrics from explicit list
    if args.metrics:
        if args.verbose:
            print(f"Loading {len(args.metrics)} explicit metrics files...")
        for metrics_path in args.metrics:
            metrics_path = Path(metrics_path).resolve()
            if not metrics_path.exists():
                print(f"❌ Error: Metrics file not found: {metrics_path}", file=sys.stderr)
                if args.strict:
                    return 1
                continue
            try:
                metrics = load_metrics_json(metrics_path)
                metrics_to_aggregate.append(metrics)
                if args.verbose:
                    cwe = metrics.get("cwe", "unknown")
                    print(f"  ✅ {cwe}: {metrics_path}")
            except Exception as e:
                print(f"❌ Error loading {metrics_path}: {e}", file=sys.stderr)
                if args.strict:
                    return 1

    # Discover metrics from eval root
    if args.eval_root:
        eval_root = Path(args.eval_root).resolve()
        if not eval_root.exists():
            print(f"❌ Error: Eval root not found: {eval_root}", file=sys.stderr)
            return 1

        if args.verbose:
            print(f"\nDiscovering metrics from {eval_root}...")

        discovered, missing = discover_metrics_from_root(
            eval_root,
            args.eval_dir_name,
            manifest_path,
            args.verbose
        )

        for cwe, metrics_path in discovered:
            try:
                metrics = load_metrics_json(metrics_path)
                # Avoid duplicates
                if metrics not in metrics_to_aggregate:
                    metrics_to_aggregate.append(metrics)
                if args.verbose:
                    print(f"  ✅ {cwe}: {metrics_path}")
            except Exception as e:
                print(f"⚠️  Warning: Could not load {metrics_path}: {e}")
                if args.strict:
                    return 1

        missing_cwes.extend(missing)

    # Check if we have metrics
    if not metrics_to_aggregate:
        print("❌ Error: No metrics to aggregate", file=sys.stderr)
        return 1

    # Report missing in strict mode
    if missing_cwes and args.strict:
        print(f"❌ Error: Missing metrics for CWEs in strict mode: {missing_cwes}", file=sys.stderr)
        return 1

    # Aggregate
    try:
        if args.verbose:
            print(f"\nAggregating {len(metrics_to_aggregate)} metrics...")

        aggregate = aggregate_metrics(
            metrics_to_aggregate,
            tool=args.tool,
            strict=args.strict
        )

        # Add missing list
        aggregate["missing"] = sorted(set(missing_cwes))
        aggregate["skipped_count"] = len(missing_cwes)

        # Write output
        write_aggregate_json(aggregate, out_path)

        # Print summary
        print("\n" + "=" * 60)
        print("VEP Aggregate v2 Result")
        print("=" * 60)
        print(f"Tool: {aggregate['tool']}")
        print(f"FP mode: {aggregate['fp_mode']}")
        print(f"Included: {aggregate['included_count']} CWEs")
        if aggregate.get("skipped_count", 0) > 0:
            print(f"Skipped: {aggregate['skipped_count']} CWEs")
        if aggregate.get("missing"):
            print(f"Missing: {', '.join(aggregate['missing'])}")
        print("")
        print("Overall Metrics:")
        overall = aggregate["overall"]
        print(f"  TP: {overall['tp']}")
        print(f"  FP: {overall['fp']}")
        print(f"  FN: {overall['fn']}")
        if "tn" in overall:
            print(f"  TN: {overall['tn']}")
        print(f"  Precision: {overall['precision']:.4f}")
        print(f"  Recall: {overall['recall']:.4f}")
        print(f"  F1: {overall['f1']:.4f}")
        print("=" * 60)
        print(f"✅ Aggregate written to: {out_path}")
        print("")

        return 0

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
