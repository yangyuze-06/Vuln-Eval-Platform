# VEP Phase 2B: 增强 v2 Evaluator 输出能力

## 文档状态

**创建时间：** 2026-06-11  
**阶段：** Phase 2B - 增强 v2 Evaluator 输出能力  
**状态：** ✅ 完成

---

## Phase 2B 范围

Phase 2B 在 Phase 2A 基础上增强 v2 evaluator 的输出能力，使其更接近旧 eval_codefuse_results.py。

**核心目标：**
- ✅ 添加详细 CSV 输出（tp.csv / fp.csv / fn.csv / outside_scope.csv）
- ✅ 添加扩展指标（fnr / fpr / fdr / dedup_findings / in_scope_findings / outside_scope_findings / outside_scope_ratio / fp_in_scope / fp_all_non_gt）
- ✅ 添加 FP 模式选项（--fp-mode all_non_gt / in_scope）
- ✅ 保持旧流程零破坏

**非目标（留待后续 Phase）：**
- ❌ 不修改 run_eval.sh
- ❌ 不修改 eval_checker.sh  
- ❌ 不自动化 SARIF → CSV
- ❌ 不重构报告系统
- ❌ 不实现 Tool 抽象层

---

## 新增功能

### 1. 详细 CSV 输出

**输出文件：**
- `tp.csv` - True Positive 详细列表
- `fp.csv` - False Positive 详细列表
- `fn.csv` - False Negative 详细列表
- `outside_scope.csv` - Outside-scope finding 列表

**CSV 字段（兼容旧 evaluator）：**
```csv
testcase,testcaseId,sinkFile,line,ruleId,findingCount
```

**默认行为：**
- 默认输出详细 CSV 到 `--out` 的父目录
- 使用 `--details-dir` 可指定输出目录
- 使用 `--no-details` 可禁用详细 CSV 输出

### 2. FP 模式

**两种 FP 计算模式：**

#### Mode 1: all_non_gt（默认）

```
FP = detected - vulnerable
   = (detected ∩ non_vulnerable) + (detected - all_expected)
```

**语义：**
- 所有未命中 vulnerable case 的 findings 都算 FP
- 包括 in-scope negative cases
- 包括 out-of-scope cases

**兼容性：** 与旧 eval_codefuse_results.py `--fp-mode all_non_gt` 一致

#### Mode 2: in_scope

```
FP = detected ∩ non_vulnerable
```

**语义：**
- 只有当前 CWE scope 内的 non-vulnerable cases 算 FP
- out-of-scope findings 不计入 FP
- out-of-scope findings 仍记录到 outside_scope.csv

**兼容性：** 更接近 aggregate_results.py 的 FP 定义

### 3. 扩展指标

**新增 metrics.json 字段：**

| 字段 | 说明 |
|---|---|
| `fp_mode` | FP 计算模式 |
| `raw_findings` | 原始 finding 数量（去重前） |
| `dedup_findings` | 去重后的 finding 数量 |
| `ground_truth_total` | Ground truth 中 vulnerable cases 数量 |
| `cwe_scope_total` | 当前 CWE 的所有 expected cases 数量 |
| `in_scope_findings` | In-scope findings 数量 |
| `outside_scope_findings` | Out-of-scope findings 数量 |
| `outside_scope_ratio` | Out-of-scope 比例 |
| `fp_in_scope` | In-scope FP 数量 |
| `fp_all_non_gt` | All non-GT FP 数量 |
| `fnr` | False Negative Rate = FN / (TP + FN) |
| `fpr` | False Positive Rate = FP / (FP + TN) |
| `fdr` | False Discovery Rate = FP / (TP + FP) |

**字段别名（兼容性）：**
- `raw_findings` = `total_findings`
- `ground_truth_total` = `total_expected_vulnerable`
- `cwe_scope_total` = `total_expected_cases`

---

## CLI 使用方式

### 基本用法（默认 all_non_gt 模式）

```bash
python scripts/evaluation/eval_findings.py \
  --findings experiments/cwe-022/results/codefuse-query/cwe022_codefuse.csv \
  --ground-truth expectedresults-1.2.csv \
  --tool codefuse \
  --cwe CWE-022 \
  --out experiments/cwe-022/eval/codefuse_eval_v2b/metrics.json
```

