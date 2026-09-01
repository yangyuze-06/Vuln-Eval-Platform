# V3 统一评估流程

## 1. 准备

```bash
source .venv/bin/activate
pip install -r requirements.txt
python scripts/verify_manifest.py
```

运行 CodeFuse 前确认真实 JDK Home：

```bash
export JAVA_HOME="/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home"
export PATH="$JAVA_HOME/bin:$PATH"
python scripts/check_codefuse_java_env.py
```

工具发现顺序为 CLI > 环境变量 > `configs/tools.yml` > PATH > 内置候选。

## 2. 完整运行

```bash
python scripts/evaluation/run_pipeline.py --tool codefuse --cwe all \
  --db dataset/codefuse-db-mac-fixed \
  --stages run,evaluate,aggregate,report \
  --no-skip-existing --keep-going

python scripts/evaluation/run_pipeline.py --tool codeql --cwe all \
  --db dataset/codeql-db/benchmark-java \
  --stages run,evaluate,aggregate,report \
  --no-skip-existing --keep-going
```

`--no-skip-existing` 表示真正重跑；默认发现已有 `metrics.json` 时跳过该 CWE。

## 3. 仅重新评估 normalized CSV

```bash
python scripts/evaluation/run_pipeline.py --tool both --cwe all \
  --stages evaluate,aggregate,report --no-skip-existing
```

输入位置：

```text
experiments/cwe-<ID>/results/codefuse-query/cwe<ID>_codefuse.csv
experiments/cwe-<ID>/results/codeql/cwe<ID>.csv
```

只有 SARIF 时先转换并评估：

```bash
python scripts/evaluation/eval_sarif_findings.py \
  --sarif experiments/cwe-328/results/codeql/cwe328.sarif \
  --ground-truth expectedresults-1.2.csv \
  --tool codeql --cwe CWE-328 \
  --out experiments/cwe-328/eval/codeql_eval_v2/metrics.json \
  --csv-out experiments/cwe-328/results/codeql/cwe328.csv
```

## 4. 仅聚合和生成报告

```bash
python scripts/evaluation/run_pipeline.py --tool both --cwe all \
  --stages aggregate,report
```

输出：

```text
experiments/cwe-<ID>/eval/<tool>_eval_v2/metrics.json
experiments/cwe-<ID>/eval/<tool>_eval_v2/tp.csv
experiments/cwe-<ID>/eval/<tool>_eval_v2/fp.csv
experiments/cwe-<ID>/eval/<tool>_eval_v2/fn.csv
experiments/cwe-<ID>/eval/<tool>_eval_v2/outside_scope.csv
reports/data/metrics_v2_codefuse_all.json
reports/data/metrics_v2_codeql_all.json
reports/report.md / report_zh.md / figs/
reports/codefuse/ / reports/codeql/
```

## 5. 调试与兼容入口

```bash
python scripts/evaluation/run_pipeline.py --tool codefuse --cwe 022 \
  --db dataset/codefuse-db-mac-fixed --no-skip-existing

./run_eval.sh
./scripts/evaluation/eval_checker.sh 022
```

旧入口是 wrapper；主线入口始终是 `run_pipeline.py`。
