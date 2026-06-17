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

### 推荐方式：统一 runner

当前主线推荐使用 `eval_checker.sh` 运行单个 CWE。runner 会负责执行 GodelScript checker、生成 JSON、转换 CSV，并输出 TP / FP / FN / metrics。

```bash
./scripts/evaluation/eval_checker.sh 022
./scripts/evaluation/eval_checker.sh 089
```

输出位置：

```text
experiments/cwe-<ID>/results/codefuse-query/checker<ID>.json
experiments/cwe-<ID>/results/codefuse-query/cwe<ID>_codefuse.csv
experiments/cwe-<ID>/eval/codefuse_eval/metrics.json
experiments/cwe-<ID>/eval/codefuse_eval/tp.csv
experiments/cwe-<ID>/eval/codefuse_eval/fp.csv
experiments/cwe-<ID>/eval/codefuse_eval/fn.csv
```

更完整的 runner 说明见 [run_codefuse_queries.md](run_codefuse_queries.md)。

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

### CodeQL：SARIF 转 CSV

```bash
python scripts/converters/sarif_to_csv.py
```

`sarif_to_csv.py` 当前使用脚本内固定输入输出路径，运行前需要按目标 CWE 修改脚本顶部路径常量。详细脚本说明见 [../scripts/README.md](../scripts/README.md)。

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

完整自动评估入口：

```bash
./run_eval.sh
```

脚本级终端 / VSCode 详细用法见 [../scripts/README.md](../scripts/README.md)。

## 当前同步说明

- `rules/codefuse-query/CWE-022` 当前主线规则为 `checker022.gdl`。
- CWE-022 早期调试规则和辅助定位脚本已归档到 `analysis-and-backup/`。
- CodeFuse JSON 转 CSV 工具为 `scripts/converters/codefuse_json_to_csv.py`。
- `scripts/README.md` 保留每个脚本的中文终端示例和 VSCode 用法。