**输出：**
- `metrics.json`
- `tp.csv`
- `fp.csv`
- `fn.csv`
- `outside_scope.csv`

### 使用 in_scope FP 模式

```bash
python scripts/evaluation/eval_findings.py \
  --findings experiments/cwe-022/results/codefuse-query/cwe022_codefuse.csv \
  --ground-truth expectedresults-1.2.csv \
  --tool codefuse \
  --cwe CWE-022 \
  --out experiments/cwe-022/eval/codefuse_eval_v2b_inscope/metrics.json \
  --fp-mode in_scope
```

### 禁用详细 CSV 输出

```bash
python scripts/evaluation/eval_findings.py \
  --findings experiments/cwe-022/results/codefuse-query/cwe022_codefuse.csv \
  --ground-truth expectedresults-1.2.csv \
  --tool codefuse \
  --cwe CWE-022 \
  --out /tmp/metrics_only.json \
  --no-details
```

**输出：** 只有 `metrics.json`

### 指定详细 CSV 输出目录

```bash
python scripts/evaluation/eval_findings.py \
  --findings experiments/cwe-022/results/codefuse-query/cwe022_codefuse.csv \
  --ground-truth expectedresults-1.2.csv \
  --tool codefuse \
  --cwe CWE-022 \
  --out /tmp/metrics.json \
  --details-dir experiments/cwe-022/eval/codefuse_eval_v2b
```

---

## 与旧 eval_codefuse_results.py 的兼容性

### 核心指标完全一致

**CWE-022 验证（all_non_gt 模式）：**

| 指标 | 旧 Evaluator | Phase 2B v2 | 状态 |
|---|---|---|---|
| raw_findings | 228 | 228 | ✅ 一致 |
| dedup_findings | 228 | 228 | ✅ 一致 |
| ground_truth_total | 133 | 133 | ✅ 一致 |
| cwe_scope_total | 268 | 268 | ✅ 一致 |
| in_scope_findings | 228 | 228 | ✅ 一致 |
| outside_scope_findings | 0 | 0 | ✅ 一致 |
| outside_scope_ratio | 0.0 | 0.0 | ✅ 一致 |
| **TP** | 120 | 120 | ✅ 一致 |
| **FP** | 108 | 108 | ✅ 一致 |
| fp_in_scope | 108 | 108 | ✅ 一致 |
| fp_all_non_gt | 108 | 108 | ✅ 一致 |
| **FN** | 13 | 13 | ✅ 一致 |
| **Precision** | 0.5263 | 0.5263 | ✅ 一致 |
| **Recall** | 0.9023 | 0.9023 | ✅ 一致 |
| **F1** | 0.6648 | 0.6648 | ✅ 一致 |

**CWE-089 验证（all_non_gt 模式）：**

| 指标 | 旧 Evaluator | Phase 2B v2 | 状态 |
|---|---|---|---|
| TP | 267 | 267 | ✅ 一致 |
| FP | 150 | 150 | ✅ 一致 |
| FN | 5 | 5 | ✅ 一致 |
| Precision | 0.6403 | 0.6403 | ✅ 一致 |
| Recall | 0.9816 | 0.9816 | ✅ 一致 |
| F1 | 0.775 | 0.7750 | ✅ 一致（格式差异） |

### 详细 CSV 输出兼容

**CSV 行数对比（CWE-022）：**

| 文件 | 旧 Evaluator | Phase 2B v2 | 状态 |
|---|---|---|---|
| tp.csv | 121 行 | 121 行 | ✅ 一致 |
| fp.csv | 109 行 | 109 行 | ✅ 一致 |
| fn.csv | 14 行 | 14 行 | ✅ 一致 |
| outside_scope.csv | 1 行 | 1 行 | ✅ 一致 |

**CSV 字段兼容：** ✅ 完全一致
- testcase, testcaseId, sinkFile, line, ruleId, findingCount

### Metrics 字段对比

