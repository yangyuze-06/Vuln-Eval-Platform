# VEP Phase 2 使用和验证指南

## 快速开始

### 前提条件

```bash
# 1. 激活虚拟环境
source .venv/bin/activate

# 2. 验证 Phase 1 基础设施
python scripts/verify_manifest.py
python scripts/validate_manifest.py

# 3. 验证 Phase 2 编译
python -m compileall vep/ scripts/evaluation/
```

---

## 使用场景 1: 评估 CodeFuse 规则（CSV 已存在）

### 单个 CWE 评估

```bash
# 评估 CWE-022
python scripts/evaluation/eval_findings.py \
  --findings experiments/cwe-022/results/codefuse-query/cwe022_codefuse.csv \
  --ground-truth expectedresults-1.2.csv \
  --tool codefuse \
  --cwe CWE-022 \
  --out experiments/cwe-022/eval/codefuse_eval_v2/metrics.json \
  --manifest configs/cwe_manifest.yml \
  --verbose

# 查看结果
cat experiments/cwe-022/eval/codefuse_eval_v2/metrics.json | python3 -m json.tool | head -30
ls experiments/cwe-022/eval/codefuse_eval_v2/
```

**预期输出：**
- `metrics.json` - 核心指标
- `tp.csv` - True Positives 详细列表
- `fp.csv` - False Positives 详细列表
- `fn.csv` - False Negatives 详细列表
- `outside_scope.csv` - Outside-scope findings

### 测试不同 FP 模式

```bash
# all_non_gt 模式（默认，更严格）
python scripts/evaluation/eval_findings.py \
  --findings experiments/cwe-022/results/codefuse-query/cwe022_codefuse.csv \
  --ground-truth expectedresults-1.2.csv \
  --tool codefuse \
  --cwe CWE-022 \
  --out /tmp/vep_all_non_gt.json \
  --fp-mode all_non_gt

# in_scope 模式（更宽松）
python scripts/evaluation/eval_findings.py \
  --findings experiments/cwe-022/results/codefuse-query/cwe022_codefuse.csv \
  --ground-truth expectedresults-1.2.csv \
  --tool codefuse \
  --cwe CWE-022 \
  --out /tmp/vep_in_scope.json \
  --fp-mode in_scope

# 对比 FP 指标
echo "all_non_gt FP:"
cat /tmp/vep_all_non_gt.json | python3 -c "import sys,json; m=json.load(sys.stdin); print(f\"FP={m['fp']}, fp_in_scope={m['fp_in_scope']}, fp_all_non_gt={m['fp_all_non_gt']}\")"

echo "in_scope FP:"
cat /tmp/vep_in_scope.json | python3 -c "import sys,json; m=json.load(sys.stdin); print(f\"FP={m['fp']}, fp_in_scope={m['fp_in_scope']}, fp_all_non_gt={m['fp_all_non_gt']}\")"
```

### 禁用详细 CSV（只输出 metrics.json）

```bash
python scripts/evaluation/eval_findings.py \
  --findings experiments/cwe-022/results/codefuse-query/cwe022_codefuse.csv \
  --ground-truth expectedresults-1.2.csv \
  --tool codefuse \
  --cwe CWE-022 \
  --out /tmp/vep_metrics_only.json \
  --no-details
```

---

## 使用场景 2: 评估 CodeQL 规则（SARIF 已存在）

### 单个 CWE 评估

```bash
# 评估 CWE-079
python scripts/evaluation/eval_sarif_findings.py \
  --sarif experiments/cwe-079/results/codeql/cwe079.sarif \
  --ground-truth expectedresults-1.2.csv \
  --tool codeql \
  --cwe CWE-079 \
  --out experiments/cwe-079/eval/codeql_eval_v2/metrics.json \
  --manifest configs/cwe_manifest.yml \
  --verbose

# 查看结果
cat experiments/cwe-079/eval/codeql_eval_v2/metrics.json | python3 -m json.tool | head -30
head -5 experiments/cwe-079/eval/codeql_eval_v2/findings.csv
ls experiments/cwe-079/eval/codeql_eval_v2/
```

**预期输出：**
- `findings.csv` - SARIF 转换后的 normalized CSV
- `metrics.json` - 核心指标
- `tp.csv / fp.csv / fn.csv / outside_scope.csv` - 详细列表

### 自定义 CSV 输出路径

```bash
python scripts/evaluation/eval_sarif_findings.py \
  --sarif experiments/cwe-079/results/codeql/cwe079.sarif \
  --ground-truth expectedresults-1.2.csv \
  --tool codeql \
  --cwe CWE-079 \
  --out /tmp/codeql_metrics.json \
  --csv-out /tmp/codeql_findings.csv
```

---

## 使用场景 3: 聚合多个 CWE 结果

