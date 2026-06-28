# 重构推进整理报告

生成时间：2026-06-28 20:34 CST

## 结论

这波重构已经完成了“规则包模块化 + 评估核心 v2 化”的主要地基工作。当前状态不是半路烂尾，而是进入了一个比较清晰的过渡期：新架构已经能独立跑通核心评估、SARIF 评估和多 CWE 聚合；旧流程仍保留作为稳定入口；下一步重点应从“继续堆 checker”切换到“统一入口、报告系统接 v2、回归测试体系”。

当前可概括为：

- Phase 1 已完成：建立 CWE manifest、只读验证层和架构诊断文档。
- Phase 2 已完成：建立 `vep.core` / `vep.evaluation` 统一评估核心，支持 CodeFuse CSV、CodeQL SARIF、detail CSV 和多 CWE 聚合。
- 规则包侧已完成 11 个 CodeFuse checker，macOS fixed DB 全量回归与 Linux baseline 对齐，整体 Recall = 1.0000。
- 仍处在双轨状态：`run_eval.sh`、`eval_checker.sh`、报告脚本还主要走旧流程；v2 目前是并行可用路径，尚未成为默认总入口。

## 已解决的问题

### 1. CWE 配置分散和命名不一致

之前同一个 CWE 在不同位置有多套命名：

- 规则目录：`CWE-022`
- 测试目录：`cwe022`
- 实验目录：`cwe-022`
- 脚本参数：`022`

Phase 1 通过 `configs/cwe_manifest.yml` 建立了统一索引层，用 manifest 显式保存不同 slug 和工具路径。`scripts/verify_manifest.py` / `scripts/validate_manifest.py` 负责只读验证，降低路径漂移风险。

### 2. 评估逻辑脚本化、工具间不对称

旧流程里 CodeFuse 和 CodeQL 的评估路径明显分裂：

- CodeFuse：`eval_codefuse_results.py`
- CodeQL：SARIF 转 CSV 后再聚合

Phase 2 新增 `vep/evaluation/` 包，把 finding、ground truth、evaluator、metrics、SARIF parser、aggregate 拆成可复用模块，并提供三个 CLI：

- `scripts/evaluation/eval_findings.py`
- `scripts/evaluation/eval_sarif_findings.py`
- `scripts/evaluation/aggregate_v2.py`

这解决了核心评估逻辑不可复用、SARIF 处理断层、多 CWE 聚合弱的问题。

### 3. 评估输出缺少审计细节

Phase 2B 已补齐：

- `tp.csv`
- `fp.csv`
- `fn.csv`
- `outside_scope.csv`
- `fnr` / `fpr` / `fdr`
- `raw_findings` / `dedup_findings`
- `fp_mode=all_non_gt|in_scope`

这些输出能支持后续人工审计、precision patch 和回归对比。

### 4. macOS CodeFuse DB 环境问题

这波也定位并修复了 macOS 上 CodeFuse/Sparrow Java DB 构建问题：`JAVA_HOME` 指向 Homebrew keg prefix 时会导致类型解析退化，进而产生 FN。修正为真实 JDK `Contents/Home` 后，macOS fixed DB 与 Linux baseline 对齐。

验证结果来自 `reports/full-regression-mac-fixed-2026-06-18.md`：

| 构建 | TP | FP | FN | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|
| Linux 2026-06-11 | 1414 | 553 | 0 | 0.7189 | 1.0000 | 0.8364 |
| Old Mac current experiment outputs | 1347 | 545 | 67 | 0.7119 | 0.9526 | 0.8149 |
| Fixed Mac | 1414 | 553 | 0 | 0.7189 | 1.0000 | 0.8364 |

### 5. 规则包模块化基本成型

当前规则框架已经拆成：

- `JavaServletSources.gdl`
- `TaintHelpers.gdl`
- `TaintTracking.gdl`
- CWE-specific `sinks/*.gdl`
- CWE-specific `sanitizers/*.gdl`
- thin checker 入口：`checkerXXX.gdl`

已完成 11 个 checker：

- CWE-022 / 078 / 079 / 089 / 090 / 643
- CWE-327 / 328 / 330
- CWE-614 / 501

当前 CodeFuse full regression 汇总：

| 指标 | 值 |
|---|---:|
| TP | 1414 |
| FP | 553 |
| FN | 0 |
| Precision | 0.7189 |
| Recall | 1.0000 |
| F1 | 0.8364 |

其中 CWE-330 和 CWE-614 已达到 Precision / Recall / F1 全部 1.0000。

## 当前未完成 / 风险点

### 1. v2 还没有接管旧入口

`docs/refactor/PHASE2_FINAL_SUMMARY.md` 明确记录：v2 是并行路径，未替换旧流程。

仍未替换的部分：

- `run_eval.sh` 仍使用旧聚合和旧报告流程。
- `eval_checker.sh` 仍使用旧 evaluator。
- 报告系统仍读取 `reports/data/metrics.json` 旧 schema。
- v2 CLI 需要手动运行。

这意味着当前工程存在“两套能跑的评估路径”，短期安全，但长期会增加认知成本和维护成本。

### 2. 报告系统还没有 v2 schema 支持

`scripts/reporting/generate_report.py` 和 `scripts/reporting/plots_metrics.py` 仍读取旧 `reports/data/metrics.json`。v2 的 `schema_version=vep.eval.v2` / `vep.aggregate.v2` 尚未被报告系统消费。

建议下一步优先处理这个点，因为它能直接把 v2 评估结果转成用户可读产物。

### 3. 缺少正式测试体系

目前验证主要依赖：

- 手动命令
- `compileall`
- 特定 CWE 对比
- 全量回归报告