| 字段 | 旧 Evaluator | Phase 2B v2 | 说明 |
|---|---|---|---|
| cwe | ✅ | ✅ | 都有 |
| tool | ❌ | ✅ | v2 新增 |
| fp_mode | ✅ | ✅ | 都有 |
| raw_findings | ✅ | ✅ | 都有 |
| dedup_findings | ✅ | ✅ | 都有 |
| ground_truth_total | ✅ | ✅ | 都有 |
| cwe_scope_total | ✅ | ✅ | 都有 |
| in_scope_findings | ✅ | ✅ | 都有 |
| outside_scope_findings | ✅ | ✅ | 都有 |
| outside_scope_ratio | ✅ | ✅ | 都有 |
| tp / fp / fn | ✅ | ✅ | 都有 |
| fp_in_scope | ✅ | ✅ | 都有 |
| fp_all_non_gt | ✅ | ✅ | 都有 |
| precision / recall / f1 | ✅ | ✅ | 都有 |
| fnr / fpr / fdr | ❌ | ✅ | v2 新增 |
| tn | ❌ | ✅ | v2 新增 |
| results_file | ✅ | ❌ | v2 未实现 |
| results_format | ✅ | ❌ | v2 未实现 |
| schema_version | ❌ | ✅ | v2 新增 |

### 缺失字段

**v2 未实现（非必需）：**
- `results_file` - 输入文件路径（记录类字段，不影响评估）
- `results_format` - 输入格式（固定 CSV，不需要）

这些字段对评估逻辑无影响，可在需要时添加。

---

## FP Mode 语义对比

### all_non_gt Mode

**定义：** FP = detected - vulnerable

**CWE-022 示例：**
```
detected = 228
vulnerable = 133
non-vulnerable (in-scope) = 135
outside-scope = 0

FP = 228 - 133 = 108
  = (detected ∩ non-vulnerable) + (detected - all_expected)
  = 108 + 0
  = 108
```

**特点：**
- 更严格的 FP 定义
- out-of-scope findings 算 FP
- 与旧 eval_codefuse_results.py 默认行为一致

### in_scope Mode

**定义：** FP = detected ∩ non-vulnerable

**CWE-022 示例（假设有 out-of-scope）：**
```
detected = 230
vulnerable = 133
non-vulnerable (in-scope) = 135
outside-scope = 2

FP (in_scope) = detected ∩ non-vulnerable = 108
FP (all_non_gt) = 230 - 133 = 110

Precision (in_scope) = 120 / (120 + 108) = 0.5263
Precision (all_non_gt) = 120 / (120 + 110) = 0.5217
```

**特点：**
- 更宽松的 FP 定义
- out-of-scope findings 不算 FP
- 更接近 aggregate_results.py 的行为

---

## Metrics Schema 变更

### Phase 2A Schema

```json
{
  "tool": "codefuse",
  "cwe": "CWE-022",
  "tp": 120,
  "fp": 108,
  "fn": 13,
  "tn": 27,
  "precision": 0.5263,
  "recall": 0.9023,
  "f1": 0.6648,
  "total_findings": 228,
  "total_expected_vulnerable": 133,
  "total_expected_cases": 268,
  "schema_version": "vep.eval.v2"
}
```

### Phase 2B Schema

```json
{
  "cwe": "CWE-022",
  "tool": "codefuse",
  "fp_mode": "all_non_gt",
  "raw_findings": 228,
  "total_findings": 228,
  "dedup_findings": 228,
  "ground_truth_total": 133,
  "total_expected_vulnerable": 133,
  "in_scope_findings": 228,
  "outside_scope_findings": 0,
  "outside_scope_ratio": 0.0,
  "tp": 120,
  "fp": 108,
  "fp_in_scope": 108,
  "fp_all_non_gt": 108,
  "fn": 13,
  "precision": 0.5263,
  "recall": 0.9023,
  "fnr": 0.0977,
  "fpr": 0.8,
  "fdr": 0.4737,
  "f1": 0.6648,
  "schema_version": "vep.eval.v2",
  "tn": 27,
  "cwe_scope_total": 268,
  "total_expected_cases": 268
}
```

**变更摘要：**
- ✅ 新增 10+ 扩展字段
- ✅ 保留所有 Phase 2A 字段
- ✅ 添加字段别名（raw_findings, ground_truth_total, cwe_scope_total）
- ✅ 向后兼容

---

## 已验证命令

### 1. Phase 1 验证

```bash
python scripts/verify_manifest.py
python scripts/validate_manifest.py
```

