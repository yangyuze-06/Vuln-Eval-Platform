#!/bin/bash
# ==============================================================================
# 通用规则一键评测脚本 (CodeFuse-Query)
# 用法: ./scripts/evaluation/eval_checker.sh <CWE编号>
# 示例: ./scripts/evaluation/eval_checker.sh 078
#       ./scripts/evaluation/eval_checker.sh 022
# ==============================================================================
set -e

CWE_ID=$1
if [ -z "$CWE_ID" ]; then
    echo "❌ 错误: 缺少 CWE 编号参数。"
    echo "用法: $0 <CWE编号> (例如: 078, 022)"
    exit 1
fi

# 激活虚拟环境 (如果存在)
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
fi

RULE_FILE="rules/codefuse-query/CWE-${CWE_ID}/checker${CWE_ID}.gdl"
DB_DIR="dataset/codefuse-db"
RESULT_DIR="experiments/cwe-${CWE_ID}/results/codefuse-query"
EVAL_DIR="experiments/cwe-${CWE_ID}/eval/codefuse_eval"
JSON_FILE="${RESULT_DIR}/checker${CWE_ID}.json"
CSV_FILE="${RESULT_DIR}/cwe${CWE_ID}_codefuse.csv"

echo "============================================"
echo " CWE-${CWE_ID} 评测流水线"
echo "============================================"
echo ""

# Step 1: Run Sparrow query
echo "[1/3] 正在执行 CodeFuse-Query 规则检测..."
echo "  规则: ${RULE_FILE}"
mkdir -p "${RESULT_DIR}"
sparrow query run \
  -d "${DB_DIR}" \
  -gdl "${RULE_FILE}" \
  -o "${RESULT_DIR}"

if [ ! -f "${JSON_FILE}" ]; then
    echo "❌ 错误: 未生成 JSON 结果文件: ${JSON_FILE}"
    echo "  请检查规则文件是否有语法错误。"
    exit 1
fi
echo "  ✅ 检测完成，结果已输出: ${JSON_FILE}"
echo ""

# Step 2: Convert JSON -> CSV
echo "[2/3] 正在将 JSON 结果转换为 CSV 格式..."
python scripts/converters/codefuse_json_to_csv.py \
  "${JSON_FILE}" \
  "${CSV_FILE}" \
  --default-rule "CWE-${CWE_ID}" \
  --include-reason
echo ""

# Step 3: Evaluate against ground truth
echo "[3/3] 正在与 Ground Truth 对比计算评测指标..."
mkdir -p "${EVAL_DIR}"
python scripts/evaluation/eval_codefuse_results.py \
  --expected expectedresults-1.2.csv \
  --results "${CSV_FILE}" \
  --cwe "CWE-${CWE_ID}" \
  --outdir "${EVAL_DIR}" \
  --format csv \
  --fp-mode all_non_gt

echo ""
echo "============================================"
echo " ✅ CWE-${CWE_ID} 评测流水线执行完成！"
echo "============================================"
echo ""
echo "📊 评测指标: ${EVAL_DIR}/metrics.json"
echo "✅ 真正例:   ${EVAL_DIR}/tp.csv"
echo "⚠️  误报列表: ${EVAL_DIR}/fp.csv"
echo "❌ 漏报列表: ${EVAL_DIR}/fn.csv"
echo ""

if [ -f "${EVAL_DIR}/metrics.json" ]; then
    echo "--- 指标摘要 ---"
    cat "${EVAL_DIR}/metrics.json"
    echo ""
fi
