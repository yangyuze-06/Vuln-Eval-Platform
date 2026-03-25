import json
import csv
import re

SARIF_FILE = "experiments/cwe-328_328S/results/codeql/cwe328_328S.sarif"
OUTPUT_CSV = "experiments/cwe-328_328S/results/codeql/cwe328_328S.csv"


pattern = re.compile(r"(BenchmarkTest\d{5})")

with open(SARIF_FILE, "r", encoding="utf-8") as f:
    sarif = json.load(f)

rows = []

runs = sarif.get("runs", [])
if not runs:
    raise RuntimeError("No runs found in SARIF")

for result in runs[0].get("results", []):
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

with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["testcase", "ruleId", "file", "line"])
    writer.writerows(rows)

print(f"[+] Converted {len(rows)} findings to {OUTPUT_CSV}")
