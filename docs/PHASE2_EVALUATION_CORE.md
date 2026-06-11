# VEP Phase 2: 统一评估核心

## 文档状态

**创建时间：** 2026-06-11  
**阶段：** Phase 2 - 统一评估核心  
**状态：** ✅ 完成

---

## Phase 2 范围

Phase 2 建立统一评估核心（Unified Evaluation Core），提供独立于现有脚本的 v2 评估路径。

**核心目标：**
- 统一 Finding / ExpectedCase / EvalResult 数据模型
- 统一评估逻辑（兼容 eval_codefuse_results.py）
- 提供独立 CLI 入口（`eval_findings.py`）
- 保持与旧流程并行，不替换现有脚本

**非目标（留待后续 Phase）：**
- ❌ 不重写 run_eval.sh
- ❌ 不修改 eval_checker.sh
- ❌ 不自动化 SARIF → CSV 转换
- ❌ 不重构报告系统
- ❌ 不实现 Tool 抽象层
- ❌ 不迁移旧 wrapper

---

## 新增文件说明

### 核心数据模型

```
vep/
├── __init__.py                   # VEP 包初始化
├── core/
│   ├── __init__.py
│   ├── models.py                 # Finding / ExpectedCase / EvalResult
│   └── normalization.py          # CWE / testcase 标准化函数
└── evaluation/
    ├── __init__.py
    ├── findings.py               # 加载 findings CSV
    ├── ground_truth.py           # 加载 ground truth CSV
    ├── evaluator.py              # 统一评估逻辑
    └── metrics.py                # metrics.json 输出
```

### CLI 入口

```
scripts/evaluation/
└── eval_findings.py              # 独立 v2 CLI 入口
```

### 文档

```
docs/
└── PHASE2_EVALUATION_CORE.md     # 本文档
```

---

## 统一 Evaluation Core 设计

### 数据模型

#### 1. Finding

表示单个漏洞检测结果（来自 normalized CSV）。

```python
@dataclass
class Finding:
    testcase: str                  # BenchmarkTest00001
    rule_id: str                   # CWE-022
    file: str                      # org/owasp/.../Test.java
    line: Optional[int]            # 行号
    tool: Optional[str]            # codefuse / codeql
    cwe: Optional[str]             # CWE 标识
    message: Optional[str]         # 检测原因
    raw: dict                      # 原始 CSV 所有字段
```

**设计考虑：**
- 支持 CodeFuse CSV（testcase, ruleId, file, line, reason）
- 支持 CodeQL CSV（testcase, ruleId, file, line）
- 灵活字段名匹配（testcase / className / name）
- raw 保留所有原始字段，便于扩展

#### 2. ExpectedCase

表示 ground truth 测试用例（来自 expectedresults-1.2.csv）。

```python
@dataclass
class ExpectedCase:
    testcase: str                  # BenchmarkTest00001
    cwe: str                       # CWE-022
    is_vulnerable: bool            # true / false
    category: Optional[str]        # pathtraver / sqli / xss
    raw: dict                      # 原始字段
```

**设计考虑：**
- 标准化 testcase 提取（BenchmarkTest 正则）
- 标准化 CWE ID（CWE-022 / 022 / cwe022 → CWE-022）
- 标准化 truth value（true/false/1/0/yes/no → bool）
- 处理 CWE-328S 特例（328S → CWE-328）

#### 3. EvalResult

表示评估结果（输出到 metrics.json）。

```python
@dataclass
class EvalResult:
    tool: str                      # codefuse / codeql
    cwe: str                       # CWE-022
    tp: int                        # True Positives
    fp: int                        # False Positives
    fn: int                        # False Negatives
    tn: Optional[int]              # True Negatives
    precision: float               # TP / (TP + FP)
    recall: float                  # TP / (TP + FN)
    f1: float                      # F1 score
    total_findings: int            # 原始 findings 数量
    total_expected_vulnerable: int # Ground truth vulnerable 数量
    total_expected_cases: Optional[int]
    schema_version: str            # "vep.eval.v2"
```

**设计考虑：**
- 兼容旧 metrics.json 核心字段（tp/fp/fn/precision/recall/f1）
- 新增 v2 字段（tool/tn/total_findings/schema_version）
- 4 位小数精度（与旧版本一致）

---

## Finding / ExpectedCase / EvalResult 模型说明

### Normalization 策略

#### CWE ID 标准化

```python
normalize_cwe_id(value: str) -> str
```

