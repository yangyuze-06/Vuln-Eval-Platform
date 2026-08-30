# 重构推进整理报告

生成时间：2026-08-30（基于 2026-06-28 首版更新）

> 本版与 2026-06-28 首版的主要差异：P1（报告系统接 v2）已完成；未提交变更已收编；
> 旧版基线 markdown 报告已清理，机器可读基线仍保留。旧版全文见 git 历史。

## 结论

这波重构的主线（规则包模块化 + 评估核心 v2 化 + 报告系统 v2 化）已经完成，从"地基阶段"进入了"收尾接线阶段"。当前状态：

- Phase 1 已完成：CWE manifest 统一索引 + 只读验证层。
- Phase 2（A/B/C/D）已完成：`vep.core` / `vep.evaluation` 统一评估核心，支持 CodeFuse CSV、CodeQL SARIF、详细审计输出和多 CWE 聚合。
- Phase 2F（即重构路线中的 P1）已完成（2026-07-04）：`vep/reporting/` + `generate_report_v2.py`，支持 legacy / `vep.eval.v2` / `vep.aggregate.v2` schema 自动识别、双工具对比、中英双语报告。
- 规则包侧 11 个 CodeFuse checker 全量回归 Recall = 1.0000，macOS fixed DB 与 Linux baseline 完全对齐。
- 工作区干净：6-28 报告中提到的未提交变更（`run_eval.sh` 修改、`scripts/run_codeql_experiments.py`）已在 7-04 提交中收编。

剩余主线工作是重构路线中的 P2（统一实验入口）、P3（pytest/golden 回归体系）、P4（FP 精度研究），对应 PHASE2_FINAL_SUMMARY 里的 Phase 3 / Phase 4 / 精度研究。

## 重构时间线

| 时间 | 事件 |
|---|---|
| 2026-04-26 ~ 04-29 | 首批 GDL checker（CWE-078/079/089/090/327/328/330/501/614/643），docs 建立 |
| 2026-06-11 | Phase 1（manifest + 验证层）、Phase 2A/2B/2C/2D（评估核心 v2 全套）单日完成 |
| 2026-06-12 ~ 06-18 | 跨平台复现审计，定位并修复 macOS CodeFuse Java DB 根因（JAVA_HOME 指向 Homebrew keg prefix），全量回归对齐 Linux baseline |
| 2026-06-28 | docs 文档结构重组（current / refactor / audits / guides），生成首版重构状态报告 |
| 2026-07-04 | **P1 完成**：模块化 V2 报告系统（`vep/reporting/`，Phase 2F）；清理旧版报告文件；收编 `run_codeql_experiments.py` 与 `run_eval.sh` 修改 |
| 2026-08-30 | 现状整理（本报告） |

## 已解决的问题

### 1. CWE 配置分散和命名不一致（Phase 1）

规则目录 `CWE-022`、测试目录 `cwe022`、实验目录 `cwe-022`、脚本参数 `022` 四套命名并存的问题，通过 `configs/cwe_manifest.yml` 统一索引层解决，`scripts/verify_manifest.py` / `validate_manifest.py` 提供只读验证。

### 2. 评估逻辑脚本化、工具间不对称（Phase 2）

CodeFuse 与 CodeQL 评估路径分裂的问题，通过 `vep/evaluation/` 包解决：findings / ground_truth / evaluator / metrics / sarif / aggregate 六个可复用模块 + 三个 CLI（`eval_findings.py`、`eval_sarif_findings.py`、`aggregate_v2.py`）。SARIF 从"两步手工转换"变为一步集成。

### 3. 评估输出缺少审计细节（Phase 2B）

已补齐 `tp.csv` / `fp.csv` / `fn.csv` / `outside_scope.csv`、`fnr` / `fpr` / `fdr`、`raw_findings` / `dedup_findings`、`fp_mode=all_non_gt|in_scope`，支持人工审计、precision patch 和回归对比。

### 4. macOS CodeFuse DB 环境问题（2026-06-18）

