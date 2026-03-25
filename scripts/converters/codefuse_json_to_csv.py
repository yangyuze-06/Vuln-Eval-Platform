import argparse
import csv
import json
import re
from pathlib import Path


BENCHMARK_RE = re.compile(r"BenchmarkTest\d{5}")
BENCHMARK_ID_RE = re.compile(r"BenchmarkTest(\d{5})")
MAX_SORT_INT = 10**18


def load_records(input_json: Path):
    with input_json.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, list):
        return data

    if isinstance(data, dict):
        for key in ("results", "findings", "data"):
            value = data.get(key)
            if isinstance(value, list):
                return value

    raise RuntimeError(f"Unsupported JSON format: {input_json}")


def extract_testcase(record: dict, unknown_label: str):
    for key in ("testcase", "sinkFile", "file", "srcFile", "methodSig"):
        value = record.get(key)
        if isinstance(value, str):
            match = BENCHMARK_RE.search(value)
            if match:
                return match.group(0)
    return unknown_label


def extract_file(record: dict):
    return str(record.get("sinkFile") or record.get("file") or record.get("srcFile") or "")


def extract_line(record: dict):
    for key in ("line", "sinkLine", "srcLine"):
        value = record.get(key)
        if value is not None and str(value) != "":
            return str(value)
    return ""


def extract_rule_id(record: dict, default_rule: str):
    value = record.get("ruleId")
    if isinstance(value, str) and value.strip():
        return value.strip()
    return default_rule


def testcase_sort_key(testcase: str):
    match = BENCHMARK_ID_RE.search(testcase)
    if match:
        return (0, int(match.group(1)))
    return (1, testcase)


def to_int_or_max(value: str):
    try:
        return int(value)
    except (TypeError, ValueError):
        return MAX_SORT_INT


def build_rows(records, default_rule: str, include_reason: bool, unknown_label: str):
    rows = []
    for record in records:
        if not isinstance(record, dict):
            continue

        testcase = extract_testcase(record, unknown_label=unknown_label)
        rule_id = extract_rule_id(record, default_rule=default_rule)
        file_path = extract_file(record)
        line = extract_line(record)
        reason = str(record.get("reason") or "")
        rows.append((testcase, rule_id, file_path, line, reason))

    rows.sort(
        key=lambda row: (
            testcase_sort_key(row[0]),
            to_int_or_max(row[3]),
            row[2],
            row[1],
            row[4],
        )
    )

    if include_reason:
        return rows

    return [(testcase, rule_id, file_path, line, "") for testcase, rule_id, file_path, line, _ in rows]


def dedup_by_testcase(rows):
    deduped = []
    seen = set()
    for row in rows:
        testcase = row[0]
        if testcase in seen:
            continue
        seen.add(testcase)
        deduped.append(row)
    return deduped


def main():
    parser = argparse.ArgumentParser(
        description="Convert Sparrow/CodeFuse JSON findings to benchmark-style CSV."
    )
    parser.add_argument("input_json", help="Input findings JSON path")
    parser.add_argument("output_csv", help="Output CSV path")
    parser.add_argument(
        "--default-rule",
        default="CWE-022",
        help='Default ruleId if missing in JSON (default: "CWE-022")',
    )
    parser.add_argument(
        "--include-reason",
        action="store_true",
        help='Include a fifth "reason" column in CSV.',
    )
    parser.add_argument(
        "--no-dedup-testcase",
        action="store_true",
        help="Do not deduplicate findings by testcase (default is dedup).",
    )
    parser.add_argument(
        "--unknown-label",
        default="UNKNOWN",
        help='Label for records where testcase cannot be extracted (default: "UNKNOWN").',
    )
    args = parser.parse_args()

    input_path = Path(args.input_json)
    output_path = Path(args.output_csv)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    records = load_records(input_path)
    rows = build_rows(
        records,
        default_rule=args.default_rule,
        include_reason=args.include_reason,
        unknown_label=args.unknown_label,
    )

    if not args.no_dedup_testcase:
        rows = dedup_by_testcase(rows)

    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if args.include_reason:
            writer.writerow(["testcase", "ruleId", "file", "line", "reason"])
            for testcase, rule_id, file_path, line, reason in rows:
                writer.writerow([testcase, rule_id, file_path, line, reason])
        else:
            writer.writerow(["testcase", "ruleId", "file", "line"])
            for testcase, rule_id, file_path, line, _ in rows:
                writer.writerow([testcase, rule_id, file_path, line])

    print(f"[+] Input records: {len(records)}")
    print(f"[+] Output rows: {len(rows)}")
    print(f"[+] Wrote CSV: {output_path}")


if __name__ == "__main__":
    main()
