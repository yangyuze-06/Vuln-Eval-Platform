#!/usr/bin/env python3
"""Evaluate CodeFuse-Query findings against OWASP Benchmark ground truth."""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


BENCHMARK_RE = re.compile(r"(BenchmarkTest(\d+))")
CWE_RE = re.compile(r"(?i)(?:cwe[-_ ]*)?0*(\d+)([a-z]*)")
MAX_SORT_INT = 10**18

HEADER_ALIASES = {
    "testcase": [
        "testcase",
        "classname",
        "class",
        "name",
        "testname",
        "test_name",
    ],
    "cwe": ["cwe", "cweid", "cwe_id", "category"],
    "truth": [
        "realvulnerability",
        "real_vulnerability",
        "expected",
        "result",
        "positive",
        "vulnerable",
        "isvulnerable",
        "groundtruth",
        "truth",
    ],
}

HEADER_ALIAS_SET = {key: set(values) for key, values in HEADER_ALIASES.items()}

POSITIVE_VALUES = {
    "1",
    "true",
    "positive",
    "vulnerable",
    "yes",
    "y",
    "real",
    "tp",
}

NEGATIVE_VALUES = {
    "0",
    "false",
    "negative",
    "safe",
    "no",
    "n",
    "notvulnerable",
    "not_vulnerable",
    "fp",
}