根因：`JAVA_HOME` 指向 Homebrew keg prefix 导致类型解析退化、产生 FN。修正为真实 JDK `Contents/Home` 后与 Linux 对齐。机器可读基线保留在 `reports/data/mac-fixed-validation/aggregate_metrics.json`。

### 5. 报告系统无法消费 v2 schema（P1 / Phase 2F，2026-07-04 完成）

新增 `vep/reporting/`（`report_generator.py` / `plot_generator.py` / `text_report.py`）和 CLI `scripts/reporting/generate_report_v2.py`：

- schema 自动识别：legacy / `vep.eval.v2` / `vep.aggregate.v2`
- 多 metrics 文件合并，支持 CodeFuse vs CodeQL 双工具对比
- 中英双语报告 + 图表

6-28 报告中"v2 结果能算但不能自然展示"的断点已消除。旧 `generate_report.py` / `plots_metrics.py` 保留，兼容性未破坏。

### 6. 工作区未提交状态（已解决）

6-28 报告记录的 `run_eval.sh`（venv→.venv、python→python3）修改和未跟踪的 `scripts/run_codeql_experiments.py`（CodeQL 全 CWE 批量执行：analyze → SARIF 转 CSV → 评估）均已在 7-04 提交收编。git status 当前干净。

### 7. 规则精度持续改进（规则包侧）

- 11 个 checker 全量 Recall = 1.0000，FN = 0。
- CWE-501 Patch 1：outside-scope findings 从 493 降到 0，FN 保持 0。
- CWE-330、CWE-614 达到 P/R/F1 全部 1.0000。

## 当前基线（macOS fixed DB，2026-06-18，CodeFuse 全量回归）

| 指标 | TP | FP | FN | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|
| Overall | 1414 | 553 | 0 | 0.7189 | 1.0000 | 0.8364 |

分 CWE 明细见 `docs/current/results.md`。FP 最重的 checker（P4 精度研究对象）：

| CWE | Precision | FP |
|---|---:|---:|
| CWE-643 | 0.4545 | 18 |
| CWE-090 | 0.5510 | 22 |
| CWE-022 | 0.5519 | 108 |
| CWE-078 | 0.5650 | 97 |
| CWE-089 | 0.6445 | 150 |

## 当前未完成 / 风险点

### 1. v2 还没有接管旧入口（P2 / Phase 3，未开始）

- `run_eval.sh` 仍走旧流程（`aggregate_results.py` → `plots_metrics.py` → `generate_report.py`）。
- `scripts/evaluation/eval_checker.sh` 仍用旧 evaluator。
- 无 `vep/tools/` 工具抽象层、无 Tool Protocol、无可替代 `run_eval.sh` 的 Python 总入口（仓库中无 `run_pipeline.py`）。
- 旧流程脚本（`aggregate_results.py` / `eval_codefuse_results.py` / `generate_report.py` / `plots_metrics.py`）仍在维护面内，双轨认知成本仍在。

### 2. 缺少正式测试体系（P3 / Phase 4，未开始）

`tests/` 目前只有 benchmark 的 Java 用例，没有 pytest 单元测试、golden fixture、CI 回归入口。对 `TaintTracking.gdl` 或 evaluator 的改动仍依赖手动全量回归，风险偏高。

### 3. v2 链路缺一次端到端全量验证

`reports/data/` 中只有 2-CWE 的 `metrics_v2_codefuse_subset.json`（6-11 验证产物），尚无用 v2 评估 11 个 checker 后的 `metrics_v2_codefuse_all.json` 聚合，v2 报告系统也还没有消费过全量真实数据。

### 4. 基线 markdown 报告已删除（低风险）

7-04 清理删除了 `reports/full-regression-mac-fixed-2026-06-18.md` 等旧版报告文件，人读版基线描述目前主要靠 `docs/current/results.md` 承担；机器可读基线（`mac-fixed-validation/` 下的 aggregate JSON + TSV）完好。如需人读版可从 v2 报告系统重新生成。

## 路线图盘点

