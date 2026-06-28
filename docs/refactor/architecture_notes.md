# VEP Architecture Analysis & Roadmap

## 文档状态

**创建时间：** 2026-06-11  
**阶段：** Phase 1 - 架构索引与诊断  
**变更影响：** 无（纯文档，不改变现有行为）

---

## 1. 当前架构总结

VEP 是一个**静态分析规则评测平台**，用于评估 CodeQL / CodeFuse Query 对 Java 安全漏洞（CWE）的检测能力。

### 核心功能

1. 管理 11 个 CWE 的检测规则（CodeQL `.ql` 和 CodeFuse `.gdl`）
2. 在 OWASP Benchmark 上执行规则检测
3. 规范化检测结果（SARIF → CSV / JSON → CSV）
4. 与 Ground Truth 对比计算 TP/FP/FN/Precision/Recall/F1
5. 生成评测指标、可视化图表、双语报告

### 当前目录结构

```
Vuln-Eval-Platform/
├── rules/
│   ├── codefuse-query/
│   │   ├── CWE-022/ ... CWE-643/    # 命名：CWE-{ID}
│   │   └── lib/security/java/        # 公共库
│   └── codeql-query/
│       └── CWE-022/ ... CWE-643/     # 命名：CWE-{ID}
│
├── tests/
│   └── codefuse-query/java/
│       └── cwe022/ ... cwe643/       # 命名：cwe{id} (小写，无连字符)
│
├── experiments/
│   └── cwe-022/ ... cwe-643/         # 命名：cwe-{id} (小写，有连字符)
│       ├── results/{tool}/*.{json|sarif|csv}
│       └── eval/{tool}_eval/metrics.json
│
├── scripts/
│   ├── converters/
│   │   ├── codefuse_json_to_csv.py
│   │   └── sarif_to_csv.py
│   ├── evaluation/
│   │   ├── eval_checker.sh          # CodeFuse 一键评测入口
│   │   ├── eval_codefuse_results.py
│   │   └── aggregate_results.py     # CodeQL 聚合入口
│   └── reporting/
│       ├── plots_metrics.py
│       └── generate_report.py
│
├── run_eval.sh                       # CodeQL 评测总入口
└── expectedresults-1.2.csv           # Ground Truth
```

---

## 2. 当前 CodeFuse 评测流程

### 入口命令

```bash
bash scripts/evaluation/eval_checker.sh 022
```

### Pipeline 详解

```
[1] CodeFuse-Query 规则执行
    godel -p <merged_lib> -f dataset/codefuse-db \
          -r rules/codefuse-query/CWE-022/checker022.gdl \
          --output-json experiments/cwe-022/results/codefuse-query/checker022.json

[2] JSON → CSV 转换
    python scripts/converters/codefuse_json_to_csv.py \
           experiments/cwe-022/results/codefuse-query/checker022.json \
           experiments/cwe-022/results/codefuse-query/cwe022_codefuse.csv

[3] Ground Truth 对比评估
    python scripts/evaluation/eval_codefuse_results.py \
           --expected expectedresults-1.2.csv \
           --results experiments/cwe-022/results/codefuse-query/cwe022_codefuse.csv \
           --cwe CWE-022 \
           --outdir experiments/cwe-022/eval/codefuse_eval

[输出]
    experiments/cwe-022/eval/codefuse_eval/
    ├── metrics.json
    ├── tp.csv
    ├── fp.csv
    ├── fn.csv
    └── outside_scope.csv
```

### 关键依赖

- `CODEFUSE_HOME` 环境变量（指向 sparrow-cli 目录）
- `GODEL_BIN` 默认为 `${CODEFUSE_HOME}/godel-script/usr/bin/godel`
- `OFFICIAL_LIB` 默认为 `${CODEFUSE_HOME}/lib/`
- `LOCAL_LIB` 默认为 `rules/codefuse-query/lib/`
- 临时合并 lib 目录到 `mktemp -d`（hack）

