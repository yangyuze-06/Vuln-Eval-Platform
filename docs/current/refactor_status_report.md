# 重构推进整理报告

生成时间：2026-08-31（第三版；首版 2026-06-28，二版 2026-08-30）

> 本版与二版的主要差异：**Phase 3（P2 统一入口）与 Phase 4（P3 测试体系）全部完成**，
> v2 正式接管全部评估入口，`roadmap.md` 的 M5 里程碑达成。旧版全文见 git 历史。

## 结论

重构主线（规则包模块化 + 评估核心 v2 化 + 报告系统 v2 化 + 统一实验入口 + 测试体系）**全部完成**。当前状态：

- Phase 1：CWE manifest 统一索引 + 只读验证层 ✅
- Phase 2（A/B/C/D/F）：评估核心 v2 + 双工具报告 ✅
- Phase 3（M3.1~M3.4）：工具抽象层 + `run_pipeline.py` 统一入口，parity gate 通过，旧入口降级 wrapper ✅
- Phase 4（M4.1~M4.5）：pytest 体系 149 个测试、golden fixtures（含 `328S` 口径守卫）、GitHub Actions CI、文档同步 ✅
- 规则包侧 11 个 checker 全量回归 Recall = 1.0000；CWE-328/330/614 三个满分 checker
- 剩余主线：**P4 规则精度研究**（降 FP），工程侧已无阻塞性欠账

## 重构时间线

| 时间 | 事件 |
|---|---|
| 2026-04-26 ~ 04-29 | 首批 GDL checker，docs 建立 |
| 2026-06-11 | Phase 1 + Phase 2A/2B/2C/2D 单日完成（评估核心 v2 全套） |
| 2026-06-18 | 定位并修复 macOS CodeFuse Java DB 根因（JAVA_HOME keg prefix），全量回归对齐 Linux baseline |
| 2026-06-28 | docs 结构重组，首版重构状态报告 |
| 2026-07-04 | P1 完成：模块化 V2 报告系统（Phase 2F） |
| 2026-08-30 | 状态整理，制定 Phase 3 计划 |
| 2026-08-31 | **Phase 3 完成**（工具抽象、统一 pipeline、parity gate、旧入口降级）；**Phase 4 完成**（测试体系、golden、CI） |

## Phase 3 交付明细（见 `docs/refactor/PHASE3_PLAN.md`）

- M3.1 `configs/tools.yml` + 路径发现 + 环境门禁（JAVA_HOME gate 复用现有脚本，实测拦截坏 keg prefix）
- M3.2 `vep/core/manifest.py` + CodeFuse/CodeQL runner 与标准化
- M3.3 `vep/pipeline.py` + `scripts/evaluation/run_pipeline.py`（manifest 驱动，stages 可拆分）
- M3.4 parity gate：11/11 findings 逐字节一致；CWE-328 口径差异根因定位并修正
  （ground truth `328S` 行应计入 CWE-328，旧 evaluator 的 outside-scope FP 属口径偏差，
  见 `docs/audits/PARITY_M34_CODEFUSE_PIPELINE.md`）；`run_eval.sh` / `eval_checker.sh` 降级 wrapper

## Phase 4 交付明细（见 `docs/refactor/PHASE4_PLAN.md`）

- M4.1 pytest 基础设施（`pytest.ini`、`tests/python/`）+ core 单元测试（normalization / manifest）
- M4.2 evaluation 单元测试：findings / ground_truth / evaluator / metrics / sarif / aggregate，
  覆盖两种 fp_mode、outside-scope 语义、聚合求和口径
- M4.3 tools 测试：路径发现五级优先级、fake godel/codeql 端到端（含 package-root 合并验证）、JAVA 门禁映射
- M4.4 pipeline golden 测试：提交级 fixtures（mini benchmark）+ golden JSON；
  **`328S` scope 守卫测试**防止口径再次漂移；CLI 错误路径与 skip_existing 语义固化
- M4.5 GitHub Actions CI（Python 3.9/3.11 矩阵：compileall + verify_manifest + pytest）+
  guides / README 同步到 pipeline 主线

