#!/usr/bin/env python3
"""
VEP Cross-platform Evaluation Results Comparator
比较两个评测结果（Mac vs Linux）找出差异的 testcase
"""
import sys
import os
import json
import csv
from pathlib import Path
from collections import defaultdict

def load_metrics(path):
    """Load metrics.json"""
    if not os.path.exists(path):
        return None
    with open(path, 'r') as f:
        return json.load(f)

def load_testcases_from_csv(path, testcase_field=None):
    """Load testcase set from CSV"""
    if not os.path.exists(path):
        return set()

    with open(path, 'r') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames

        if not fieldnames:
            return set()

        if testcase_field is None:
            for candidate in ['testcase', 'testcaseId', 'testCase', 'name']:
                if candidate in fieldnames:
                    testcase_field = candidate
                    break

        if testcase_field not in fieldnames:
            return set()

        testcases = set()
        for row in reader:
            tc = row.get(testcase_field, '').strip()
            if tc:
                testcases.add(tc)
        return testcases

def load_eval_dir(eval_dir):
    """Load all CSVs from eval directory"""
    eval_path = Path(eval_dir)

    result = {
        'metrics': None,
        'tp': set(),
        'fp': set(),
        'fn': set(),
        'outside_scope': set()
    }

    metrics_file = eval_path / 'metrics.json'
    if metrics_file.exists():
        result['metrics'] = load_metrics(str(metrics_file))

    for category in ['tp', 'fp', 'fn', 'outside_scope']:
        csv_file = eval_path / f'{category}.csv'
        if csv_file.exists():
            result[category] = load_testcases_from_csv(str(csv_file))

    return result

def compare_sets(left_set, right_set, left_label, right_label):
    """Compare two sets and return diff"""
    left_only = left_set - right_set
    right_only = right_set - left_set
    common = left_set & right_set

    return {
        'left_only': sorted(left_only),
        'right_only': sorted(right_only),
        'common': sorted(common),
        'left_count': len(left_set),
        'right_count': len(right_set),
        'common_count': len(common),
        'left_label': left_label,
        'right_label': right_label
    }

