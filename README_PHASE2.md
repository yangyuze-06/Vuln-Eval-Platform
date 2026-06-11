# VEP Phase 2 - 3 分钟快速上手

## 一、验证安装

```bash
# 激活环境
source .venv/bin/activate

# 快速验证（推荐）
./scripts/quick_verify.sh
```

**预期输出：** ✅ Phase 2 验证完成

---

## 二、三种使用方式

### 方式 1: 评估 CodeFuse CSV

```bash
python scripts/evaluation/eval_findings.py \
  --findings experiments/cwe-022/results/codefuse-query/cwe022_codefuse.csv \
  --ground-truth expectedresults-1.2.csv \
  --tool codefuse \
  --cwe CWE-022 \
  --out experiments/cwe-022/eval/my_eval/metrics.json
```

**输出：** metrics.json + tp.csv + fp.csv + fn.csv + outside_scope.csv

### 方式 2: 评估 CodeQL SARIF

```bash
python scripts/evaluation/eval_sarif_findings.py \
  --sarif experiments/cwe-079/results/codeql/cwe079.sarif \
  --ground-truth expectedresults-1.2.csv \
  --tool codeql \
  --cwe CWE-079 \
  --out experiments/cwe-079/eval/my_eval/metrics.json
```

**输出：** findings.csv + metrics.json + detail CSVs

### 方式 3: 聚合多个 CWE

```bash
python scripts/evaluation/aggregate_v2.py \
  --metrics experiments/cwe-022/eval/my_eval/metrics.json \
            experiments/cwe-089/eval/my_eval/metrics.json \
  --out reports/data/my_aggregate.json
```

**输出：** aggregate.json（包含 overall 指标）

---

## 三、常用参数

| 参数 | 说明 | 默认值 |
|---|---|---|
| `--fp-mode` | FP 计算模式（all_non_gt / in_scope） | all_non_gt |
| `--no-details` | 不输出详细 CSV | false（会输出） |
| `--manifest` | CWE manifest 验证 | 无 |
| `--verbose` | 详细输出 | false |
| `--strict` | Strict 模式（聚合时验证一致性） | false |

---

## 四、查看结果

```bash
# 查看 metrics
cat experiments/cwe-022/eval/my_eval/metrics.json | python3 -m json.tool | head -30

# 查看 detail CSV
head -5 experiments/cwe-022/eval/my_eval/tp.csv
wc -l experiments/cwe-022/eval/my_eval/*.csv

# 查看 aggregate
cat reports/data/my_aggregate.json | python3 -c "
import sys, json
d = json.load(sys.stdin)
o = d['overall']
print(f\"Overall: TP={o['tp']}, FP={o['fp']}, FN={o['fn']}, P={o['precision']:.4f}, R={o['recall']:.4f}, F1={o['f1']:.4f}\")
"
```

---

## 五、验证正确性

```bash
# 对比新旧 evaluator（CWE-022）
echo "旧 evaluator:"
cat experiments/cwe-022/eval/codefuse_eval/metrics.json | python3 -c "import sys,json; m=json.load(sys.stdin); print(f\"TP={m['tp']}, FP={m['fp']}, FN={m['fn']}, P={m['precision']}, R={m['recall']}, F1={m['f1']}\")"

echo "v2 evaluator:"
python scripts/evaluation/eval_findings.py \
  --findings experiments/cwe-022/results/codefuse-query/cwe022_codefuse.csv \
  --ground-truth expectedresults-1.2.csv \
  --tool codefuse \
  --cwe CWE-022 \
  --out /tmp/v2_check.json \
  --no-details

cat /tmp/v2_check.json | python3 -c "import sys,json; m=json.load(sys.stdin); print(f\"TP={m['tp']}, FP={m['fp']}, FN={m['fn']}, P={m['precision']}, R={m['recall']}, F1={m['f1']}\")"
```

**预期：** 核心指标完全一致

---

## 六、常见问题

**Q: v2 会覆盖旧结果吗？**  
A: 不会。v2 输出在独立目录（例如 `my_eval/` 而非 `codefuse_eval/`）

**Q: 找不到 CSV/SARIF 怎么办？**  
A: 运行旧流程生成，或检查：
```bash
find experiments -name "*.csv" -o -name "*.sarif" | head -5
```

**Q: Overall 指标是平均值吗？**  
A: 不是！是按总 TP/FP/FN 计算：`Precision = sum(TP) / (sum(TP) + sum(FP))`

---

## 七、完整文档

- **快速开始：** `docs/QUICK_START_PHASE2.md`
- **Phase 2 总结：** `docs/PHASE2_FINAL_SUMMARY.md`
- **Phase 2A 核心：** `docs/PHASE2_EVALUATION_CORE.md`
- **Phase 2B 详细输出：** `docs/PHASE2B_EVALUATOR_DETAILS.md`

---

**开始使用 VEP Phase 2 ✅**