### 硬编码路径模式

- 规则：`rules/codefuse-query/CWE-{CWE_ID}/checker{CWE_ID}.gdl`
- 结果：`experiments/cwe-{CWE_ID}/results/codefuse-query/checker{CWE_ID}.json`
- CSV：`experiments/cwe-{CWE_ID}/results/codefuse-query/cwe{CWE_ID}_codefuse.csv`
- 评估：`experiments/cwe-{CWE_ID}/eval/codefuse_eval/metrics.json`

---

## 3. 当前 CodeQL 评测流程

### 入口命令

```bash
./run_eval.sh
```

### Pipeline 详解

```
[前置] 手动执行 CodeQL 分析
    # 用户需手动运行 codeql database analyze 并生成 SARIF
    # 放置到 experiments/cwe-{id}/results/codeql/*.sarif

[0] SARIF 完整性检查
    for dir in experiments/*/; do
        find "$dir/results" -name "*.sarif"
    done

[1] 聚合指标（从 CSV）
    python scripts/evaluation/aggregate_results.py
    # → reports/data/metrics.json

[2] 绘制图表
    python scripts/reporting/plots_metrics.py
    # → reports/figs/*.png

[3] 生成双语报告
    python scripts/reporting/generate_report.py
    # → reports/report.md, reports/report_zh.md
```

### 关键问题

❌ **SARIF → CSV 转换未自动化**
- `scripts/converters/sarif_to_csv.py` 存在但未被调用
- `aggregate_results.py` 直接读取 CSV，假设 CSV 已存在
- 用户需手动转换或依赖历史 CSV

❌ **评估逻辑与 CodeFuse 不一致**
- CodeFuse：使用 `eval_codefuse_results.py`（功能强大，支持多种 FP 模式）
- CodeQL：使用 `aggregate_results.py`（简化版，直接计算 TP/FP/FN）

❌ **报告生成只支持 CodeQL**
- `generate_report.py` 硬编码读取 `metrics["OVERALL"]["tools"]["codeql"]`
- 无法为 CodeFuse 生成报告

---

## 4. CWE 命名分裂问题

当前仓库存在 **4 种 CWE 命名约定**，导致路径映射复杂：

| 位置 | 命名格式 | 示例 |
|---|---|---|
| `rules/codefuse-query/` | `CWE-{ID}` | `CWE-022` |
| `rules/codeql-query/` | `CWE-{ID}` | `CWE-022` |
| `tests/codefuse-query/java/` | `cwe{id}` | `cwe022` |
| `experiments/` | `cwe-{id}` | `cwe-022` |
| `eval_checker.sh` 参数 | `{id}` | `022` |

### 特殊情况

- **CWE-328：** CodeQL 有 `CWE-328_328S`，CodeFuse 只有 `CWE-328`
- **文件命名：** `checker022.gdl` vs `checker{CWE_ID}.gdl` 依赖变量替换

### 映射复杂度

新增 1 个 CWE 需要：
1. 创建 `rules/codefuse-query/CWE-{ID}/checker{ID}.gdl`
2. 创建 `tests/codefuse-query/java/cwe{id}/`（可选）
3. 创建 `experiments/cwe-{id}/` 目录结构
4. 手动运行评测脚本
5. 无需修改代码（路径模式已覆盖）

---

## 5. 硬编码问题清单

### 5.1 路径硬编码

| 脚本 | 硬编码内容 |
|---|---|
| `eval_checker.sh` | `rules/codefuse-query/CWE-${CWE_ID}/checker${CWE_ID}.gdl` |
| `eval_checker.sh` | `dataset/codefuse-db` |
| `eval_checker.sh` | `experiments/cwe-${CWE_ID}/results/codefuse-query/` |
| `aggregate_results.py` | `expectedresults-1.2.csv` |
| `aggregate_results.py` | `experiments/` |
| `aggregate_results.py` | `reports/data/metrics.json` |
| `generate_report.py` | `reports/data/metrics.json` |
| `generate_report.py` | `reports/report.md` |

