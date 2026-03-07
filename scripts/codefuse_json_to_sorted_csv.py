import argparse
import csv
import json
import re
from pathlib import Path


BENCHMARK_RE = re.compile(r"(BenchmarkTest\d{5})")


def extract_testcase(record):
    for key in ("testcase", "sinkFile", "file", "srcFile", "methodSig"):
        value = record.get(key)
        if isinstance(value, str):
            match = BENCHMARK_RE.search(value)
            if match:
                return match.group(1)
    return None


def sort_key(testcase):
    return int(testcase[-5:])


def load_records(input_json):
    with open(input_json, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, list):
        return data

    if isinstance(data, dict):
        for key in ("results", "findings", "data"):
            value = data.get(key)
            if isinstance(value, list):
                return value

    raise RuntimeError(f"Unsupported JSON format: {input_json}")


def main():
    parser = argparse.ArgumentParser(
        description="Convert CodeFuse JSON findings to deduplicated benchmark-sorted CSV."
    )
    parser.add_argument("input_json", help="Sparrow query JSON output path")
    parser.add_argument("output_csv", help="Output CSV path")
    args = parser.parse_args()

    records = load_records(args.input_json)
    testcase_map = {}

    for record in records:
        if not isinstance(record, dict):
            continue

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

    output_path = Path(args.output_csv)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["testcase", "ruleId", "file", "line"])
        for row in sorted_rows:
            writer.writerow([row["testcase"], row["ruleId"], row["file"], row["line"]])

    print(f"[+] Input findings: {len(records)}")
    print(f"[+] Unique testcases: {len(sorted_rows)}")
    print(f"[+] Wrote sorted CSV: {output_path}")


if __name__ == "__main__":
    main()
