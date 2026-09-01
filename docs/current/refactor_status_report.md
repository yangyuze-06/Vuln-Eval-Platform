# V3 重构与发布状态

更新时间：2026-09-01

## 结论

规则模块化、评估核心 v2、工具抽象、统一 pipeline、golden regression、CI 与双工具报告编排均已完成。V3.0.0 发布基线为：

- 11 个 CodeFuse-Query / GodelScript Java checker。
- CodeFuse-Query 和 CodeQL 共用 `run_pipeline.py`。
- 工具自动发现与 CodeFuse JAVA_HOME 门禁。
- `vep.eval.v2` 单 CWE 评估和 `vep.aggregate.v2` 聚合。
- CodeFuse-Query + CodeQL 联合报告，以及两份独立报告。
- pytest、golden fixtures、CWE-328 `328S` 守卫和 Python 3.9/3.11 CI。
- 旧入口保留为兼容 wrapper。

## 阶段编号说明

仓库历史上存在两套编号：

1. 早期规则模块化 Phase 1～5：source、helper、taint、sink、sanitizer/barrier，现已全部完成并归档。
2. 工程化路线 P0～P4：P0 基线、P1 v2 报告、P2 统一入口、P3 测试体系均已完成；P4 规则精度研究进入 V3.x，不阻塞 V3.0.0。

历史文档保留在 `docs/refactor/`，当前状态以本文和 `docs/current/roadmap.md` 为准。

## 交付时间线

| 时间 | 交付 |
|---|---|
| 2026-06-11 | Manifest 与 v2 evaluation core |
| 2026-06-18 | 修复 macOS JAVA_HOME/JDK type-model 根因 |
| 2026-07-04 | v2 双工具报告系统 |
| 2026-08-31 | Phase 3 统一 pipeline；Phase 4 测试、golden、CI |
| 2026-09-01 | V3 双工具联合/独立报告编排、文档和发布材料 |

## V3 基线（`all_non_gt`）

| 工具 | TP | FP | FN | TN | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|---:|
| CodeFuse-Query | 1415 | 552 | 0 | 773 | 0.7194 | 1.0000 | 0.8368 |
| CodeQL | 1415 | 2236 | 0 | 794 | 0.3876 | 1.0000 | 0.5586 |

机器可读基线：

- `reports/data/metrics_v2_codefuse_all.json`
- `reports/data/metrics_v2_codeql_all.json`

CWE-328 的 OWASP `328S` 行必须计入 CWE-328；golden 测试要求 `BenchmarkTest00003` 出现在 `tp.csv`。

## 当前非阻塞事项

- P4/V3.x 精度研究：优先审计 CWE-089、022、078、090、643 的 FP。
- CodeQL database create 仍由用户在 pipeline 外完成。
- Linux 侧真实 CodeFuse 工具发现需要补一次跨平台运行记录。
- `scripts/run_codeql_experiments.py` 和旧报告脚本继续保留一个兼容周期。

精度 patch 应限制在 CWE-specific sink/sanitizer/scope filter；若修改共享 `TaintTracking.gdl`，必须执行 11 CWE 全量回归。

## 发布验收入口

```bash
python -m compileall vep/ scripts/evaluation/ scripts/reporting/ scripts/converters/
python scripts/verify_manifest.py
python -m pytest
python scripts/evaluation/run_pipeline.py --tool both --cwe all \
  --stages aggregate,report
```

完整工具回归需增加数据库参数、`run` 阶段和 `--no-skip-existing`。