### 5.2 工具路径硬编码

| 脚本 | 工具 | 配置方式 |
|---|---|---|
| `eval_checker.sh` | godel | `CODEFUSE_HOME` 环境变量 + 多级回退 |
| `run_eval.sh` | venv | 硬编码检查 `venv/bin/activate` |

### 5.3 CSV Schema 隐式约定

| 文件类型 | 必需列 | 使用脚本 |
|---|---|---|
| 工具输出 CSV | `testcase, ruleId, file, line` | `aggregate_results.py`, `eval_codefuse_results.py` |
| Ground Truth | `testcase, category, real vulnerability, cwe` | `eval_codefuse_results.py` |

### 5.4 Metrics Schema 隐式约定

`metrics.json` 结构（由 `eval_codefuse_results.py` 输出）：

```json
{
  "cwe": "CWE-022",
  "results_format": "csv",
  "fp_mode": "all_non_gt",
  "raw_findings": 228,
  "dedup_findings": 228,
  "tp": 120,
  "fp": 108,
  "fn": 13,
  "precision": 0.5263,
  "recall": 0.9023,
  "f1": 0.6648
}
```

---

## 6. 结果流问题

### 当前数据流

```
[CodeFuse]
  GDL → JSON → CSV → eval_codefuse_results.py → metrics.json (per-CWE)
                                                  ↓
                                             (无聚合)

[CodeQL]
  QL → SARIF → (手动转 CSV) → aggregate_results.py → metrics.json (all-CWE)
                                                      ↓
                                                  generate_report.py
```

### 问题

1. **双轨制：** CodeFuse 和 CodeQL 使用不同的评估脚本
2. **功能不对称：**
   - `eval_codefuse_results.py` 功能更强（支持 FP mode、详细 CSV 输出、去重逻辑）
   - `aggregate_results.py` 只做简单聚合
3. **报告单向：** 只能为 CodeQL 生成报告
4. **SARIF 转换断层：** `sarif_to_csv.py` 未集成到自动化流程

### 理想流程（未实现）

```
[统一流程]
  规则 → 原始输出 → 标准化 CSV → 统一评估 → per-CWE metrics
                                              ↓
                                          聚合器
                                              ↓
                                    全局 metrics.json
                                              ↓
                                      报告生成器（双语）
```

---

## 7. 目标架构草案

### 设计原则

1. **声明式配置优于硬编码**
2. **统一评估流程（工具中立）**
3. **向后兼容，渐进重构**
4. **可测试、可验证**

### 目标目录结构

```
Vuln-Eval-Platform/
├── configs/
│   ├── cwe_manifest.yml          # CWE 注册表（新增）
│   ├── tools.yml                 # 工具配置（Phase 2）
│   └── paths.yml                 # 路径模板（Phase 2）
│
├── vep/                          # Python 包（Phase 2+）
│   ├── config/
│   ├── core/
│   ├── converters/
│   ├── evaluation/
│   └── reporting/
│
├── scripts/                      # 保留兼容性包装器
│   └── ...
│
├── docs/
│   ├── architecture_notes.md     # 本文档（Phase 1）
│   └── ...
│
├── rules/                        # 不变
├── tests/                        # 不变
├── experiments/                  # 不变
└── ...
```

---

## 8. Phase 1/2/3/4 路线图

### Phase 1: 配置索引层（当前阶段）✅

**目标：** 建立只读配置索引，不改变现有行为

**交付物：**
- ✅ `docs/refactor/architecture_notes.md`（本文档）
- ✅ `configs/cwe_manifest.yml`（CWE 注册表）
- ✅ `scripts/verify_manifest.py`（验证脚本，只读检查）

