# Phase 3 计划：工具抽象层与统一实验入口

> **文档状态：已完成并归档（2026-08-31）。** 当前 V3 状态见 `docs/current/refactor_status_report.md`。


创建时间：2026-08-30
前置阶段：Phase 1 ✅ / Phase 2（A~D）✅ / Phase 2F 报告系统双工具化 ✅（2026-07-04）
对应重构路线：`docs/current/refactor_status_report.md` 中的 **P2 统一实验入口**
预计工作量：4~8 小时（不含全量回归运行时间）

## 1. 背景与目标

Phase 2 完成后，仓库存在"两套能跑的评估路径"：

- 旧流程：`run_eval.sh`（CodeQL，旧聚合+旧报告）、`scripts/evaluation/eval_checker.sh`（CodeFuse，旧 evaluator）
- v2 流程：`eval_findings.py` / `eval_sarif_findings.py` / `aggregate_v2.py` / `generate_report_v2.py`，需手动逐条运行

Phase 3 的目标是**用一层工具抽象 + 一个 Python 总入口把双轨合并成单轨**：

1. 定义 Tool Protocol，封装 CodeFuse（godel）与 CodeQL（database analyze）的调用细节；
2. 新增 `run_pipeline.py` 总入口：manifest 驱动，一条命令完成 工具执行 → 结果标准化 → v2 评估 → 聚合 → 报告；
3. 验证与旧流程指标完全对齐后，`run_eval.sh` / `eval_checker.sh` 降级为兼容 wrapper。

**明确不做的事：**
- 不改任何 `.gdl` 规则，尤其不动 `TaintTracking.gdl`；
- 不删旧脚本（对齐验证通过后才降级为 wrapper）；
- 不动 `vep/reporting/`（Phase 2F 产物）；
- CodeQL database create 自动化不在本期范围（仅校验 DB 存在并给出提示）。

## 2. 现状要点（实现时必须保留的行为）

### CodeFuse 侧（来自 `scripts/evaluation/eval_checker.sh`）

- 工具发现顺序：CLI/环境变量 `CODEFUSE_HOME` > PATH 中的 `sparrow`（realpath 解析）> 硬编码候选路径。
- godel 2.1.0 package-root workaround：临时目录合并官方 `lib` 与本地 `rules/codefuse-query/lib`，用 `-p` 指向。
- 调用形态：`godel -p <package_root> -f <db> -Of -r <checker.gdl> --output-json <out.json>`。
- macOS 环境约束：`JAVA_HOME` 必须指向真实 JDK `Contents/Home`（6-18 修复的根因），已有 `scripts/check_codefuse_java_env.py` 做检查。

### CodeQL 侧（来自 `scripts/run_codeql_experiments.py`）

- `codeql database analyze <db> rules/codeql-query/<dir> --format=sarifv2.1.0 --output=<sarif>`。
- 该脚本的 CWE map 是硬编码的，Phase 3 改为从 manifest 读取（CWE-328 的 `CWE-328_328S` 目录特例 manifest 已覆盖）。
- 实际 DB 路径为 `dataset/codeql-db/benchmark-java`（manifest 中 `databases.codeql` 少了子目录，需在配置中修正）。

### Manifest（`configs/cwe_manifest.yml`）

已具备 Phase 3 所需的全部索引字段：`id` / `name` / `slug` / `slug_compact`、`codefuse.rule_file`、`codeql.rule_directory`、`tests`、`experiments.directory`、`databases`、`ground_truth`。**缺工具可执行路径配置**，本期补齐。

## 3. 交付物

### 3.1 工具路径配置中心化：`configs/tools.yml`（新增）

```yaml
version: "1.0"

codefuse:
  home: null            # 显式指定则跳过探测；null 时按发现顺序探测
  godel_bin: null       # 默认 <home>/godel-script/usr/bin/godel
  official_lib: null    # 默认 <home>/lib

codeql:
  bin: codeql           # PATH 中的可执行名或绝对路径

databases:
  codefuse: dataset/codefuse-db
  codeql: dataset/codeql-db/benchmark-java   # 修正 manifest 中的不完整路径

env_checks:
  codefuse_java_env: true   # 运行前强制执行 JAVA_HOME 校验（macOS 6-18 修复不回退）
```

