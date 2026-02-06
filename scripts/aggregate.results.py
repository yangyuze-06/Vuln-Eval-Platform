import os
import csv
import json
import re
from collections import defaultdict

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXPECTED_FILE = os.path.join(BASE_DIR, "expectedresults-1.2.csv")
EXPERIMENT_DIR = os.path.join(BASE_DIR, "experiments")
OUTPUT_JSON = os.path.join(BASE_DIR, "reports", "data", "summery.json")


# ----------------------------
# Ground Truth
# ----------------------------
def load_ground_truth():
    gt = defaultdict(lambda: {"rp": set(), "rn": set()})

    with open(EXPECTED_FILE, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)

        for row in reader:
            if not row or row[0].startswith('#'):
                continue

            testcase, _, real, cwe = row[:4]
            cwe_key = f"CWE-{cwe.strip()}"

            if real.strip().lower() == "true":
                gt[cwe_key]["rp"].add(testcase.strip())
            else:
                gt[cwe_key]["rn"].add(testcase.strip())

    return gt


# ----------------------------
# Load Tool Output
# ----------------------------
def load_detected(csv_file):
    detected = set()

    with open(csv_file, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            detected.add(row["testcase"].strip())

    return detected


# ----------------------------
# Evaluate
# ----------------------------
def evaluate_tool(gt, cwe_key, csv_path):
    rp = gt[cwe_key]["rp"]
    rn = gt[cwe_key]["rn"]

    detected = load_detected(csv_path)

    TP = detected & rp
    FP = detected & rn
    FN = rp - detected

    tp = len(TP)
    fp = len(FP)
    fn = len(FN)

    precision = tp / (tp + fp) if tp + fp else 0
    recall = tp / len(rp) if rp else 0
    fnr = fn / len(rp) if rp else 0
    fpr = fp / len(rn) if rn else 0
    fdr = fp / (tp + fp) if tp + fp else 0



    return {
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "fnr": round(fnr, 4),
        "fpr": round(fpr, 4),
        "fdr": round(fdr, 4)
        
    }


# ----------------------------
# 自动寻找 CSV
# ----------------------------
def find_csv(tool_dir):
    if not os.path.exists(tool_dir):
        return None

    for f in os.listdir(tool_dir):
        if f.endswith(".csv"):
            return os.path.join(tool_dir, f)

    return None


# ----------------------------
# Extract CWE key
# ----------------------------
def normalize_cwe(folder_name):
    match = re.search(r'(\d+)', folder_name)
    if not match:
        return None
    num = int(match.group(1))
    return f"CWE-{num}"

# ----------------------------
# Main
# ----------------------------
def main():
    gt = load_ground_truth()
    metrics = {}
    print("[DEBUG] scanning experiments folder")
    
    for cwe_folder in os.listdir(EXPERIMENT_DIR):
        folder_path = os.path.join(EXPERIMENT_DIR, cwe_folder)
        
        if not os.path.isdir(folder_path):
            continue
        cwe_key = normalize_cwe(cwe_folder)
        
        if not cwe_key or cwe_key not in gt:
            continue
        
        print(f"[DEBUG] processing {cwe_key}")
        codeql_dir = os.path.join(folder_path, "results", "codeql")
        
        codefuse_dir = os.path.join(folder_path, "results", "codefuse")
        
        codeql_csv = find_csv(codeql_dir)
        
        codefuse_csv = find_csv(codefuse_dir)
        
        metrics[cwe_key] = {
            "benchmark_total": len(gt[cwe_key]["rp"]) + len(gt[cwe_key]["rn"]),
            "real_positive": len(gt[cwe_key]["rp"]),
            "tools": {}
        }

        if codeql_csv:
            metrics[cwe_key]["tools"]["codeql"] = evaluate_tool(gt, cwe_key, codeql_csv)

        if codefuse_csv:
            metrics[cwe_key]["tools"]["codefuse"] = evaluate_tool(gt, cwe_key, codefuse_csv)

    # ⭐ 按 CWE 数字排序
    sorted_metrics = dict(
        sorted(metrics.items(), key=lambda x: int(x[0].split("-")[1]))
    )

    os.makedirs(os.path.dirname(OUTPUT_JSON), exist_ok=True)

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(sorted_metrics, f, indent=2)

    print(f"[+] Aggregated results saved to {OUTPUT_JSON}")


if __name__ == "__main__":
    main()