| 输入 | 输出 | 说明 |
|---|---|---|
| "CWE-022" | "CWE-022" | 保持标准格式 |
| "022" | "CWE-022" | 补全前缀 |
| "22" | "CWE-022" | 零填充 + 补全前缀 |
| "cwe022" | "CWE-022" | 大小写 + 格式标准化 |
| "CWE_022" | "CWE-022" | 下划线转连字符 |
| "328S" | "CWE-328S" | 保留 suffix |
| "CWE-328_328S" | "CWE-328" | 特例：移除 _328S 后缀 |

**特殊处理：**
- CWE-328_328S（CodeQL 目录名）→ CWE-328（标准化）
- Ground truth 中的 "328S" → CWE-328（匹配时兼容）

#### Testcase ID 标准化

```python
normalize_testcase_id(value: str) -> str
```

| 输入 | 输出 |
|---|---|
| "BenchmarkTest00001" | "BenchmarkTest00001" |
| "org/owasp/benchmark/BenchmarkTest00001.java" | "BenchmarkTest00001" |
| "/path/to/BenchmarkTest00001.java" | "BenchmarkTest00001" |

使用正则 `BenchmarkTest(\d+)` 提取。

#### Truth Value 标准化

```python
normalize_truth_value(value: str) -> Optional[bool]
```

| 输入 | 输出 |
|---|---|
| "true" / "1" / "yes" / "vulnerable" / "positive" | True |
| "false" / "0" / "no" / "safe" / "negative" | False |
| 其他 | None（跳过该行） |

---

## CLI 使用方式

### 基本用法

```bash
python scripts/evaluation/eval_findings.py \
  --findings experiments/cwe-022/results/codefuse-query/cwe022_codefuse.csv \
  --ground-truth expectedresults-1.2.csv \
  --tool codefuse \
  --cwe CWE-022 \
  --out experiments/cwe-022/eval/codefuse_eval_v2/metrics.json
```

### 带验证和详细输出

```bash
python scripts/evaluation/eval_findings.py \
  --findings experiments/cwe-022/results/codefuse-query/cwe022_codefuse.csv \
  --ground-truth expectedresults-1.2.csv \
  --tool codefuse \
  --cwe CWE-022 \
  --out experiments/cwe-022/eval/codefuse_eval_v2/metrics.json \
  --manifest configs/cwe_manifest.yml \
  --verbose
```

### 参数说明

| 参数 | 必需 | 说明 |
|---|---|---|
| `--findings` | ✅ | Normalized findings CSV 路径 |
| `--ground-truth` | ✅ | Ground truth CSV 路径 |
| `--tool` | ✅ | 工具名（codefuse / codeql） |
| `--cwe` | ✅ | 目标 CWE（CWE-022 / 022 / cwe-022） |
| `--out` | ✅ | 输出 metrics.json 路径 |
| `--manifest` | ❌ | CWE manifest 验证（可选） |
| `--no-tn` | ❌ | 不计算 TN |
| `--verbose` | ❌ | 详细输出 |

---

## 与旧 eval_codefuse_results.py 的兼容关系

### 核心指标完全一致

**验证结果（CWE-022）：**

| 指标 | 旧 evaluator | 新 evaluator (v2) | 状态 |
|---|---|---|---|
| TP | 120 | 120 | ✅ 一致 |
| FP | 108 | 108 | ✅ 一致 |
| FN | 13 | 13 | ✅ 一致 |
| Precision | 0.5263 | 0.5263 | ✅ 一致 |
| Recall | 0.9023 | 0.9023 | ✅ 一致 |
| F1 | 0.6648 | 0.6648 | ✅ 一致 |

### 匹配逻辑兼容性

**去重策略：** ✅ 一致
- 新旧均按 testcase 去重
- 旧：`testcase_to_record.setdefault(testcase, record)`（保留首个）
- 新：`if testcase not in testcase_to_finding`（保留首个）

**FP 模式：** ✅ 一致
- 新 evaluator 使用 `all_non_gt` 模式（默认）
- FP = detected - vulnerable（包含 in-scope 和 out-of-scope）
- 与旧 evaluator `--fp-mode all_non_gt` 一致

**CWE 过滤：** ✅ 一致
- 均在 ground truth 加载时过滤
- 均支持 CWE-328S 特例处理

### 字段差异