仓库目前有两条并行的路线图，方向一致、互补：

### 1. `docs/current/roadmap.md`（规则包路线）

- 短期：稳定化与封装（全量回归、checker 模板统一、rule pack 封装、suppression 标注）；候选 checker：CWE-601 / 094 / 502。
- 中期：框架加固（`SecurityReporting.gdl`、`SinkHelpers.gdl`、统一 source 入口、标准 checker 模板）。
- 长期：精度研究（strong update、collection/key sensitivity、path sensitivity、field/context sensitivity、可解释 taint 路径）。
- 里程碑 M1~M5 已全部达成至 M4；**M5（具备回归、封装和技术报告的稳定 rule pack）中"回归"与"封装"尚未完成**。

### 2. `docs/current/refactor_status_report.md` 首版提出的重构路线（P0~P4）

| 阶段 | 内容 | 状态 |
|---|---|---|
| P0 | 冻结稳定基线 | ✅ 基本完成（JSON/TSV 基线在，未提交变更已收编） |
| P1 | 报告系统接 v2 | ✅ 完成（2026-07-04） |
| P2 | 统一实验入口 | ⬜ 未开始 |
| P3 | 测试体系 / golden regression | ⬜ 未开始 |
| P4 | 规则精度研究（降 FP） | ⬜ 未开始（CWE-501 patch 属规则包侧自发进展） |

约束（继续有效）：优先在 CWE-specific sink/sanitizer/scope filter 内做 patch；不轻易改 `TaintTracking.gdl`；公共 taint engine 改动必须跑 11 checker 全量回归。

## 建议下一步

### Quick win（半天内）：v2 链路端到端验证

```bash
python3 scripts/verify_manifest.py
python3 scripts/evaluation/aggregate_v2.py \
  --eval-root experiments \
  --tool codefuse \
  --eval-dir-name codefuse_eval_v2b \
  --out reports/data/metrics_v2_codefuse_all.json \
  --manifest configs/cwe_manifest.yml
python3 scripts/reporting/generate_report_v2.py \
  --metrics reports/data/metrics_v2_codefuse_all.json \
  --out-dir reports
```

产出 v2 全量聚合 JSON + 双工具报告，验证新报告链路，同时与 `mac-fixed-validation` 基线（TP=1414 / FP=553 / FN=0）核对一致性。

### 主线（P2）：统一实验入口

按首版报告的 P2 方案：新增 `run_pipeline.py` 总入口，从 manifest 读取 CWE 列表，支持 CodeFuse / CodeQL / both、单/多 CWE、只评估或重跑工具；完成后 `run_eval.sh` 降级为兼容 wrapper。这是消除双轨的关键一步。

详细实施方案已落在 `docs/refactor/PHASE3_PLAN.md`（Phase 3：工具抽象层与统一实验入口），含交付物设计、里程碑和 parity gate 验收标准。

### 然后（P3）：pytest + golden 回归

优先覆盖 `vep/core/normalization.py`、`vep/evaluation/evaluator.py`、`vep/evaluation/sarif.py`，固化 2~3 个小型 fixture 和 golden metrics 对比。

### 规则侧（P4，可与工程侧并行）

在 FP 最重的 CWE-643 / 090 / 022 / 078 / 089 上做 CWE-local precision patch，每个 patch 必须报告 TP/FP/FN/P/R/F1 并跑全量回归。

## 参考文件

- `docs/refactor/PHASE1_SUMMARY.md` / `PHASE2_FINAL_SUMMARY.md` / `PHASE2_EVALUATION_CORE.md` / `PHASE2B_EVALUATOR_DETAILS.md`
- `docs/refactor/architecture_notes.md`
- `docs/current/architecture.md` / `results.md` / `roadmap.md`
- `docs/guides/QUICK_START_PHASE2.md` / `evaluation_workflow.md`
- `docs/audits/CROSS_PLATFORM_REPRO_AUDIT.md` / `audits/java-database/`
- `reports/data/mac-fixed-validation/aggregate_metrics.json`（机器可读基线）