**结果：** ✅ 通过

### 2. 编译检查

```bash
python -m compileall vep/ scripts/evaluation/eval_findings.py
```

**结果：** ✅ 通过

### 3. CWE-022 all_non_gt 模式

```bash
python scripts/evaluation/eval_findings.py \
  --findings experiments/cwe-022/results/codefuse-query/cwe022_codefuse.csv \
  --ground-truth expectedresults-1.2.csv \
  --tool codefuse \
  --cwe CWE-022 \
  --out experiments/cwe-022/eval/codefuse_eval_v2b/metrics.json \
  --fp-mode all_non_gt \
  --verbose
```

**结果：** ✅ 核心指标与旧 evaluator 完全一致

### 4. CWE-022 in_scope 模式

```bash
python scripts/evaluation/eval_findings.py \
  --findings experiments/cwe-022/results/codefuse-query/cwe022_codefuse.csv \
  --ground-truth expectedresults-1.2.csv \
  --tool codefuse \
  --cwe CWE-022 \
  --out experiments/cwe-022/eval/codefuse_eval_v2b_inscope/metrics.json \
  --fp-mode in_scope
```

**结果：** ✅ in_scope 模式正常运行

### 5. CWE-089 all_non_gt 模式

```bash
python scripts/evaluation/eval_findings.py \
  --findings experiments/cwe-089/results/codefuse-query/cwe089_codefuse.csv \
  --ground-truth expectedresults-1.2.csv \
  --tool codefuse \
  --cwe CWE-089 \
  --out experiments/cwe-089/eval/codefuse_eval_v2b/metrics.json \
  --fp-mode all_non_gt
```

**结果：** ✅ 核心指标与旧 evaluator 完全一致

### 6. --no-details 选项

```bash
python scripts/evaluation/eval_findings.py \
  --findings experiments/cwe-022/results/codefuse-query/cwe022_codefuse.csv \
  --ground-truth expectedresults-1.2.csv \
  --tool codefuse \
  --cwe CWE-022 \
  --out /tmp/metrics_only.json \
  --no-details
```

**结果：** ✅ 只输出 metrics.json，无详细 CSV

---

## Remaining TODO

### Phase 2C: SARIF 自动化（下一步）

**优先级：中**
- [ ] 集成 sarif_to_csv.py 到统一流程
- [ ] 修改 run_eval.sh 自动调用 SARIF 转换
- [ ] 验证 CodeQL 端到端流程

### Phase 2D: 报告系统双工具化

**优先级：中**
- [ ] 修改 generate_report.py 读取 v2 metrics
- [ ] 支持 CodeFuse + CodeQL 双工具报告
- [ ] 支持 schema_version 自动识别

### Phase 3: 工具抽象层（未来）

**优先级：低**
- [ ] 定义 Tool Protocol
- [ ] 实现 CodeFuseTool / CodeQLTool
- [ ] 统一工具调用接口

### Phase 4: 测试体系（未来）

**优先级：低**
- [ ] 单元测试（normalization / evaluator / loader）
- [ ] 集成测试（端到端 pipeline）
- [ ] Golden result 回归测试

---

## 总结

### Phase 2B 成就

✅ **增强详细输出能力**
- 4 个详细 CSV 输出（tp / fp / fn / outside_scope）
- CSV 字段与旧 evaluator 完全兼容
- CSV 行数与旧 evaluator 完全一致

✅ **添加 FP 模式支持**
- all_non_gt 模式（默认，与旧 evaluator 一致）
- in_scope 模式（与 aggregate_results.py 兼容）

✅ **扩展 Metrics 字段**
- 新增 10+ 扩展字段
- 完整覆盖旧 evaluator 核心字段
- 新增 fnr / fpr / fdr 指标

✅ **验证兼容性**
- CWE-022: 核心指标完全一致
- CWE-089: 核心指标完全一致
- CSV 行数完全一致
- 旧流程零破坏

### Phase 2B 限制

⚠️ **当前未实现（非必需）：**
- results_file 字段（记录类字段）
- results_format 字段（固定 CSV）

这些字段对评估逻辑无影响，可在需要时快速添加。

---

**Phase 2B 完成 ✅**  
**准备进入 Phase 2C：SARIF 自动化（可选）**