测试规模：**149 个测试，全绿，约 4 秒**，不依赖真实 godel/CodeQL/数据库，可在任何机器与 CI 运行。

## 当前基线（2026-08-31，v2 口径，CodeFuse 全量回归）

| 指标 | TP | FP | FN | TN | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Overall | 1415 | 552 | 0 | 773 | 0.7194 | 1.0000 | 0.8368 |

- 机器可读基线：`reports/data/metrics_v2_codefuse_all.json`（CodeFuse）、`metrics_v2_codeql_all.json`（CodeQL，P=0.3876 / R=1.0000）
- 分 CWE 明细：`docs/current/results.md`
- FP 最重的 checker（P4 研究对象）：CWE-643（P=0.4545，18 FP）、CWE-090（0.5510，22 FP）、
  CWE-022（0.5519，108 FP）、CWE-078（0.5650，97 FP）、CWE-089（0.6445，150 FP）——合计占全部 FP 的 71%

## 当前未完成 / 风险点

### 1. 规则精度研究未启动（P4，唯一剩余主线）

约束不变：patch 只进 CWE-specific sink/sanitizer/scope filter 模块，不动 `TaintTracking.gdl`；
每个 patch 报告 TP/FP/FN/P/R/F1 并跑 `run_pipeline.py --tool codefuse --cwe all` 全量回归
（现在有 149 个测试 + CI 护航）。

### 2. CodeQL database create 未自动化

pipeline 校验 DB 存在并报错，但不负责建库。低优先级。

### 3. Linux 侧工具发现未实测

`vep/tools` 的发现逻辑平台中立，M3/M4 全部验证在 mac 完成。下次在 Linux 机器跑
`run_pipeline.py --tool codefuse --cwe 090 --stages run,evaluate` 即可补验。

### 4. 遗留清理项

- `scripts/run_codeql_experiments.py` 已标记 deprecated，按计划在一个版本周期后删除。
- `reports/data/metrics.json` 等旧流程产物仍在（旧报告脚本 `generate_report.py` 保留兼容）。

## 路线图盘点

### 规则包路线（`docs/current/roadmap.md`）

**M1~M5 全部达成**：M5（具备回归、封装和技术报告的稳定 rule pack）自 Phase 4 起成立——
回归 = pytest + golden + CI + pipeline 全量回归命令；封装 = manifest/tools.yml 配置层 + 统一入口 + 文档；
技术报告 = v2 报告系统 + `docs/current/results.md`。

### 重构路线（P0~P4）

| 阶段 | 内容 | 状态 |
|---|---|---|
| P0 | 冻结稳定基线 | ✅ 完成（2026-06） |
| P1 | 报告系统接 v2 | ✅ 完成（2026-07-04） |
| P2 | 统一实验入口 | ✅ 完成（2026-08-31） |
| P3 | 测试体系 / golden regression | ✅ 完成（2026-08-31） |
| P4 | 规则精度研究（降 FP） | ⬜ 未开始（唯一剩余主线） |

## 建议下一步：P4 规则精度研究

- 对象（按 FP 量级）：CWE-022（108）、CWE-089（150）、CWE-078（97）、CWE-090（22）、CWE-643（18）。
- 方法：逐 FP 审计 `fp.csv`，patch 限定在 CWE-specific sink/sanitizer/scope filter；
  每个 patch 必须报告 TP/FP/FN/P/R/F1 并通过全量回归 + 测试套件。
- 长期方向（`roadmap.md`）：strong update、collection/key sensitivity、path sensitivity、
  field/context sensitivity、可解释 taint 路径——均属 `TaintTracking.gdl` 级别改动，需单独立项并全量回归。

## 参考文件

- `docs/refactor/PHASE3_PLAN.md` / `PHASE4_PLAN.md`
- `docs/audits/PARITY_M34_CODEFUSE_PIPELINE.md`（CWE-328 口径审计）
- `docs/refactor/PHASE1_SUMMARY.md` / `PHASE2_FINAL_SUMMARY.md`
- `docs/current/architecture.md` / `results.md` / `roadmap.md`
- `reports/data/metrics_v2_codefuse_all.json` / `metrics_v2_codeql_all.json`（机器可读基线）
