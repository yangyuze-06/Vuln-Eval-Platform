# Phase 4 计划：测试体系与 CI

> **文档状态：已完成并归档（2026-08-31）。** 当前 V3 状态见 `docs/current/refactor_status_report.md`。


创建时间：2026-08-31
前置阶段：Phase 1 ✅ / Phase 2（A~D, F）✅ / Phase 3（M3.1~M3.4）✅（2026-08-31，parity gate 通过）
对应重构路线：`docs/current/refactor_status_report.md` 中的 **P3 测试体系 / golden regression**
预计工作量：7~10 小时

## 1. 背景与目标

Phase 3 完成后，仓库的所有评估入口已统一到 `run_pipeline.py`，但验证手段仍然只有：
手动命令、`compileall`、全量回归报告。Phase 3 开发中暴露的两个缺陷
（`build_rows` 漏传 `unknown_label`、`_discover_paths` 返回值解包错误）都是人工冒烟发现的——
这正是缺测试体系的代价。

Phase 4 的目标：

1. 为 `vep/` 全部公共模块建立 pytest 单元测试；
2. 用**golden fixtures** 固化 pipeline 评估语义，特别是 **CWE-328 `328S` scope 口径**（防止漂移）；
3. 建立 CI 入口（compileall + manifest 验证 + pytest）；
4. 把 guides/README 同步到 pipeline 主线（消除 Phase 3 遗留的文档漂移）。

**明确不做的事：**
- 不改任何 `.gdl` 规则与 `TaintTracking.gdl`；
- 不改 `vep/` 生产代码行为（测试中若发现 bug，单独修复并在 commit message 中说明）；
- 不做性能测试、不做 coverage 门禁（后续可选）。

## 2. Phase 3 review 结论（本计划的输入）

验收标准全部达成，parity gate 通过。遗留事项按优先级：

| 优先级 | 发现 | 处理 |
|---|---|---|
| P2 | 文档漂移：`docs/guides/*` 与根 `README.md` 仍以旧入口为主线 | M4.5 文档同步 |
| P3 | `Manifest.resolve()` 不去重（`--cwe 022 022` 跑两遍） | M4.1 测试固化现状；如修红单独 commit |
| P3 | `--stages run` 单独使用时 `skip_existing` 以 metrics.json 存在为准跳过工具运行 | 测试固化现状 |
| P3 | `--stages report` 不能独立使用已有聚合文件 | 测试固化现状（guard 行为） |
| 信息 | Linux 侧工具发现未实测；`run_codeql_experiments.py` 待一个周期后删除 | 维持已知项 |

## 3. 交付物

### 3.1 测试基础设施（M4.1）

- `requirements.txt` 增加 `pytest`。
- `pytest.ini`：`testpaths = tests/python`（与 `tests/codefuse-query/` 的 benchmark 数据隔离）。
- `tests/python/conftest.py`：注入项目根到 `sys.path`。
- `tests/python/test_normalization.py`：`normalize_cwe_id` / `short_cwe_id` /
  `normalize_testcase_id` / `safe_int` / `normalize_truth_value` 全分支。
- `tests/python/test_manifest.py`：manifest 加载、`resolve("all"/id/slug)`、未知 token 报错、
  CWE-328 的 CodeQL 目录特例（`CWE-328_328S`）。

### 3.2 evaluation 模块单元测试（M4.2）

- `test_findings.py`：4 列（CodeQL 旧格式）与 5 列（CodeFuse 含 reason）CSV 加载；
  testcase 缺失时从 file 列提取。
- `test_ground_truth.py`：CWE 过滤、**`328S → CWE-328` 归一化（口径守卫）**、
  模糊真值跳过、文件缺失报错。
- `test_evaluator.py`：合成小型用例断言 TP/FP/FN/TN/P/R/F1/FNR/FPR/FDR；
  `fp_mode=all_non_gt` 与 `in_scope` 的语义差异；outside-scope 归类；detail 行数。
- `test_metrics.py`：`eval_result_to_dict` 字段与 `schema_version`；metrics/details 写盘 roundtrip。
- `test_sarif.py`：最小 SARIF → `load_sarif_findings` → `write_findings_csv` →
  `load_findings_csv` 往返一致。
- `test_aggregate.py`：overall 按 TP/FP/FN 求和（非平均）；strict 模式混合 fp_mode 报错；写盘。

### 3.3 tools 模块单元测试（M4.3）

- `test_config.py`：`load_tools_config` 默认值/缺文件/覆盖；`discover_codefuse` 五级优先级
  （CLI > env > config > PATH-sparrow > 内置候选，用 monkeypatch 控制 env 与 PATH）；
  `discover_codeql` 三种形态（PATH 名 / 绝对路径 / 找不到）。
