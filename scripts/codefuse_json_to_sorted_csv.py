import argparse
import csv
import json
import re
from pathlib import Path


BENCHMARK_RE = re.compile(r"(BenchmarkTest\d{5})")
TESTCASE_ID_RE = re.compile(r"BenchmarkTest(\d+)\.java$")
MAX_SORT_INT = 10**18


def extract_testcase(record):
    for key in ("testcase", "sinkFile", "file", "srcFile", "methodSig"):
        value = record.get(key)
        if isinstance(value, str):
            match = BENCHMARK_RE.search(value)
            if match:
                return match.group(1)
    return None


def extract_testcase_id(sink_file):
    if not isinstance(sink_file, str):
        return -1

    match = TESTCASE_ID_RE.search(sink_file)
    if match:
        return int(match.group(1))

    # Fallback: still try to extract when suffix is not exactly ".java".
    fallback = re.search(r"BenchmarkTest(\d+)", sink_file)
    return int(fallback.group(1)) if fallback else -1


def to_int_or_max(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return MAX_SORT_INT


def sort_key(testcase):
    return int(testcase[-5:])


def load_records(input_json):
    with open(input_json, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, list):
        return data, None, None

    if isinstance(data, dict):
        for key in ("results", "findings", "data"):
            value = data.get(key)
            if isinstance(value, list):
                return value, data, key

    raise RuntimeError(f"Unsupported JSON format: {input_json}")


def sort_records(records, add_testcase_id=False):
    prepared = []
    for idx, record in enumerate(records):
        if not isinstance(record, dict):
            continue

        sink_file = str(record.get("sinkFile") or record.get("file") or "")
        line_value = record.get("line")
        if line_value is None:
            line_value = record.get("sinkLine")

        testcase_id = extract_testcase_id(sink_file)
        testcase_sort = testcase_id if testcase_id >= 0 else MAX_SORT_INT
        line_sort = to_int_or_max(line_value)

        normalized = dict(record)
        if add_testcase_id and testcase_id >= 0:
            normalized["testcaseId"] = testcase_id

        # Deterministic tie-breakers for fully stable output.
        normalized_dump = json.dumps(normalized, ensure_ascii=False, sort_keys=True)
        prepared.append(
            (
                testcase_sort,
                line_sort,
                sink_file,
                str(normalized.get("ruleId", "")),
                normalized_dump,
                idx,
                normalized,
            )
        )

    prepared.sort(key=lambda item: item[:6])
    return [item[6] for item in prepared]


def build_output_payload(records, container, list_key):
    if container is None:
        return records

    payload = dict(container)
    payload[list_key] = records
    return payload


def write_json(path, payload):
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write("\n")


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Convert CodeFuse JSON findings to deterministic benchmark-sorted JSON/CSV."
        )
    )
    parser.add_argument("input_json", help="Sparrow query JSON output path")
    parser.add_argument("output_csv", help="Output CSV path")
    parser.add_argument(
        "--sorted-json-out",
        help="Optional path to write deterministic sorted JSON output.",
    )
    parser.add_argument(
        "--rewrite-input-json",
        action="store_true",
        help="Force rewriting input JSON in deterministic sorted order (default behavior).",
    )
    parser.add_argument(
        "--skip-rewrite-input-json",
        action="store_true",
        help="Do not rewrite the input JSON file.",
    )
    parser.add_argument(
        "--add-testcase-id",
        action="store_true",
        help='Add "testcaseId" to each JSON record when writing sorted JSON.',
    )
    args = parser.parse_args()

    records, container, list_key = load_records(args.input_json)
    sorted_records = sort_records(records, add_testcase_id=args.add_testcase_id)
    testcase_map = {}

    for record in sorted_records:
        testcase = extract_testcase(record)
        if not testcase:
            continue

        if testcase not in testcase_map:
            testcase_map[testcase] = {
                "testcase": testcase,
                "ruleId": str(record.get("ruleId", "CWE-022")),
                "file": str(record.get("sinkFile") or record.get("file") or ""),
                "line": record.get("sinkLine") or record.get("line") or "",
            }

    sorted_rows = [testcase_map[k] for k in sorted(testcase_map.keys(), key=sort_key)]

    if args.sorted_json_out:
        payload = build_output_payload(sorted_records, container, list_key)
        write_json(args.sorted_json_out, payload)
        print(f"[+] Wrote sorted JSON: {args.sorted_json_out}")

    rewrite_input_json = True
    if args.skip_rewrite_input_json:
        rewrite_input_json = False
    elif args.rewrite_input_json:
        rewrite_input_json = True

    if rewrite_input_json:
        payload = build_output_payload(sorted_records, container, list_key)
        write_json(args.input_json, payload)
        print(f"[+] Rewrote input JSON in sorted order: {args.input_json}")

    output_path = Path(args.output_csv)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["testcase", "ruleId", "file", "line"])
        for row in sorted_rows:
            writer.writerow([row["testcase"], row["ruleId"], row["file"], row["line"]])

    print(f"[+] Input findings: {len(records)}")
    print(f"[+] Sorted findings: {len(sorted_records)}")
    print(f"[+] Unique testcases: {len(sorted_rows)}")
    print(f"[+] Wrote sorted CSV: {output_path}")


if __name__ == "__main__":
    main()