def generate_markdown_report(comparison, left_label, right_label, cwe, ground_truth_path, out_path):
    """Generate markdown report"""

    lines = [
        "# Cross-platform Evaluation Comparison",
        "",
        "## Inputs",
        "",
        f"- **Left ({left_label})**: `{comparison['left_path']}`",
        f"- **Right ({right_label})**: `{comparison['right_path']}`",
        f"- **Ground Truth**: `{ground_truth_path}`",
        f"- **CWE**: {cwe if cwe else 'ALL'}",
        ""
    ]

    # Metrics diff
    lines.append("## Metrics Diff")
    lines.append("")

    left_m = comparison['left_metrics']
    right_m = comparison['right_metrics']

    if left_m and right_m:
        lines.append("| Metric | " + left_label + " | " + right_label + " | Diff |")
        lines.append("|--------|---------|---------|------|")

        for key in ['tp', 'fp', 'fn', 'precision', 'recall', 'f1']:
            if key in left_m and key in right_m:
                left_val = left_m[key]
                right_val = right_m[key]
                diff = ""
                if isinstance(left_val, (int, float)) and isinstance(right_val, (int, float)):
                    diff_val = right_val - left_val
                    diff = f"{diff_val:+.4f}" if isinstance(left_val, float) else f"{diff_val:+d}"
                lines.append(f"| {key} | {left_val} | {right_val} | {diff} |")
        lines.append("")
    else:
        lines.append("⚠️ Metrics not available for comparison")
        lines.append("")

    # TP/FP/FN/Outside-scope diffs
    for category in ['tp', 'fp', 'fn', 'outside_scope']:
        diff = comparison[f'{category}_diff']
        lines.append(f"## {category.upper()} Set Diff")
        lines.append("")
        lines.append(f"- **{left_label} count**: {diff['left_count']}")
        lines.append(f"- **{right_label} count**: {diff['right_count']}")
        lines.append(f"- **Common**: {diff['common_count']}")
        lines.append("")

        if diff['left_only']:
            lines.append(f"### {left_label}-only ({len(diff['left_only'])} testcases)")
            lines.append("")
            for tc in diff['left_only']:
                lines.append(f"- `{tc}`")
            lines.append("")

        if diff['right_only']:
            lines.append(f"### {right_label}-only ({len(diff['right_only'])} testcases)")
            lines.append("")
            for tc in diff['right_only']:
                lines.append(f"- `{tc}`")
            lines.append("")

    # Suspect testcases
    lines.append("## Suspect Testcases")
    lines.append("")

    suspects = []

    fn_diff = comparison['fn_diff']
    if fn_diff['left_only']:
        suspects.append(f"- **{left_label} extra FN** ({len(fn_diff['left_only'])}): {', '.join(fn_diff['left_only'])}")
    if fn_diff['right_only']:
        suspects.append(f"- **{right_label} extra FN** ({len(fn_diff['right_only'])}): {', '.join(fn_diff['right_only'])}")

    tp_diff = comparison['tp_diff']
    if tp_diff['left_only']:
        suspects.append(f"- **{left_label} extra TP** ({len(tp_diff['left_only'])}): {', '.join(tp_diff['left_only'])}")
    if tp_diff['right_only']:
        suspects.append(f"- **{right_label} extra TP** ({len(tp_diff['right_only'])}): {', '.join(tp_diff['right_only'])}")

    if suspects:
        lines.extend(suspects)
    else:
        lines.append("✅ No suspect testcases found (results match)")

    lines.append("")

    # Initial diagnosis
    lines.append("## Initial Diagnosis")
    lines.append("")

    if not suspects:
        lines.append("✅ **Status**: Results are consistent across platforms")
    else:
        lines.append("⚠️ **Status**: Cross-platform inconsistency detected")
        lines.append("")
        lines.append("### Possible Root Causes (需进一步验证)")
        lines.append("")
        lines.append("1. **Analyzer result differs**: raw SARIF/JSON 在两个平台本身不同")
        lines.append("2. **Converter dropped finding**: raw 有 finding 但 CSV 丢失")
        lines.append("3. **Testcase extraction mismatch**: CSV 有 finding 但 testcase 名解析不一致")
        lines.append("4. **Path normalization issue**: /Users vs /home, symlink, URL encoding")
        lines.append("5. **Case sensitivity issue**: macOS 默认大小写不敏感，Linux 大小写敏感")
        lines.append("6. **Tool version mismatch**: CodeQL/CodeFuse/JDK 版本不同")
        lines.append("7. **Database/build mismatch**: 两边不是同一个 extracted database")
        lines.append("8. **Nondeterministic ordering/dedup**: set/dict 顺序导致保留不同 finding")
        lines.append("")
        lines.append("### Next Steps")
        lines.append("")
        lines.append("1. 对 suspect testcases 检查 raw findings (SARIF/JSON)")
        lines.append("2. 对 suspect testcases 检查 normalized CSV findings")
        lines.append("3. 比较两边环境指纹 (运行 collect_env_fingerprint.py)")
        lines.append("4. 检查 testcase 路径标准化逻辑")
        lines.append("5. 检查 evaluator 匹配逻辑")

    lines.append("")

    with open(out_path, 'w') as f:
        f.write('\n'.join(lines))

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Compare two VEP evaluation results")
    parser.add_argument("--left", required=True, help="Left eval dir or metrics.json or CSV")
    parser.add_argument("--right", required=True, help="Right eval dir or metrics.json or CSV")
    parser.add_argument("--left-label", default="mac", help="Label for left side")
    parser.add_argument("--right-label", default="linux", help="Label for right side")
    parser.add_argument("--ground-truth", help="Ground truth CSV path")
    parser.add_argument("--cwe", help="CWE identifier")
    parser.add_argument("--out", help="Output markdown report path")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    args = parser.parse_args()

    # Load left and right
    left = load_eval_dir(args.left)
    right = load_eval_dir(args.right)

    # Compare
    comparison = {
        'left_path': args.left,
        'right_path': args.right,
        'left_metrics': left['metrics'],
        'right_metrics': right['metrics'],
        'tp_diff': compare_sets(left['tp'], right['tp'], args.left_label, args.right_label),
        'fp_diff': compare_sets(left['fp'], right['fp'], args.left_label, args.right_label),
        'fn_diff': compare_sets(left['fn'], right['fn'], args.left_label, args.right_label),
        'outside_scope_diff': compare_sets(left['outside_scope'], right['outside_scope'], args.left_label, args.right_label)
    }

    # Print summary
    print(f"=== Comparison: {args.left_label} vs {args.right_label} ===")
    print()

    if left['metrics'] and right['metrics']:
        print("Metrics:")
        for key in ['tp', 'fp', 'fn', 'precision', 'recall', 'f1']:
            if key in left['metrics'] and key in right['metrics']:
                lv = left['metrics'][key]
                rv = right['metrics'][key]
                print(f"  {key:12s}: {args.left_label}={lv:8} {args.right_label}={rv:8}")
    print()

    diff_found = False
    for category in ['tp', 'fp', 'fn', 'outside_scope']:
        diff = comparison[f'{category}_diff']
        if diff['left_only'] or diff['right_only']:
            diff_found = True
            print(f"{category.upper()} Diff:")
            print(f"  {args.left_label}-only: {len(diff['left_only'])}")
            print(f"  {args.right_label}-only: {len(diff['right_only'])}")
            if args.verbose:
                if diff['left_only']:
                    print(f"    {args.left_label}-only testcases: {', '.join(diff['left_only'])}")
                if diff['right_only']:
                    print(f"    {args.right_label}-only testcases: {', '.join(diff['right_only'])}")
            print()

    if not diff_found:
        print("✅ No differences found")
    else:
        print("⚠️ Differences detected")

    # Generate report
    if args.out:
        generate_markdown_report(comparison, args.left_label, args.right_label,
                                args.cwe, args.ground_truth, args.out)
        print(f"📄 Report saved to: {args.out}")

    return 0

if __name__ == "__main__":
    sys.exit(main())