还没有 pytest 单元测试、golden result fixture、CI 回归入口。对公共模块如 `TaintTracking.gdl` 或 evaluator 改动时，风险仍偏高。

### 4. 工具抽象层尚未实现

还没有：

- `vep/tools/codefuse.py`
- `vep/tools/codeql.py`
- 统一 Tool Protocol
- 可替代 `run_eval.sh` 的 Python 总入口

因此 CodeQL database analyze、CodeFuse query run、结果转换、评估、聚合还没有形成真正一体化 pipeline。

### 5. 当前工作区有未提交变更

当前 `git status --short` 显示：

```text
 M run_eval.sh
?? scripts/run_codeql_experiments.py
```

`run_eval.sh` 的修改点：

- 虚拟环境从 `venv` 改为 `.venv`
- `python` 改为 `python3`

`scripts/run_codeql_experiments.py` 是一个新的 CodeQL 全 CWE 批量执行脚本，会依次跑 CodeQL analyze、SARIF 转 CSV，然后调用 `./run_eval.sh`。这个方向符合“自动化 CodeQL database analyze / 全量实验”的路线，但它目前还是未提交文件，需要进一步 review：

- 是否复用 manifest，避免硬编码 CWE map。
- 是否改用 v2 `eval_sarif_findings.py`，避免继续加深旧流程。
- 是否处理 CodeQL DB 路径、query pack、失败恢复和局部重跑。

## 路线图判断

仓库已有路线图：`docs/current/roadmap.md`。它的方向仍然有效，但需要和 Phase 2 的 v2 评估架构合并理解。

建议路线如下。

### P0：先冻结当前稳定基线

目标：把“现在可复现的好状态”钉住。

- 保留 `reports/full-regression-mac-fixed-2026-06-18.md` 作为当前 CodeFuse baseline。
- 把 `reports/data/mac-fixed-validation/aggregate_metrics.json` 作为机器可读证据。
- 对未提交的 `run_eval.sh` 和 `scripts/run_codeql_experiments.py` 做一次 review，决定纳入或重做。

验收标准：

- 11 个 CodeFuse checker 全量回归仍为 FN=0。
- manifest 验证通过。
- 文档能指出正式 baseline 文件。

### P1：报告系统接入 v2

目标：让 v2 评估结果能直接生成图表和报告。

建议任务：

- `generate_report.py` 支持 `vep.aggregate.v2`。
- `plots_metrics.py` 支持 v2 aggregate schema。
- 保持旧 schema 兼容。
- 添加一个 `reports/data/metrics_v2_*.json` 的样例验证命令。

验收标准：

- v2 aggregate JSON 能生成报告。
- 旧 `reports/data/metrics.json` 仍能生成报告。

### P2：统一实验入口

目标：减少双轨认知成本。

建议任务：

- 新增 Python CLI，例如 `scripts/evaluation/run_pipeline.py`。
- 从 manifest 读取 CWE 列表和规则路径。
- 支持 CodeFuse、CodeQL 或 both。
- 支持单 CWE / 多 CWE。
- 支持只评估已有结果、重新跑工具、重新聚合。

验收标准：

- 单个命令能完成：工具执行 -> 结果标准化 -> v2 评估 -> 聚合 -> 报告。
- `run_eval.sh` 可降级为兼容 wrapper。

### P3：测试体系和 golden regression

目标：降低后续精度 patch 和公共 taint engine 修改风险。

建议任务：

- 为 `vep/core/normalization.py`、`vep/evaluation/evaluator.py`、`vep/evaluation/sarif.py` 写 pytest。
- 固化 2 到 3 个小型 fixture。
- 增加 golden metrics 对比。
- 为 11 个 checker 保留全量回归命令。

验收标准：

- 修改 evaluator 后可以快速跑单元测试。
- 修改 GDL 公共模块后必须跑全量回归。

### P4：规则精度研究

目标：在 Recall=1.0000 的基础上降低 FP。

优先对象：

- CWE-643：Precision 0.4545，FP 18。
- CWE-022：Precision 0.5519，FP 108。
- CWE-078：Precision 0.5650，FP 97。
- CWE-090：Precision 0.5510，FP 22。
- CWE-089：Precision 0.6445，FP 150。

约束：

- 优先在 CWE-specific sink/sanitizer/scope filter 内做 patch。
- 不要轻易改 `TaintTracking.gdl`。
- 公共 taint engine 改动必须跑 11 个 checker 全量回归。

## 建议下一步

最推荐下一步做 P1：报告系统接 v2。原因是它工作量可控，能立刻消除“v2 结果能算但不能自然展示”的断点，而且不会碰公共 taint engine。

建议命令入口：

```bash
python3 scripts/verify_manifest.py
python3 -m compileall vep/ scripts/evaluation/
python3 scripts/evaluation/aggregate_v2.py \
  --eval-root experiments \
  --tool codefuse \
  --eval-dir-name codefuse_eval_v2b \
  --out reports/data/metrics_v2_codefuse_all.json \
  --manifest configs/cwe_manifest.yml
```

然后改造：

```bash
python3 scripts/reporting/plots_metrics.py
python3 scripts/reporting/generate_report.py
```

让它们既能读旧 `metrics.json`，也能读 v2 aggregate。

## 参考文件

- `docs/refactor/PHASE1_SUMMARY.md`
- `docs/refactor/PHASE2_FINAL_SUMMARY.md`
- `docs/current/architecture.md`
- `docs/guides/evaluation_workflow.md`
- `docs/current/roadmap.md`
- `docs/current/results.md`
- `reports/full-regression-mac-fixed-2026-06-18.md`
- `reports/data/mac-fixed-validation/aggregate_metrics.json`