- `test_codefuse.py`：
  - `check_environment`：假 sparrow home（tmp 目录伪造 `godel-script/usr/bin/godel` + `lib/`）
    下各失败分支；`env_checks.codefuse_java_env=false` 跳过 JAVA 门禁。
  - `run()`：**fake godel 可执行脚本**（shell 脚本把 `-p` package root 拷到检查点并写出 JSON），
    验证命令拼装、package root 合并（官方 lib + 本地 lib 同时存在）、JSON 落盘与 ToolRunResult。
  - `standardize()`：构造 JSON → CSV，与 `codefuse_json_to_csv.py` 直跑结果逐字节一致。
  - `run_java_env_gate`：monkeypatch subprocess（exit 0/1/2 + JSON 明细）映射为问题清单。
- `test_codeql.py`：fake codeql 脚本写出最小 SARIF → `run()` → `standardize()` 往返；
  `check_environment` 找不到 CLI 的报错。

### 3.4 pipeline golden 集成测试（M4.4）

- `tests/python/fixtures/mini_benchmark/`：提交到 git 的小型切片——
  迷你 ground truth（含一行 `328S`）、两个 CWE 的 findings CSV（CodeFuse 5 列 / CodeQL 4 列）、
  期望 metrics/aggregate golden JSON。
- `test_pipeline_golden.py`：
  - 进程内调用 `run_pipeline(stages=evaluate,aggregate)` 于 fixture manifest + tmp experiments 目录，
    输出与 golden JSON 完全一致；
  - **`328S` scope 守卫**：断言该样本计入 TP（防止口径再次漂移）；
  - CLI 行为：未知 CWE token → exit 2；非法 stage → exit 2；`--tool both --db` → exit 2；
  - `skip_existing` 语义与 `--no-skip-existing`。

### 3.5 CI 与文档同步（M4.5）

- `.github/workflows/ci.yml`：push/PR 触发；Python 3.9 + 3.11 矩阵；
  步骤：`pip install -r requirements.txt` → `compileall` → `verify_manifest.py` → `pytest`。
- 文档同步（消除 Phase 3 遗留漂移）：
  - `docs/guides/evaluation_workflow.md`：主线改为 `run_pipeline.py`，旧入口标注为兼容 wrapper；
  - `docs/guides/how_to_add_checker.md`：验证步骤改为 pipeline 命令；
  - `docs/guides/run_codefuse_queries.md`：标注 wrapper 现状；
  - 根 `README.md`：评测流程段改为 pipeline 用法。

## 4. 里程碑与验收标准

### M4.1 基础设施 + core 测试（~1h）

- 验收：`pytest` 在仓库根可一键运行且全绿；`normalize_*` 与 manifest 分支覆盖完整；
  CWE-328 目录特例有断言。

### M4.2 evaluation 测试（~2h）

- 验收：评估语义（两种 fp_mode、outside-scope、聚合求和）全部有回归断言；
  `328S` ground truth 归一化有专门测试。

### M4.3 tools 测试（~2h）

- 验收：路径发现五级优先级可测试且全绿；fake godel 验证 package root 合并；
  fake codeql 验证 SARIF 往返；JAVA 门禁映射逻辑有断言。

### M4.4 pipeline golden 测试（~1.5h）

- 验收：golden JSON 与 pipeline 输出一致；`328S` 守卫测试通过；
  CLI 错误路径 exit code 正确。全部测试不依赖真实 godel/CodeQL/数据库。

### M4.5 CI + 文档同步（~1h）

- 验收：workflow 语法有效（本地模拟各步骤通过）；guides/README 与现状一致；
  `run_codeql_experiments.py` 的 deprecated 标注仍保留。

## 5. 风险与约束

| 风险 | 缓解 |
|---|---|
| 测试固化了错误语义 | golden 语义以 `docs/audits/PARITY_M34_CODEFUSE_PIPELINE.md` 审计结论为准；328S 守卫测试注释引用该文档 |
| CI 环境缺系统依赖 | 测试不依赖 godel/CodeQL/JDK；requirements 仅纯 Python 包 |
| 测试与实现耦合过紧 | 单元测试面向公共函数签名，不 mock 内部私有调用；golden 面向产物 |
| Python 版本差异（3.9 vs 3.11） | CI 矩阵覆盖；类型注解统一 `Optional/List` 风格 |

## 6. 与整体路线的关系

- 本期完成 = 重构路线 **P3 完成**，`roadmap.md` 的 **M5（具备回归、封装和技术报告的稳定 rule pack）** 达成。
- 之后进入 **P4 规则精度研究**（CWE-643 / 090 / 022 / 078 / 089 降 FP），每个 patch 以
  `run_pipeline.py` 全量回归 + 本期测试体系护航。

## 参考文件

- `docs/current/refactor_status_report.md`（P0~P4 路线与当前状态）
- `docs/audits/PARITY_M34_CODEFUSE_PIPELINE.md`（CWE-328 口径审计结论，golden 语义依据）
- `docs/refactor/PHASE3_PLAN.md`（Phase 3 交付物，测试对象清单）
- `docs/refactor/PHASE2_FINAL_SUMMARY.md`（Phase 4 原始设想与工作量估计）