发现优先级统一为：CLI 参数 > 环境变量（`CODEFUSE_HOME` / `GODEL_BIN` / `CODEQL_BIN`）> `configs/tools.yml` > PATH 探测 > 硬编码候选（迁移 `eval_checker.sh` 现有逻辑）。工具路径不入 manifest（manifest 只管 CWE 索引），单独一个 `tools.yml` 职责更清晰。

### 3.2 工具抽象层：`vep/tools/`（新增）

```
vep/tools/
├── __init__.py        # 导出 Tool / CodeFuseTool / CodeQLTool / build_tool()
├── base.py            # Tool Protocol + ToolRunResult 数据类
├── codefuse.py        # CodeFuseTool（含路径发现 + package-root workaround）
└── codeql.py          # CodeQLTool
```

Protocol 设计（保持最小接口，便于未来加第三个工具）：

```python
@dataclass
class ToolRunResult:
    tool: str                 # "codefuse" | "codeql"
    cwe: str                  # "CWE-022"
    raw_output: Path          # checker JSON 或 SARIF
    returncode: int
    log_file: Path | None

class Tool(Protocol):
    name: str
    def check_environment(self) -> list[str]: ...      # 返回问题列表，空列表 = 可运行
    def run(self, cwe: CweConfig, db: Path, out_dir: Path) -> ToolRunResult: ...
    def standardize(self, run: ToolRunResult, out_csv: Path) -> Path: ...
    # raw → normalized findings CSV：CodeFuse 走 codefuse_json_to_csv 逻辑，
    # CodeQL 直接复用 vep.evaluation.sarif（不再绕 scripts/converters/sarif_to_csv.py）
```

要点：
- `check_environment()` 把"工具没装/路径不对/JAVA_HOME 非法"在 run 之前暴露出来；JAVA_HOME 校验直接调用 `scripts/check_codefuse_java_env.py` 的现有逻辑，不重写第二份。
- package-root 临时目录合并、`trap` 清理等细节从 `eval_checker.sh` 原样迁移到 `CodeFuseTool.run()`。
- CodeFuseTool 失败时不中断整个 pipeline（由 orchestrator 决定 continue/abort）。

### 3.3 统一入口：`scripts/evaluation/run_pipeline.py`（新增）+ `vep/pipeline.py`

```bash
# 全量 11 个 checker，CodeFuse，跑工具+评估+聚合+报告
python3 scripts/evaluation/run_pipeline.py --tool codefuse --cwe all

# 只评估已有结果（工具没装的机器上也能跑）
python3 scripts/evaluation/run_pipeline.py --tool codeql --cwe all --stages evaluate,aggregate,report

# 单个 CWE 调试，跳过报告
python3 scripts/evaluation/run_pipeline.py --tool both --cwe 089 --no-report --keep-going
```

参数契约：

| 参数 | 取值 | 默认 |
|---|---|---|
| `--tool` | `codefuse` / `codeql` / `both` | 必填 |
| `--cwe` | `all` 或 id/slug 列表（`022 089`、`cwe-022` 均可，经 manifest 解析） | 必填 |
| `--stages` | `run,evaluate,aggregate,report` 的子集 | `run,evaluate,aggregate` |
| `--db` | 覆盖 DB 路径 | tools.yml |
| `--fp-mode` | `all_non_gt` / `in_scope` | `all_non_gt` |
| `--eval-dir-name` | 评估输出目录名 | `codefuse_eval_v2` / `codeql_eval_v2` |
| `--keep-going` | 单 CWE 失败不中断整体 | 关闭 |
| `--skip-existing` | metrics.json 已存在则跳过该 CWE | 开启 |
| `--out-root` | 聚合/报告输出根 | `reports/data` / `reports` |

流程（每个 CWE）：

```
manifest 条目 → Tool.check_environment() → Tool.run() → Tool.standardize()
  → vep.evaluation evaluator（v2，产 metrics.json + 4 张 detail CSV）
  → aggregate_v2（全部完成后，产 vep.aggregate.v2 JSON）
  → generate_report_v2（--stages 含 report 时）
```

