# 静态分析实验与结果评测流程

本文集中记录 CodeQL、CodeFuse-Query / GodelScript 的实验命令、结果转换和指标评测流程。README 首页只保留短入口，详细命令统一放在这里维护。

## 运行前提

- 在仓库根目录执行命令。
- Python 依赖已安装。
- CodeQL CLI、JDK 17+、CodeFuse/Sparrow CLI 已在本机可用。
- OWASP Benchmark 源码位于 `dataset/benchmark`。

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## CodeQL 实验示例

### 构建数据库

```bash
codeql database create owasp-benchmark-db \
  --language=java \
  --source-root=dataset/benchmark \
  --command="mvn clean package -DskipTests -Dspotless.skip=true"
```

### 执行规则检测

```bash
codeql database analyze owasp-benchmark-db \
  rules/codeql-query/CWE-xxx \
  --format=sarifv2.1.0 \
  --output=experiments/cwe-xxx/results/codeql/cwexxx.sarif
```

## CodeFuse-Query / GodelScript 实验示例

### macOS CodeFuse Java Environment Gate

macOS 上构建 CodeFuse/Sparrow Java DB 前，先确认 `JAVA_HOME` 指向真实 JDK
`Contents/Home`，而不是 Homebrew keg prefix。背景和修复步骤见
[codefuse_macos_jdk_setup.md](codefuse_macos_jdk_setup.md)。

```bash
python3 scripts/check_codefuse_java_env.py --require-version 21 --require-modules
```

该 gate 必须 PASS 后再执行 `sparrow database create`。

### 推荐方式：统一 pipeline（Phase 3 起）

主线入口是 `scripts/evaluation/run_pipeline.py`：manifest 驱动，一条命令完成
工具执行 → 标准化 → v2 评估 → 聚合（→ 报告）。

```bash
# 全量 11 个 checker（CodeFuse）；DB 路径按机器指定
python3 scripts/evaluation/run_pipeline.py --tool codefuse --cwe all \
  --db dataset/codefuse-db-mac-fixed

# 全量 CodeQL 评估（SARIF 已存在时无需 --db 工具运行）
python3 scripts/evaluation/run_pipeline.py --tool codeql --cwe all \
  --stages evaluate,aggregate,report

# 单个 CWE 调试
python3 scripts/evaluation/run_pipeline.py --tool codefuse --cwe 022
```

输出位置（v2 口径）：

```text
experiments/cwe-<ID>/results/codefuse-query/checker<ID>.json
experiments/cwe-<ID>/results/codefuse-query/cwe<ID>_codefuse.csv
experiments/cwe-<ID>/eval/codefuse_eval_v2/metrics.json   # + tp/fp/fn/outside_scope.csv
reports/data/metrics_v2_codefuse_all.json                 # 聚合（vep.aggregate.v2）
reports/report.md                                         # --stages 含 report 时
```

兼容 wrapper：`./scripts/evaluation/eval_checker.sh <ID>`（单 CWE，等价于
`run_pipeline.py --tool codefuse --cwe <ID> --stages run,evaluate`，可用 `DB_DIR` 覆盖数据库）。
更完整的说明见 [run_codefuse_queries.md](run_codefuse_queries.md)。

### 手动构建数据库

```bash
python3 scripts/check_codefuse_java_env.py --require-version 21 --require-modules

sparrow database create \
  -s dataset/benchmark/src/main/java \
  -lang java \
  -o dataset/codefuse-db \
  -overwrite
```

### 手动执行规则检测

主线 checker 命名为 `checker<ID>.gdl`：

```bash
sparrow query run \
  -d dataset/codefuse-db \
  -gdl rules/codefuse-query/CWE-022/checker022.gdl \
  -o experiments/cwe-022/results/codefuse-query
```

执行后通常会在输出目录生成 JSON 结果：

```text
experiments/cwe-022/results/codefuse-query/checker022.json
```

早期 CWE-022 调试规则已归档在 `rules/codefuse-query/CWE-022/analysis-and-backup/`，例如：

```text
rules/codefuse-query/CWE-022/analysis-and-backup/checker_taint_no_fallback.gdl
rules/codefuse-query/CWE-022/analysis-and-backup/checker_taint_no_fallback_debug.gdl
rules/codefuse-query/CWE-022/analysis-and-backup/sourcefinder.gdl
rules/codefuse-query/CWE-022/analysis-and-backup/sinkfinder.gdl
```

这些文件适合追溯早期定位过程，不作为当前主线 checker 入口。

## 结果分析

以下为 pipeline 内部使用的底层步骤，仅在需要单步调试时手动执行。

### CodeQL：SARIF 转 CSV

```bash
python scripts/converters/sarif_to_csv.py
```

`sarif_to_csv.py` 当前使用脚本内固定输入输出路径，运行前需要按目标 CWE 修改脚本顶部路径常量。详细脚本说明见 [../../scripts/README.md](../../scripts/README.md)。

### CodeFuse：JSON 转 CSV

```bash
python scripts/converters/codefuse_json_to_csv.py \
  experiments/cwe-022/results/codefuse-query/checker022.json \
  experiments/cwe-022/results/codefuse-query/cwe022_codefuse.csv \
  --include-reason
```

### 单 CWE 评测（CodeFuse）

```bash
python scripts/evaluation/eval_codefuse_results.py \
  --expected expectedresults-1.2.csv \
  --results experiments/cwe-022/results/codefuse-query/cwe022_codefuse.csv \
  --cwe CWE-022 \
  --outdir experiments/cwe-022/eval/codefuse \
  --format csv \
  --fp-mode all_non_gt
```

### 汇总统计结果（多 CWE）

```bash
python scripts/evaluation/aggregate_results.py
```

### 生成图表与报告

```bash
python scripts/reporting/plots_metrics.py
python scripts/reporting/generate_report.py
```

实验统计结果将输出至：

```text
reports/
```

## 自动评估流程

主线入口（CodeFuse / CodeQL / both，manifest 驱动）：

```bash
python3 scripts/evaluation/run_pipeline.py --tool codefuse --cwe all \
  --db dataset/codefuse-db-mac-fixed
```

兼容 wrapper（旧入口保留，内部已转发 pipeline）：

```bash
./run_eval.sh          # CodeQL：SARIF 预检查 + evaluate,aggregate,report
./scripts/evaluation/eval_checker.sh 022   # CodeFuse 单 CWE
```

脚本级终端 / VSCode 详细用法见 [../../scripts/README.md](../../scripts/README.md)。

## 当前同步说明

- 评估主线为 `scripts/evaluation/run_pipeline.py`（Phase 3 起）；旧评估脚本
  （`eval_codefuse_results.py` / `aggregate_results.py` / `generate_report.py`）保留但不再是主线。
- `scripts/run_codeql_experiments.py` 自 Phase 3 M3.4 起标记 deprecated，将由 pipeline 取代。
- `rules/codefuse-query/CWE-022` 当前主线规则为 `checker022.gdl`。
- CWE-022 早期调试规则和辅助定位脚本已归档到 `analysis-and-backup/`。
- CodeFuse JSON 转 CSV 工具为 `scripts/converters/codefuse_json_to_csv.py`。
- `scripts/README.md` 保留每个脚本的中文终端示例和 VSCode 用法。