### 显式指定 metrics 文件

```bash
# 聚合 CWE-022 和 CWE-089
python scripts/evaluation/aggregate_v2.py \
  --metrics experiments/cwe-022/eval/codefuse_eval_v2b/metrics.json \
            experiments/cwe-089/eval/codefuse_eval_v2b/metrics.json \
  --out reports/data/metrics_v2_codefuse_subset.json \
  --verbose

# 查看 overall 指标
cat reports/data/metrics_v2_codefuse_subset.json | python3 -c "
import sys, json
data = json.load(sys.stdin)
print('Aggregate Summary:')
print(f\"  Tool: {data['tool']}")
print(f\"  FP mode: {data['fp_mode']}")
print(f\"  Included: {data['included_count']} CWEs\")
print(f\"  Overall TP: {data['overall']['tp']}\")
print(f\"  Overall FP: {data['overall']['fp']}\")
print(f\"  Overall FN: {data['overall']['fn']}\")
print(f\"  Overall Precision: {data['overall']['precision']:.4f}\")
print(f\"  Overall Recall: {data['overall']['recall']:.4f}\")
print(f\"  Overall F1: {data['overall']['f1']:.4f}\")
"
```

### 自动发现（从 eval-root）

```bash
# 自动发现所有 codefuse_eval_v2b 目录下的 metrics
python scripts/evaluation/aggregate_v2.py \
  --eval-root experiments \
  --tool codefuse \
  --eval-dir-name codefuse_eval_v2b \
  --out reports/data/metrics_v2_codefuse_all.json \
  --manifest configs/cwe_manifest.yml \
  --verbose
```

### Strict 模式（验证一致性）

```bash
# Strict 模式：要求所有 manifest 中的 CWE 都有 metrics
# 如果缺失任何 CWE，会失败并报错
python scripts/evaluation/aggregate_v2.py \
  --eval-root experiments \
  --tool codefuse \
  --eval-dir-name codefuse_eval_v2b \
  --out reports/data/metrics_v2_codefuse_strict.json \
  --manifest configs/cwe_manifest.yml \
  --strict
```

---

## 验证指南

### 验证 1: 对比新旧 evaluator（CWE-022）

```bash
# 运行 v2 evaluator
python scripts/evaluation/eval_findings.py \
  --findings experiments/cwe-022/results/codefuse-query/cwe022_codefuse.csv \
  --ground-truth expectedresults-1.2.csv \
  --tool codefuse \
  --cwe CWE-022 \
  --out /tmp/v2_metrics.json \
  --no-details

# 对比核心指标
echo "=== 新旧 Evaluator 对比 ==="
echo "旧 evaluator:"
cat experiments/cwe-022/eval/codefuse_eval/metrics.json | python3 -c "
import sys, json
m = json.load(sys.stdin)
print(f\"  TP={m['tp']}, FP={m['fp']}, FN={m['fn']}\")
print(f\"  Precision={m['precision']}, Recall={m['recall']}, F1={m['f1']}\")
"

echo "v2 evaluator:"
cat /tmp/v2_metrics.json | python3 -c "
import sys, json
m = json.load(sys.stdin)
print(f\"  TP={m['tp']}, FP={m['fp']}, FN={m['fn']}\")
print(f\"  Precision={m['precision']}, Recall={m['recall']}, F1={m['f1']}\")
"
```

**预期结果：** 核心指标完全一致

### 验证 2: 检查 Detail CSV 行数

```bash
echo "=== Detail CSV 行数对比 ==="
echo "旧 evaluator:"
wc -l experiments/cwe-022/eval/codefuse_eval/*.csv

echo "v2 evaluator:"
python scripts/evaluation/eval_findings.py \
  --findings experiments/cwe-022/results/codefuse-query/cwe022_codefuse.csv \
  --ground-truth expectedresults-1.2.csv \
  --tool codefuse \
  --cwe CWE-022 \
  --out /tmp/v2_check/metrics.json \
  --details-dir /tmp/v2_check

wc -l /tmp/v2_check/*.csv
```

**预期结果：** CSV 行数完全一致

### 验证 3: Aggregate 计算正确性