def normalize_header_name(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def normalize_truth(value: object) -> Optional[bool]:
    if value is None:
        return None
    text = normalize_header_name(str(value))
    if text in POSITIVE_VALUES:
        return True
    if text in NEGATIVE_VALUES:
        return False
    return None


def canonicalize_cwe(value: object) -> Optional[Tuple[int, str]]:
    if value is None:
        return None

    text = str(value).strip()
    match = CWE_RE.search(text)
    if not match:
        return None

    return int(match.group(1)), match.group(2).upper()


def format_cwe(cwe_key: Tuple[int, str]) -> str:
    number, suffix = cwe_key
    return f"CWE-{number:03d}{suffix}"


def extract_testcase(value: object) -> Tuple[Optional[str], Optional[int]]:
    if value is None:
        return None, None

    match = BENCHMARK_RE.search(str(value))
    if not match:
        return None, None

    testcase = match.group(1)
    testcase_id = int(match.group(2))
    return testcase, testcase_id


def to_int_or_none(value: object) -> Optional[int]:
    if value is None:
        return None
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


def to_sort_int(value: Optional[int]) -> int:
    return value if value is not None else MAX_SORT_INT


def lookup_field(row: Dict[str, object], field_group: str) -> Optional[object]:
    normalized = {normalize_header_name(key): value for key, value in row.items()}
    for alias in HEADER_ALIASES[field_group]:
        if alias in normalized:
            return normalized[alias]
    return None


def looks_like_header(row: Sequence[str]) -> bool:
    normalized = {normalize_header_name(cell) for cell in row if cell}
    known = set().union(*HEADER_ALIAS_SET.values())
    return bool(normalized & known)


def iter_expected_rows(path: Path) -> Iterable[Dict[str, object]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        header: Optional[List[str]] = None

        for row in reader:
            if not row or all(not str(cell).strip() for cell in row):
                continue
            if str(row[0]).lstrip().startswith("#"):
                continue

            if header is None and looks_like_header(row):
                header = list(row)
                continue

            if header is not None:
                padded = list(row) + [""] * max(0, len(header) - len(row))
                yield dict(zip(header, padded))
                continue

            yield {
                "testcase": row[0] if len(row) > 0 else "",
                "category": row[1] if len(row) > 1 else "",
                "real vulnerability": row[2] if len(row) > 2 else "",
                "cwe": row[3] if len(row) > 3 else "",
            }


def load_ground_truth(path: Path, target_cwe: Tuple[int, str]) -> Tuple[set[str], set[str], set[str]]:
    positives: set[str] = set()
    negatives: set[str] = set()
    all_cases: set[str] = set()

    for row in iter_expected_rows(path):
        testcase_value = lookup_field(row, "testcase")
        cwe_value = lookup_field(row, "cwe")
        truth_value = lookup_field(row, "truth")

        testcase, _ = extract_testcase(testcase_value)
        cwe_key = canonicalize_cwe(cwe_value)
        truth = normalize_truth(truth_value)

        if testcase is None or cwe_key != target_cwe or truth is None:
            continue

        all_cases.add(testcase)
        if truth:
            positives.add(testcase)
        else:
            negatives.add(testcase)

    return positives, negatives, all_cases


def load_json_records(path: Path) -> List[object]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    if isinstance(data, list):
        return data

    if isinstance(data, dict):
        for key in ("results", "findings", "data"):
            value = data.get(key)
            if isinstance(value, list):
                return value

    raise RuntimeError(f"Unsupported JSON format: {path}")


def load_csv_records(path: Path) -> List[Dict[str, object]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader)


def detect_format(path: Path, requested: str) -> str:
    if requested != "auto":
        return requested

    suffix = path.suffix.lower()
    if suffix == ".json":
        return "json"
    if suffix == ".csv":
        return "csv"

    raise RuntimeError(f"Cannot auto-detect result format for: {path}")


def normalize_result_record(record: object, index: int) -> Optional[Dict[str, object]]:
    if not isinstance(record, dict):
        return None

    testcase = None
    testcase_id = None
    for key in ("testcase", "className", "classname", "name", "sinkFile", "file", "srcFile", "methodSig"):
        value = record.get(key)
        testcase, testcase_id = extract_testcase(value)
        if testcase is not None:
            break

    sink_file = record.get("sinkFile") or record.get("file") or record.get("srcFile") or ""
    line = (
        record.get("line")
        or record.get("sinkLine")
        or record.get("startLine")
        or ""
    )
    line_int = to_int_or_none(line)
    testcase_id = to_int_or_none(record.get("testcaseId")) or testcase_id
    rule_id = str(record.get("ruleId") or record.get("rule") or "")

    return {
        "index": index,
        "testcase": testcase,
        "testcaseId": testcase_id,
        "sinkFile": str(sink_file),
        "line": line,
        "lineInt": line_int,
        "ruleId": rule_id,
    }


def load_results(path: Path, fmt: str) -> Tuple[int, List[Dict[str, object]]]:
    raw_records = load_json_records(path) if fmt == "json" else load_csv_records(path)
    normalized: List[Dict[str, object]] = []

    for index, record in enumerate(raw_records):
        normalized_record = normalize_result_record(record, index)
        if normalized_record is not None:
            normalized.append(normalized_record)

    return len(raw_records), normalized


def finding_sort_key(record: Dict[str, object]) -> Tuple[int, int, str, str, int]:
    return (
        to_sort_int(record["testcaseId"]),
        to_sort_int(record["lineInt"]),
        str(record["sinkFile"]),
        str(record["ruleId"]),
        int(record["index"]),
    )


def deduplicate_findings(records: List[Dict[str, object]]) -> Tuple[Dict[str, Dict[str, object]], Dict[str, int]]:
    testcase_to_record: Dict[str, Dict[str, object]] = {}
    testcase_counts: Dict[str, int] = {}

    for record in sorted(records, key=finding_sort_key):
        testcase = record.get("testcase")
        if not testcase:
            continue
        testcase_counts[testcase] = testcase_counts.get(testcase, 0) + 1
        testcase_to_record.setdefault(testcase, record)

    return testcase_to_record, testcase_counts


def ordered_testcases(cases: Iterable[str]) -> List[str]:
    def testcase_key(testcase: str) -> Tuple[int, str]:
        _, testcase_id = extract_testcase(testcase)
        return to_sort_int(testcase_id), testcase

    return sorted(cases, key=testcase_key)


def write_case_csv(
    path: Path,
    cases: Iterable[str],
    testcase_to_record: Dict[str, Dict[str, object]],
    testcase_counts: Dict[str, int],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["testcase", "testcaseId", "sinkFile", "line", "ruleId", "findingCount"])

        for testcase in ordered_testcases(cases):
            record = testcase_to_record.get(testcase, {})
            _, testcase_id = extract_testcase(testcase)
            testcase_id = to_int_or_none(record.get("testcaseId")) or testcase_id or ""
            writer.writerow(
                [
                    testcase,
                    testcase_id,
                    record.get("sinkFile", ""),
                    record.get("line", ""),
                    record.get("ruleId", ""),
                    testcase_counts.get(testcase, 0),
                ]
            )


def round_metric(value: float) -> float:
    return round(value, 4)


def evaluate(
    expected_path: Path,
    results_path: Path,
    cwe_text: str,
    outdir: Path,
    fmt: str,
    fp_mode: str,
) -> Dict[str, object]:
    target_cwe = canonicalize_cwe(cwe_text)
    if target_cwe is None:
        raise RuntimeError(f"Unsupported CWE value: {cwe_text}")

    raw_findings, raw_records = load_results(results_path, fmt)
    testcase_to_record, testcase_counts = deduplicate_findings(raw_records)

    positives, negatives, all_scope_cases = load_ground_truth(expected_path, target_cwe)
    detected_cases = set(testcase_to_record)

    tp_cases = ordered_testcases(detected_cases & positives)
    fp_in_scope_cases = ordered_testcases(detected_cases & negatives)
    fp_all_non_gt_cases = ordered_testcases(detected_cases - positives)
    fn_cases = ordered_testcases(positives - detected_cases)
    in_scope_cases = detected_cases & all_scope_cases
    outside_scope_cases = detected_cases - all_scope_cases

    tp = len(tp_cases)
    fp_in_scope = len(fp_in_scope_cases)
    fp_all_non_gt = len(fp_all_non_gt_cases)
    fp = fp_all_non_gt if fp_mode == "all_non_gt" else fp_in_scope
    fn = len(fn_cases)
    dedup_findings = len(detected_cases)
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) else 0.0
    outside_scope_ratio = len(outside_scope_cases) / dedup_findings if dedup_findings else 0.0

    metrics = {
        "cwe": format_cwe(target_cwe),
        "results_file": str(results_path),
        "results_format": fmt,
        "fp_mode": fp_mode,
        "raw_findings": raw_findings,
        "dedup_findings": dedup_findings,
        "ground_truth_total": len(positives),
        "cwe_scope_total": len(all_scope_cases),
        "in_scope_findings": len(in_scope_cases),
        "outside_scope_findings": len(outside_scope_cases),
        "outside_scope_ratio": round_metric(outside_scope_ratio),
        "tp": tp,
        "fp": fp,
        "fp_in_scope": fp_in_scope,
        "fp_all_non_gt": fp_all_non_gt,
        "fn": fn,
        "precision": round_metric(precision),
        "recall": round_metric(recall),
        "f1": round_metric(f1),
    }

    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    write_case_csv(outdir / "tp.csv", tp_cases, testcase_to_record, testcase_counts)
    write_case_csv(
        outdir / "fp.csv",
        fp_all_non_gt_cases if fp_mode == "all_non_gt" else fp_in_scope_cases,
        testcase_to_record,
        testcase_counts,
    )
    write_case_csv(outdir / "fn.csv", fn_cases, testcase_to_record, testcase_counts)
    write_case_csv(outdir / "outside_scope.csv", outside_scope_cases, testcase_to_record, testcase_counts)

    return metrics


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Evaluate CodeFuse-Query findings against OWASP Benchmark expected results."
    )
    parser.add_argument("--expected", required=True, help="Path to expectedresults-1.2.csv")
    parser.add_argument("--results", required=True, help="Path to CodeFuse results JSON or CSV")
    parser.add_argument("--cwe", required=True, help="Target CWE, for example CWE-022")
    parser.add_argument("--outdir", required=True, help="Directory for metrics.json / tp.csv / fp.csv / fn.csv")
    parser.add_argument(
        "--format",
        choices=("auto", "json", "csv"),
        default="auto",
        help="Results file format. Default: auto",
    )
    parser.add_argument(
        "--fp-mode",
        choices=("in_scope", "all_non_gt"),
        default="all_non_gt",
        help=(
            "FP definition: 'all_non_gt' uses detected-ground_truth_positive; "
            "'in_scope' uses only CWE in-scope negatives."
        ),
    )
    return parser