每 CWE 日志写入 `experiments/<slug>/logs/<tool>_pipeline.log`。

### 3.4 旧入口降级（对齐验证通过后执行）

- `run_eval.sh` 改为调用 `run_pipeline.py --tool codeql --stages evaluate,aggregate,report`（保留 SARIF 存在性检查）。
- `scripts/evaluation/eval_checker.sh` 保留为 CodeFuse 单 CWE 的兼容 wrapper（内部转发 `run_pipeline.py --tool codefuse --cwe <id>`）。
- `scripts/run_codeql_experiments.py` 标记 deprecated（docstring 注明已被 pipeline 取代），对齐验证一个版本周期后删除。

## 4. 里程碑与验收标准

### M3.1 配置与工具发现（~1h）

- `configs/tools.yml` 落地，含 codeql DB 路径修正。
- 路径发现逻辑 + `check_environment()` 完成。
- 验收：两台环境（mac / linux）上 `check_environment` 输出正确；故意设错 `JAVA_HOME` 能被拦截。

### M3.2 Tool Protocol + 双工具实现（~2-3h）

- `vep/tools/` 三个模块完成，godel workaround 原样迁移。
- 验收：`CodeFuseTool.run()` 单跑 CWE-089 产出的 JSON 与 `eval_checker.sh` 输出 diff 为空；`CodeQLTool.run()` 单跑 CWE-079 产出 SARIF 与旧脚本输出一致。

### M3.3 Pipeline 编排（~1.5-2h）

- `run_pipeline.py` 全参数可用，`--stages` 可拆分。
- 验收：`--stages evaluate,aggregate,report` 在无 godel/CodeQL 的机器上可独立运行。

### M3.4 对齐验证与切换（~1h + 回归运行时间）

- 用 pipeline 跑 11 个 checker 全量 CodeFuse 回归，产出 `reports/data/metrics_v2_codefuse_all.json`。
- **对齐门槛（parity gate）**：overall 与 `reports/data/mac-fixed-validation/aggregate_metrics.json` 完全一致（TP=1414 / FP=553 / FN=0 / P=0.7189 / R=1.0000 / F1=0.8364），且分 CWE 指标与 `docs/current/results.md` 一致。
- 通过后执行 3.4 的入口降级；不通过则修复 pipeline，不动旧流程。

## 5. 风险与约束

| 风险 | 缓解 |
|---|---|
| godel package-root workaround 迁移走样 | M3.2 用 diff 对拍验证；代码从 `eval_checker.sh` 逐行移植 |
| macOS JAVA_HOME 修复被绕过 | `check_environment()` 强制调用现有 env 检查，tools.yml 可关但默认开 |
| 双轨期间指标口径漂移 | parity gate 以机器可读 JSON 对比，不接受人工"看起来一致" |
| 工具未安装的机器无法全流程 | `--stages` 拆分，run 阶段独立 |
| manifest 字段变更破坏 pipeline | pipeline 只经 `vep/core` 读取 manifest，不做自己的 YAML 解析 |

## 6. 与整体路线的关系

- 本期完成 = 重构路线 **P2 完成**；之后进入 **Phase 4 / P3 测试体系**（pytest + golden regression，优先覆盖 `vep/core/normalization.py`、`vep/evaluation/evaluator.py`、`vep/evaluation/sarif.py`）。
- Phase 3 + Phase 4 完成后，`docs/current/roadmap.md` 的 **M5（具备回归、封装和技术报告的稳定 rule pack）** 即达成。
- 规则侧 P4（CWE-643 / 090 / 022 / 078 / 089 降 FP）可与本计划并行，互不触碰。

## 参考文件

- `docs/current/refactor_status_report.md`（P0~P4 路线与当前状态）
- `docs/refactor/PHASE2_FINAL_SUMMARY.md`（Phase 3 原始设想与工作量估计）
- `scripts/evaluation/eval_checker.sh` / `scripts/run_codeql_experiments.py`（待迁移行为的事实来源）
- `configs/cwe_manifest.yml` / `docs/guides/run_codefuse_queries.md`