```bash
# 手动计算预期结果
python3 -c "
# CWE-022: TP=120, FP=108, FN=13
# CWE-089: TP=267, FP=150, FN=5
tp = 120 + 267
fp = 108 + 150
fn = 13 + 5
precision = tp / (tp + fp)
recall = tp / (tp + fn)
f1 = 2 * precision * recall / (precision + recall)

print('预期 Overall 指标:')
print(f'  TP: {tp}')
print(f'  FP: {fp}')
print(f'  FN: {fn}')
print(f'  Precision: {precision:.4f}')
print(f'  Recall: {recall:.4f}')
print(f'  F1: {f1:.4f}')
"

# 运行 aggregate
python scripts/evaluation/aggregate_v2.py \
  --metrics experiments/cwe-022/eval/codefuse_eval_v2b/metrics.json \
            experiments/cwe-089/eval/codefuse_eval_v2b/metrics.json \
  --out /tmp/aggregate_check.json

# 查看实际结果
cat /tmp/aggregate_check.json | python3 -c "
import sys, json
data = json.load(sys.stdin)
o = data['overall']
print('\n实际 Overall 指标:')
print(f\"  TP: {o['tp']}\")
print(f\"  FP: {o['fp']}\")
print(f\"  FN: {o['fn']}\")
print(f\"  Precision: {o['precision']:.4f}\")
print(f\"  Recall: {o['recall']:.4f}\")
print(f\"  F1: {o['f1']:.4f}\")
"
```

**预期结果：** 预期值与实际值完全一致

---

## 快速验证脚本

将以下内容保存为 `scripts/quick_verify.sh`：

```bash
#!/bin/bash
set -e

echo "=============================="
echo "VEP Phase 2 快速验证"
echo "=============================="

# 激活虚拟环境
source .venv/bin/activate

# Phase 1 验证
echo "\n[1/5] Phase 1 验证..."
python scripts/verify_manifest.py | tail -3

# 编译检查
echo "\n[2/5] 编译检查..."
python -m compileall vep/ scripts/evaluation/ 2>&1 | grep -E "(Compiling|Error)" | tail -5 || echo "✅ 编译通过"

# CodeFuse 评估
echo "\n[3/5] CodeFuse 评估 (CWE-022)..."
python scripts/evaluation/eval_findings.py \
  --findings experiments/cwe-022/results/codefuse-query/cwe022_codefuse.csv \
  --ground-truth expectedresults-1.2.csv \
  --tool codefuse \
  --cwe CWE-022 \
  --out /tmp/vep_verify_metrics.json \
  --no-details 2>&1 | grep -E "(TP|FP|FN|Precision|Recall|F1)" | head -8

# CodeQL 评估
echo "\n[4/5] CodeQL 评估 (CWE-079)..."
python scripts/evaluation/eval_sarif_findings.py \
  --sarif experiments/cwe-079/results/codeql/cwe079.sarif \
  --ground-truth expectedresults-1.2.csv \
  --tool codeql \
  --cwe CWE-079 \
  --out /tmp/vep_verify_codeql.json \
  --no-details 2>&1 | grep -E "(TP|FP|FN|Precision|Recall|F1)" | head -8

# 聚合
echo "\n[5/5] 聚合验证..."
python scripts/evaluation/aggregate_v2.py \
  --metrics experiments/cwe-022/eval/codefuse_eval_v2b/metrics.json \
            experiments/cwe-089/eval/codefuse_eval_v2b/metrics.json \
  --out /tmp/vep_verify_aggregate.json 2>&1 | grep -E "(TP|FP|FN|Precision|Recall|F1)" | head -8

echo "\n=============================="
echo "✅ Phase 2 验证完成"
echo "=============================="
```

运行：

```bash
chmod +x scripts/quick_verify.sh
./scripts/quick_verify.sh
```

---

## 常见问题

### Q1: 找不到 normalized CSV 怎么办？

**A:** 检查是否存在：

```bash
find experiments -name "*_codefuse.csv" -o -name "*_codeql.csv" | head -5
```

如果不存在，需要先运行旧流程生成 CSV。

### Q2: SARIF 文件在哪里？

**A:** 查找现有 SARIF：

```bash
find experiments -name "*.sarif" | head -5
```

如果不存在，需要先运行 CodeQL database analyze。

### Q3: 如何验证新旧 evaluator 指标一致？

**A:** 使用验证 1 脚本（见上文"验证 1"）。

### Q4: Aggregate 计算的 Overall 是平均值吗？

**A:** 不是！是按总 TP/FP/FN 计算：

```
Overall Precision = sum(TP) / (sum(TP) + sum(FP))
NOT: mean([cwe.precision for cwe in cwes])
```

### Q5: v2 会覆盖旧结果吗？

**A:** 不会！v2 输出在独立目录：

```
旧: experiments/cwe-022/eval/codefuse_eval/
v2: experiments/cwe-022/eval/codefuse_eval_v2/
```

---

## 下一步

1. **评估你的规则：** 使用 `eval_findings.py` 或 `eval_sarif_findings.py`
2. **聚合多个 CWE：** 使用 `aggregate_v2.py`
3. **对比新旧指标：** 确保 v2 与旧 evaluator 一致
4. **阅读完整文档：** `docs/PHASE2_FINAL_SUMMARY.md`

---

**VEP Phase 2 使用指南完成 ✅**