| 字段 | 旧 evaluator | 新 evaluator (v2) | 说明 |
|---|---|---|---|
| cwe | ✅ | ✅ | 都有 |
| tp/fp/fn | ✅ | ✅ | 都有 |
| precision/recall/f1 | ✅ | ✅ | 都有 |
| results_file | ✅ | ❌ | v2 不记录输入路径 |
| results_format | ✅ | ❌ | v2 不记录格式 |
| fp_mode | ✅ | ❌ | v2 固定 all_non_gt |
| raw_findings | ✅ | ✅ | v2 为 total_findings |
| dedup_findings | ✅ | ❌ | v2 不单独输出 |
| ground_truth_total | ✅ | ✅ | v2 为 total_expected_vulnerable |
| cwe_scope_total | ✅ | ✅ | v2 为 total_expected_cases |
| in_scope_findings | ✅ | ❌ | v2 不输出 |
| outside_scope_findings | ✅ | ❌ | v2 不输出 |
| outside_scope_ratio | ✅ | ❌ | v2 不输出 |
| fp_in_scope | ✅ | ❌ | v2 不细分 |
| fp_all_non_gt | ✅ | ❌ | v2 不细分 |
| fnr/fpr/fdr | ✅ | ❌ | v2 未实现（可在 Phase 2B 添加） |
| tool | ❌ | ✅ | v2 新增 |
| tn | ❌ | ✅ | v2 新增 |
| schema_version | ❌ | ✅ | v2 新增 |

### 详细输出差异

| 输出 | 旧 evaluator | 新 evaluator (v2) |
|---|---|---|
| metrics.json | ✅ | ✅ |
| tp.csv | ✅ | ❌ |
| fp.csv | ✅ | ❌ |
| fn.csv | ✅ | ❌ |
| outside_scope.csv | ✅ | ❌ |

**说明：**
- v2 当前只输出 metrics.json
- 详细 CSV 输出可在 Phase 2B 添加
- 不影响核心指标准确性

---

## 与旧 aggregate_results.py 的兼容关系

### 聚合逻辑差异

