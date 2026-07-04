#!/usr/bin/env bash
set -e

echo "========================================="
echo "   CodeQL Evaluation Framework"
echo "========================================="

if [ ! -d "experiments" ]; then
    echo "❌ experiments/ directory not found."
    exit 1
fi

echo "[+] Checking SARIF files..."

missing=0

for dir in experiments/*/; do
    cwe=$(basename "$dir")

    # 查找 results 子目录里的 sarif
    sarif_file=$(find "$dir/results" -name "*.sarif" 2>/dev/null || true)

    if [ -z "$sarif_file" ]; then
        echo "❌ Missing SARIF file for $cwe"
        missing=1
    else
        echo "✔ Found SARIF for $cwe"
    fi
done

if [ "$missing" -eq 1 ]; then
    echo ""
    echo "⚠ Some SARIF files are missing."
    echo "Please run CodeQL analysis before evaluation."
    exit 1
fi

echo ""
echo "[+] All SARIF files detected."
echo ""

# 激活虚拟环境
if [ -d ".venv" ]; then
    echo "[+] Activating virtual environment"
    source .venv/bin/activate
fi

echo "[+] Step 1: Aggregating metrics..."
python3 scripts/evaluation/aggregate_results.py

echo "[+] Step 2: Generating plots..."
python3 scripts/reporting/plots_metrics.py

echo "[+] Step 3: Generating reports..."
python3 scripts/reporting/generate_report.py

echo ""
echo "========================================="
echo "   Evaluation Completed Successfully"
echo "========================================="
echo ""
echo "Reports generated in reports/"
echo "Open reports/report.md to view results."
