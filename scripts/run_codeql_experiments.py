import os
import subprocess
import sys

def main():
    cwes_map = {
        "022": "CWE-022",
        "078": "CWE-078",
        "079": "CWE-079",
        "089": "CWE-089",
        "090": "CWE-090",
        "327": "CWE-327",
        "328": "CWE-328_328S",
        "330": "CWE-330",
        "501": "CWE-501",
        "614": "CWE-614",
        "643": "CWE-643"
    }

    db_path = "dataset/codeql-db/benchmark-java"
    if not os.path.exists(db_path):
        print(f"❌ CodeQL database not found at {db_path}")
        sys.exit(1)

    print("🚀 Starting CodeQL analysis for all CWEs...")

    for cwe_id, ql_dir in cwes_map.items():
        print(f"\n=========================================")
        print(f"   Analyzing CWE-{cwe_id} (Query dir: {ql_dir})")
        print(f"=========================================")
        
        sarif_out = f"experiments/cwe-{cwe_id}/results/codeql/cwe{cwe_id}.sarif"
        csv_out = f"experiments/cwe-{cwe_id}/results/codeql/cwe{cwe_id}.csv"
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(sarif_out), exist_ok=True)
        
        # 1. Run CodeQL Analyze
        cmd_analyze = [
            "codeql", "database", "analyze",
            db_path,
            f"rules/codeql-query/{ql_dir}",
            "--format=sarifv2.1.0",
            f"--output={sarif_out}"
        ]
        print(f"Running: {' '.join(cmd_analyze)}")
        res = subprocess.run(cmd_analyze)
        if res.returncode != 0:
            print(f"❌ CodeQL analyze failed for CWE-{cwe_id}")
            sys.exit(1)
            
        # 2. Run SARIF to CSV conversion
        cmd_convert = [
            "python3", "scripts/converters/sarif_to_csv.py",
            sarif_out,
            csv_out
        ]
        print(f"Running: {' '.join(cmd_convert)}")
        res = subprocess.run(cmd_convert)
        if res.returncode != 0:
            print(f"❌ CSV conversion failed for CWE-{cwe_id}")
            sys.exit(1)

    print("\n=========================================")
    print("   Running Evaluation Script")
    print("=========================================")
    res = subprocess.run(["./run_eval.sh"])
    if res.returncode != 0:
        print("❌ Evaluation script failed")
        sys.exit(1)

    print("\n🎉 CodeQL experiments and evaluation finished successfully!")

if __name__ == "__main__":
    main()