| 特性 | aggregate_results.py | eval_findings.py (v2) |
|---|---|---|
| **输入** | 扫描 experiments/* 自动发现 CSV | 手动指定 findings CSV |
| **FP 定义** | in_scope only | all_non_gt（更严格） |
| **去重** | 假设 CSV 已去重 | 显式去重 |
| **输出** | 多 CWE 聚合 JSON | 单 CWE metrics.json |
| **OVERALL** | 累加所有 CWE | 不支持 |

**兼容性：** ⚠️ 部分兼容
- v2 evaluator 可替代单 CWE 评估
- 聚合多 CWE 需要后续 Phase 实现
- FP 定义不同可能导致指标差异

---

## 已验证命令

### Phase 1 验证（仍然通过）

```bash
python scripts/verify_manifest.py
python scripts/validate_manifest.py
```

输出：✅ 验证通过：所有核心规则文件存在

### 编译检查

```bash
python -m compileall vep/ scripts/evaluation/eval_findings.py
```

输出：✅ 所有文件编译通过

### 端到端评估

```bash
python scripts/evaluation/eval_findings.py \
  --findings experiments/cwe-022/results/codefuse-query/cwe022_codefuse.csv \
  --ground-truth expectedresults-1.2.csv \
  --tool codefuse \
  --cwe CWE-022 \
  --out experiments/cwe-022/eval/codefuse_eval_v2/metrics.json \
  --manifest configs/cwe_manifest.yml \
  --verbose
```

**输出：**
```
Tool: codefuse
CWE: CWE-022
Total findings: 228
Ground truth vulnerable: 133

TP: 120
FP: 108
FN: 13
TN: 27

Precision: 0.5263
Recall: 0.9023
F1: 0.6648
```

**对比旧 evaluator：** ✅ 核心指标完全一致

---

## 当前差异

### 1. 输出字段差异

| 类别 | 说明 | 影响 |
|---|---|---|
| **旧有但 v2 无** | results_file, results_format, fp_mode, dedup_findings, in_scope_findings, outside_scope_findings, outside_scope_ratio, fp_in_scope, fp_all_non_gt, fnr, fpr, fdr | ⚠️ 需要这些字段的报告系统无法使用 v2 输出 |
| **v2 新增** | tool, tn, schema_version | ✅ 向前兼容，旧系统可忽略 |

### 2. 详细 CSV 输出缺失

- ❌ 无 tp.csv / fp.csv / fn.csv / outside_scope.csv
- **影响：** 无法查看详细 testcase 列表
- **解决方案：** Phase 2B 可添加（需要保留 testcase 到 finding 的映射）

### 3. FNR / FPR / FDR 缺失

- ❌ 未计算 False Negative Rate / False Positive Rate / False Discovery Rate
- **影响：** 少数评估场景需要这些指标
- **解决方案：** 计算简单，Phase 2B 可添加

### 4. 不支持多 CWE 聚合

- ❌ v2 evaluator 只处理单 CWE
- **影响：** 无法生成 OVERALL 统计
- **解决方案：** Phase 2C 实现聚合器

### 5. 不支持 in_scope FP 模式

- ❌ v2 固定使用 all_non_gt FP 模式
- **影响：** 与 aggregate_results.py 的 FP 定义不同
- **解决方案：** Phase 2B 添加 --fp-mode 参数

---

## Differences From Old Evaluator

### 设计哲学差异

| 方面 | 旧 evaluator | 新 evaluator (v2) |
|---|---|---|
| **职责** | 一站式（转换+评估+详细输出） | 纯评估（假设 CSV 已标准化） |
| **输入** | JSON / CSV / SARIF | 仅 CSV |
| **输出** | 5 个文件（metrics + 4 CSV） | 1 个文件（metrics.json） |
| **扩展性** | 单体脚本 | 模块化包 |

### 已知不兼容场景

1. **依赖详细 CSV 输出的工作流**
   - 旧流程：tp.csv / fp.csv / fn.csv 用于人工审查
   - v2：需要在 Phase 2B 添加

2. **依赖 outside_scope 分析的工作流**
   - 旧流程：outside_scope.csv + outside_scope_ratio
   - v2：未实现（可在 Phase 2B 添加）

3. **依赖 FPR / FNR / FDR 的研究**
   - 旧流程：输出 fnr / fpr / fdr
   - v2：未实现（可在 Phase 2B 添加）

---

## Remaining TODO

### Phase 2B: 增强 v2 Evaluator（可选）

- [ ] 添加详细 CSV 输出（tp.csv / fp.csv / fn.csv）
- [ ] 添加 outside_scope 分析
- [ ] 添加 FNR / FPR / FDR 计算
- [ ] 添加 --fp-mode 参数（in_scope / all_non_gt）
- [ ] 添加 dedup_findings 字段到输出

### Phase 2C: 自动化 SARIF → CSV 转换

- [ ] 集成 sarif_to_csv.py 到统一流程
- [ ] 实现 run_eval.sh 自动调用转换
- [ ] 验证 CodeQL 流程端到端

### Phase 2D: 报告系统双工具化

- [ ] 修改 generate_report.py 读取 v2 metrics
- [ ] 支持 CodeFuse + CodeQL 双工具报告
- [ ] 支持 v2 schema_version 自动识别

### Phase 3: 工具抽象层

- [ ] 实现 Tool Protocol
- [ ] 实现 CodeFuseTool / CodeQLTool
- [ ] 统一工具调用接口

### Phase 4: 测试体系

- [ ] 单元测试（normalizer / evaluator / loader）
- [ ] 集成测试（端到端 pipeline）
- [ ] Golden result 回归测试
- [ ] Smoke test

---

## Next Recommended Step

### 短期（Phase 2B）：增强 v2 Evaluator

**优先级：高**

1. 添加详细 CSV 输出
   - 实现 `write_detail_csv()` 函数
   - 输出 tp.csv / fp.csv / fn.csv
   - 保持字段格式与旧版兼容

2. 添加缺失指标
   - 计算 fnr / fpr / fdr
   - 计算 outside_scope_ratio
   - 添加到 metrics.json

3. 添加 FP 模式选项
   - 支持 --fp-mode in_scope / all_non_gt
   - 默认保持 all_non_gt

### 中期（Phase 2C）：自动化转换流程

**优先级：中**

1. SARIF → CSV 自动化
   - 集成 sarif_to_csv.py
   - 修改 run_eval.sh 自动调用

2. 验证 CodeQL 流程
   - 端到端测试 CodeQL 评估
   - 确保指标一致性

### 长期（Phase 3/4）：抽象与测试

**优先级：低**

1. 工具抽象层
   - 定义 Tool Protocol
   - 实现工具插件

2. 测试体系
   - 单元测试覆盖
   - 集成测试
   - 回归测试

---

## 总结

### Phase 2 成就

✅ **建立统一评估核心**
- 3 个核心数据模型（Finding / ExpectedCase / EvalResult）
- 5 个评估模块（normalization / findings / ground_truth / evaluator / metrics）
- 1 个独立 CLI 入口（eval_findings.py）

✅ **验证兼容性**
- 与 eval_codefuse_results.py 核心指标完全一致
- TP/FP/FN/Precision/Recall/F1 精确匹配

✅ **保持并行**
- 旧流程不受影响
- 新 v2 路径独立运行
- Phase 1 验证仍然通过

### Phase 2 限制

⚠️ **当前不支持：**
- 详细 CSV 输出（tp.csv / fp.csv / fn.csv）
- Outside-scope 分析
- FNR / FPR / FDR 指标
- In-scope FP 模式
- 多 CWE 聚合

**这些功能可在 Phase 2B 快速添加，不影响核心架构。**

---

**Phase 2 完成 ✅**  
**准备进入 Phase 2B：增强 v2 Evaluator（可选）**
