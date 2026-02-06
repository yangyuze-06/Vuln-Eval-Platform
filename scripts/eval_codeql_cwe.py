#!/usr/bin/env python3
import csv
import argparse

def load_detected(detected_csv):
    detected = set()
    with open(detected_csv, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            testcase = row['testcase'].strip()
            if testcase:
                detected.add(testcase)
    return detected


def load_expected(expected_csv, target_cwe):
    real_positive = set()
    real_negative = set()

    with open(expected_csv, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            if not row or row[0].startswith('#'):
                continue

            testcase, category, real, cwe = row[:4]

            if cwe.strip() != str(target_cwe):
                continue

            testcase = testcase.strip()
            real = real.strip().lower()

            if real == 'true':
                real_positive.add(testcase)
            else:
                real_negative.add(testcase)

    return real_positive, real_negative


def main(args=None):
    if args is None:
        parser = argparse.ArgumentParser(
            description="CodeQL OWASP Benchmark Evaluation (CSV-based)"
        )
        parser.add_argument('--detected', required=True)
        parser.add_argument('--expected', required=True)
        parser.add_argument('--cwe', required=True, type=int)
        args = parser.parse_args()

    detected = load_detected(args.detected)
    real_positive, real_negative = load_expected(args.expected, args.cwe)

    total_cases = len(real_positive) + len(real_negative)

    TP = detected & real_positive
    FP = detected & real_negative
    FN = real_positive - detected
    TN = real_negative - detected   

    tp = len(TP)
    fp = len(FP)
    fn = len(FN)
    tn = len(TN)                   
    rp = len(real_positive)

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / rp if rp > 0 else 0.0
    fnr = fn / rp if rp > 0 else 0.0
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0   
    fdr = fp / (tp + fp) if (tp + fp) > 0 else 0.0
    
    fnr_label = "（全部命中）" if fnr == 0 else ""

    print("\n=== CodeQL Benchmark Evaluation ===")
    print(f"Target CWE            : CWE-{args.cwe}")
    print(f"Benchmark total cases : {total_cases}")
    print(f"Detected testcases    : {len(detected)}")
    print(f"Real Positive (GT)    : {rp}")
    print("----------------------------------")
    print(f"TP (True Positive)    : {tp}")
    print(f"FP (False Positive)   : {fp}")
    print(f"FN (False Negative)   : {fn}")
    print(f"TN (True Negative)    : {tn}")   
    print("----------------------------------")
    print(f"Precision             : {precision:.4f}")
    print(f"Recall                : {recall:.4f}")
    print(f"FNR (漏报率)          : {fnr:.4f} {fnr_label}")
    print(f"FPR (误报率)          : {fpr:.4f}")
    print(f"FDR (误检率)          : {fpr:.4f}")

    print("\n[Sample FN cases]")
    for name in list(FN)[:10]:
        print("  ", name)

    print("\n[Sample FP cases]")
    for name in list(FP)[:10]:
        print("  ", name)


if __name__ == '__main__':
    # ===== 可替换成你想要分析的数据路径 =====
    class Args:
        detected = "/home/ubuntu64/Security-Eval-Lab/experiments/cwe-xxx/results/codeql/cwexxx.csv"
        expected = "/home/ubuntu64/Security-Eval-Lab/expectedresults-1.2.csv"
        cwe = 22  # 替换成你要分析的CWE编号

    main(Args())
