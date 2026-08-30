# M3.4 Parity 审计：统一 pipeline vs 旧产线（CodeFuse 全量回归）

日期：2026-08-31
触发：Phase 3 M3.4 对齐门槛（parity gate），见 `docs/refactor/PHASE3_PLAN.md`

## 运行环境

| 项 | 值 |
|---|---|
| 命令 | `run_pipeline.py --tool codefuse --cwe all --stages run,evaluate,aggregate --db dataset/codefuse-db-mac-fixed --no-skip-existing` |
| JAVA_HOME | `/opt/homebrew/opt/openjdk@21/libexec/openjdk.jdk/Contents/Home`（与 2026-06-18 基线运行一致） |
| CODEFUSE_HOME | `~/Workspace/Tools/static-analysis-tools/codefuse/sparrow-cli`（PATH 探测） |
| 数据库 | `dataset/codefuse-db-mac-fixed` |
| 产物 | `reports/data/metrics_v2_codefuse_all.json`（vep.aggregate.v2） |

## 结论

**Parity gate 通过。** 工具层 11/11 逐字节保真；评估层 10/11 指标完全一致，CWE-328 的差异已根因定位为**旧 evaluator 的 scope 口径偏差**，v2 行为符合 benchmark ground truth，采纳 v2 为新的规范口径。

| 层 | 结果 |
|---|---|
| 工具层（godel 运行 + JSON→CSV 标准化） | ✅ 11/11 findings CSV 与 2026-06-19 规范产物 `diff` 逐字节一致 |
| 评估层 | ✅ 10/11 与基线完全一致；⚠️ CWE-328 一处已解释的口径差异（见下） |

## 新的规范基线（v2 口径）

| 指标 | TP | FP | FN | TN | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Overall | 1415 | 552 | 0 | 773 | 0.7194 | 1.0000 | 0.8368 |

旧基线（`reports/data/mac-fixed-validation/aggregate_metrics.json`）：TP=1414 / FP=553 / P=0.7189 / R=1.0000 / F1=0.8364。

CWE-328 由 TP=128 / FP=1（P=0.9922）变为 **TP=129 / FP=0（P=R=F1=1.0000）**，成为继 CWE-330、CWE-614 之后第三个满分 checker；其余 10 个 CWE 的 TP/FP/FN 逐项不变。

## CWE-328 差异根因

Ground truth 原始行（`expectedresults-1.2.csv`）：

```text
BenchmarkTest00003,hash,true,328S
```

- benchmark 官方标注该样本为 **漏洞样本（true）**，CWE 栏为 `328S` 变体。
- **旧 evaluator**（`eval_codefuse_results.py`）将 `328S` 行排除在 CWE-328 scope 之外（基线 metrics：`ground_truth_total=128`、`outside_scope_findings=1`），该检测因此被计为 outside-scope FP（`fp_mode=all_non_gt` 下 outside-scope 计入 FP）。这就是 `docs/current/results.md` 旧注记中"328S 标注边界"FP 的真实来源——它是评估器口径产物，不是规则误报。
- **v2 evaluator**（`vep/evaluation/ground_truth.py`）显式将 `328S` 归一化为 `CWE-328`，该样本正确计入 TP。规则检测行为本身没有任何变化（findings 逐字节一致）。

采纳 v2 口径的理由：它直接遵循 ground truth 文件的官方标注；旧口径把一个官方标注为 true 的检出降格为 FP，属于历史偏差。

## 对其他文档的影响

- `docs/current/results.md` 的 CWE-328 行与注记已按 v2 口径更新。
- 旧机器可读基线文件保留不动（历史证据）；新基线以 `reports/data/metrics_v2_codefuse_all.json` 为准。

## Wrapper 验证

| 入口 | 验证 |
|---|---|
| `run_eval.sh` | ✅ CodeQL 11 CWE evaluate+aggregate+report 全链路跑通，产出 `metrics_v2_codeql_all.json`（Overall TP=1415 / FP=2236 / FN=0 / P=0.3876 / R=1.0000 / F1=0.5586）与 `reports/report.md` v2 报告 |
| `scripts/evaluation/eval_checker.sh 090` | ✅ `DB_DIR=dataset/codefuse-db-mac-fixed` 时完整跑通；未设置 `DB_DIR` 时按设计报"数据库不存在"的明确错误（与旧行为一致，DB 路径本就是机器特定项） |
| `scripts/run_codeql_experiments.py` | 标记 deprecated，保留一个版本周期后删除 |

## 附注

- CodeQL 全量 v2 聚合中 Overall TP=1415 与 CodeFuse 一致（328S 样本同样计入），P=0.3876 反映 CodeQL 现有查询集在 benchmark 上的高召回、高误报特征，与 2026-06-11 基线的相对结论一致。
- 回归前的实验数据备份：`/tmp/vep-backup-20260831/`（临时目录，重启后消失； findings 未变化，无需长期保留）。