def print_summary(metrics: Dict[str, object]) -> None:
    print(f"CWE: {metrics['cwe']}")
    print(f"FP mode: {metrics['fp_mode']}")
    print(f"Raw findings: {metrics['raw_findings']}")
    print(f"Dedup findings: {metrics['dedup_findings']}")
    print(f"Ground truth total: {metrics['ground_truth_total']}")
    print(f"In-scope findings: {metrics['in_scope_findings']}")
    print(f"Outside-scope findings: {metrics['outside_scope_findings']}")
    print(f"Outside-scope ratio: {metrics['outside_scope_ratio']:.4f}")
    print(f"TP: {metrics['tp']}")
    print(f"FP: {metrics['fp']}")
    print(f"FP (in-scope only): {metrics['fp_in_scope']}")
    print(f"FP (all non-GT): {metrics['fp_all_non_gt']}")
    print(f"FN: {metrics['fn']}")
    print(f"Precision: {metrics['precision']:.4f}")
    print(f"Recall: {metrics['recall']:.4f}")
    print(f"F1: {metrics['f1']:.4f}")


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    expected_path = Path(args.expected).resolve()
    results_path = Path(args.results).resolve()
    outdir = Path(args.outdir).resolve()
    fmt = detect_format(results_path, args.format)

    metrics = evaluate(expected_path, results_path, args.cwe, outdir, fmt, args.fp_mode)
    print_summary(metrics)


if __name__ == "__main__":
    main()
