import json
import csv
import re
import argparse

SARIF_FILE = "experiments/cwe-328_328S/results/codeql/cwe328_328S.sarif"
OUTPUT_CSV = "experiments/cwe-328_328S/results/codeql/cwe328_328S.csv"


pattern = re.compile(r"(BenchmarkTest\d{5})")


def convert(sarif_file, output_csv):
    with open(sarif_file, "r", encoding="utf-8") as f:
        sarif = json.load(f)

    rows = []

    runs = sarif.get("runs", [])
    if not runs:
        raise RuntimeError("No runs found in SARIF")

    for run in runs:
        for result in run.get("results", []):
            rule_id = result.get("ruleId", "")

            for loc in result.get("locations", []):
                phys = loc.get("physicalLocation", {})
                artifact = phys.get("artifactLocation", {})
                uri = artifact.get("uri", "")

                region = phys.get("region", {})
                line = region.get("startLine", "")

                match = pattern.search(uri)
                testcase = match.group(1) if match else "UNKNOWN"

                rows.append([
                    testcase,
                    rule_id,
                    uri,
                    line
                ])

    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["testcase", "ruleId", "file", "line"])
        writer.writerows(rows)

    print(f"[+] Converted {len(rows)} findings to {output_csv}")


def main():
    parser = argparse.ArgumentParser(description="Convert CodeQL SARIF results to evaluation CSV.")
    parser.add_argument("sarif_file", nargs="?", default=SARIF_FILE)
    parser.add_argument("output_csv", nargs="?", default=OUTPUT_CSV)
    args = parser.parse_args()
    convert(args.sarif_file, args.output_csv)


if __name__ == "__main__":
    main()
