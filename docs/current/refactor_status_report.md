# 重构推进整理报告

生成时间：2026-08-31（基于 2026-06-28 首版、2026-08-30 二版更新）

> 本版与 2026-08-30 版的主要差异：**Phase 3（P2 统一实验入口）已完成并通过 parity gate**，
> v2 已正式接管全部评估入口，双轨时代结束。旧版全文见 git 历史。

## 结论

重构主线（规则包模块化 + 评估核心 v2 化 + 报告系统 v2 化 + 统一实验入口）**全部完成**。当前状态：

- Phase 1 已完成：CWE manifest 统一索引 + 只读验证层。
- Phase 2（A/B/C/D/F）已完成：`vep.core` / `vep.evaluation` 评估核心 + `vep.reporting` 双工具报告。
- **Phase 3 已完成（2026-08-31）**：`vep/tools/` 工具抽象层 + `run_pipeline.py` 统一入口；`run_eval.sh` /
  `eval_checker.sh` 降级为兼容 wrapper；parity gate 通过（见 `docs/audits/PARITY_M34_CODEFUSE_PIPELINE.md`）。
- 规则包侧 11 个 checker 全量回归 Recall = 1.0000，FN = 0；CWE-328/330/614 三个满分 checker。
- 剩余主线：P3（pytest + golden 回归体系）与 P4（FP 精度研究）。

## 重构时间线

| 时间 | 事件 |
|---|---|
| 2026-04-26 ~ 04-29 | 首批 GDL checker，docs 建立 |
| 2026-06-11 | Phase 1 + Phase 2A/2B/2C/2D 单日完成（评估核心 v2 全套） |
| 2026-06-18 | 定位并修复 macOS CodeFuse Java DB 根因（JAVA_HOME keg prefix），全量回归对齐 Linux baseline |
| 2026-06-28 | docs 结构重组，首版重构状态报告 |
| 2026-07-04 | P1 完成：模块化 V2 报告系统（Phase 2F），收编未提交变更 |
| 2026-08-30 | 状态整理，制定 Phase 3 计划 |
| 2026-08-31 | **Phase 3 完成**：M3.1 工具配置与环境门禁、M3.2 双工具 runner、M3.3 统一 pipeline、M3.4 parity gate + 旧入口降级 |

## Phase 3 交付明细

### M3.1 工具配置与环境门禁

- `configs/tools.yml`：工具路径配置中心化（优先级：CLI > 环境变量 > 配置文件 > PATH > 内置候选），修正 CodeQL DB 路径。
- `vep/tools/config.py`：路径发现逻辑（从 `eval_checker.sh` 原样迁移）；`CodeFuseTool.check_environment()`
  通过子进程复用 `scripts/check_codefuse_java_env.py`（无第二份 JAVA_HOME 实现），实测拦截了本机
  `JAVA_HOME=/opt/homebrew/opt/openjdk@17` 的坏 keg prefix。

### M3.2 双工具 runner

- `vep/core/manifest.py`：manifest 类型化加载（含 CWE-328_328S 特例）。
- `CodeFuseTool.run()/standardize()`：godel package-root workaround 原样迁移；标准化复用
  `codefuse_json_to_csv.py`，输出与旧产线逐字节一致。
- `CodeQLTool.run()/standardize()`：`database analyze` + `vep.evaluation.sarif`。

### M3.3 统一入口

- `vep/pipeline.py` + `scripts/evaluation/run_pipeline.py`：manifest 驱动，一条命令完成
  工具执行 → 标准化 → v2 评估 → 聚合 → 报告；`--stages` 可拆分（无工具机器可只评估）、
  `--keep-going`、`--skip-existing`、`--db-codefuse/--db-codeql`。

### M3.4 Parity gate 与旧入口降级

- 11/11 findings CSV 与 2026-06-19 规范产物逐字节一致。
- 10/11 CWE 指标一致；CWE-328 差异根因：ground truth 官方标注 `BenchmarkTest00003,hash,true,328S`
  为漏洞样本，旧 evaluator 把 `328S` 排除出 scope 产生口径性 FP，v2 修正为 TP。
  **CWE-328 成为第三个满分 checker**。
- `run_eval.sh` / `eval_checker.sh` 降级为 pipeline 兼容 wrapper（均端到端实测）；
  `run_codeql_experiments.py` 标记 deprecated（一个版本周期后删除）。