**保证：**
- ❌ 不修改任何现有脚本
- ❌ 不移动任何规则或测试文件
- ❌ 不改变评测输出格式
- ❌ 不引入新依赖（仅使用标准库 + PyYAML）

---

### Phase 2: 统一评估核心（未来）

**目标：** 重构评估逻辑为统一 pipeline

**计划：**
1. 创建 `vep/` Python 包
2. 统一 `eval_codefuse_results.py` 和 `aggregate_results.py` 逻辑
3. 自动化 SARIF → CSV 转换
4. 支持双工具报告生成

**保证：**
- 保留 `scripts/` 作为兼容性包装器
- 保持输出格式向后兼容

---

### Phase 3: 工具抽象层（未来）

**目标：** 抽象 Tool 接口，支持新工具接入

**计划：**
1. 定义 Tool Protocol（run / parse / evaluate）
2. 实现 CodeFuseTool / CodeQLTool
3. 支持插件式工具注册

---

### Phase 4: 自动化测试（未来）

**目标：** 建立测试体系

**计划：**
1. 单元测试（converter / evaluator / reporter）
2. 集成测试（端到端 pipeline）
3. Golden result 回归测试
4. Smoke test

---

## 9. Phase 1 不改变现有行为的承诺

### 明确声明

**Phase 1 只新增以下文件：**
1. `docs/refactor/architecture_notes.md`（本文档）
2. `configs/cwe_manifest.yml`（配置文件）
3. `scripts/verify_manifest.py`（验证脚本）

**Phase 1 不修改：**
- ❌ `run_eval.sh`
- ❌ `scripts/evaluation/eval_checker.sh`
- ❌ `scripts/evaluation/eval_codefuse_results.py`
- ❌ `scripts/evaluation/aggregate_results.py`
- ❌ `scripts/converters/*.py`
- ❌ `scripts/reporting/*.py`
- ❌ 任何规则文件（`.gdl`, `.ql`）
- ❌ 任何测试文件（`.java`）

**Phase 1 不移动：**
- ❌ 规则目录
- ❌ 测试目录
- ❌ 实验目录

**Phase 1 可以做的验证：**
- ✅ 读取现有文件路径
- ✅ 检查文件存在性
- ✅ 解析现有 CSV / JSON
- ✅ 报告配置不一致（warning only，不阻塞）

---

## 10. 验证清单

运行 `python scripts/verify_manifest.py` 应该输出：

```
✅ 所有 CWE manifest 条目对应的规则文件存在
✅ 所有 CWE manifest 条目对应的测试目录存在（如果声明）
✅ 所有实验目录可映射到 manifest
⚠️  发现命名不一致：tests 用 cwe022, rules 用 CWE-022（已知问题，Phase 2 处理）
```

**不应该：**
- ❌ 修改任何文件
- ❌ 创建任何目录
- ❌ 运行任何评测命令
- ❌ 生成任何报告

---

## 附录：当前 CWE 覆盖范围

| CWE-ID | CodeFuse 规则 | CodeQL 规则 | 测试样例 | 实验目录 |
|---|---|---|---|---|
| CWE-022 | ✅ | ✅ | ✅ | ✅ |
| CWE-078 | ✅ | ✅ | ✅ | ✅ |
| CWE-079 | ✅ | ✅ | ✅ | ✅ |
| CWE-089 | ✅ | ✅ | ✅ | ✅ |
| CWE-090 | ✅ | ✅ | ✅ | ✅ |
| CWE-327 | ✅ | ✅ | ✅ | ✅ |
| CWE-328 | ✅ | ✅ (328_328S) | ✅ | ✅ |
| CWE-330 | ✅ | ✅ | ✅ | ✅ |
| CWE-501 | ✅ | ✅ | ✅ | ✅ |
| CWE-614 | ✅ | ✅ | ✅ | ✅ |
| CWE-643 | ✅ | ✅ | ✅ | ✅ |

---

**文档结束**