## 当前基线（2026-08-31，v2 口径，CodeFuse 全量回归）

| 指标 | TP | FP | FN | TN | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Overall | 1415 | 552 | 0 | 773 | 0.7194 | 1.0000 | 0.8368 |

- 机器可读基线：`reports/data/metrics_v2_codefuse_all.json`（CodeFuse）、`metrics_v2_codeql_all.json`（CodeQL，P=0.3876 / R=1.0000）。
- 分 CWE 明细：`docs/current/results.md`。
- FP 最重的 checker（P4 研究对象）：CWE-643（P=0.4545，18 FP）、CWE-090（0.5510，22 FP）、
  CWE-022（0.5519，108 FP）、CWE-078（0.5650，97 FP）、CWE-089（0.6445，150 FP）。

## 当前未完成 / 风险点

### 1. 缺少正式测试体系（P3 / Phase 4，未开始）

`tests/` 只有 benchmark 的 Java 用例。没有 pytest 单元测试、golden fixture、CI 入口。
本轮 M3.2 开发中 `build_rows` 漏传 `unknown_label`、`_discover_paths` 返回值解包错误两个问题都是
冒烟阶段人工发现的——正是测试体系缺失的代价。

### 2. 规则精度研究未启动（P4）

FP 集中在 5 个污点型 checker（合计 395 FP，占全部 FP 的 71%）。约束不变：patch 只进
CWE-specific 模块，不动 `TaintTracking.gdl`，改动必须全量回归（现在一条 pipeline 命令即可）。

### 3. CodeQL database create 未自动化

pipeline 校验 DB 存在并报错，但不负责建库。低优先级。

### 4. Linux 侧工具发现未实测

`vep/tools` 的发现逻辑平台中立（PATH + 与旧脚本相同的候选列表），M3.1~M3.4 验证均在 mac 完成；
下次在 Linux 机器跑一遍 `run_pipeline.py --tool codefuse --cwe 090 --stages run,evaluate` 即可补上。

## 路线图盘点

### 规则包路线（`docs/current/roadmap.md`）

M1~M4 已达成；**M5（具备回归、封装和技术报告的稳定 rule pack）**：封装 ✅（统一 pipeline + 文档）、
技术报告 ✅（v2 报告系统）、回归 ⬜（pipeline 全量回归命令已具备，pytest/golden 体系待 P3）。

### 重构路线（P0~P4）

| 阶段 | 内容 | 状态 |
|---|---|---|
| P0 | 冻结稳定基线 | ✅ 完成（2026-06） |
| P1 | 报告系统接 v2 | ✅ 完成（2026-07-04） |
| P2 | 统一实验入口 | ✅ 完成（2026-08-31，Phase 3 全部四个里程碑） |
| P3 | 测试体系 / golden regression | ⬜ 未开始 |
| P4 | 规则精度研究（降 FP） | ⬜ 未开始 |

## 建议下一步

### 主线（P3）：pytest + golden 回归体系

- 优先覆盖：`vep/core/normalization.py`、`vep/evaluation/evaluator.py`、`vep/evaluation/sarif.py`、
  `vep/tools/config.py`（路径发现是本轮最容易回归的部分）。
- golden fixtures：用 `experiments/cwe-090`、`cwe-328` 的小型 findings/ground truth 切片固化期望输出；
  CWE-328 必须包含 `328S` 行（防止 scope 口径再次漂移）。
- CI 入口：`compileall + pytest + verify_manifest.py` 三件套。

### 规则侧（P4，可与 P3 并行）

在 CWE-643 / 090 / 022 / 078 / 089 上做 CWE-local precision patch；每个 patch 报告 TP/FP/FN/P/R/F1
并跑 `run_pipeline.py --tool codefuse --cwe all` 全量回归。

## 参考文件

- `docs/refactor/PHASE3_PLAN.md`（Phase 3 计划与验收标准）
- `docs/audits/PARITY_M34_CODEFUSE_PIPELINE.md`（M3.4 parity 审计）
- `docs/refactor/PHASE1_SUMMARY.md` / `PHASE2_FINAL_SUMMARY.md`
- `docs/current/architecture.md` / `results.md` / `roadmap.md`
- `docs/guides/QUICK_START_PHASE2.md` / `evaluation_workflow.md`
- `reports/data/metrics_v2_codefuse_all.json` / `metrics_v2_codeql_all.json`（机器可读基线）
