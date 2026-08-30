# 运行模块化 CodeFuse-Query Checker

> **Phase 3 起**：主线入口为 `scripts/evaluation/run_pipeline.py`（见
> [evaluation_workflow.md](evaluation_workflow.md)）。本文描述的 `eval_checker.sh`
> 现在是兼容 wrapper（内部转发 pipeline，产物目录为 `codefuse_eval_v2`），
> 下文的手工 godel 命令仍可用于理解底层调用形态。

模块化 Java checker 同时依赖官方 CodeFuse schema 模块，以及仓库本地的安全规则模块：

```text
rules/codefuse-query/lib
```

## 推荐方式

使用统一评测 runner：

```bash
./scripts/evaluation/eval_checker.sh 089
./scripts/evaluation/eval_checker.sh 022
./scripts/evaluation/eval_checker.sh 078
./scripts/evaluation/eval_checker.sh 079
./scripts/evaluation/eval_checker.sh 328
./scripts/evaluation/eval_checker.sh 501
```

runner 会直接调用底层 `godel` 可执行文件，并输出 JSON 到固定路径：

```text
experiments/cwe-<ID>/results/codefuse-query/checker<ID>.json
```

随后 runner 会把 JSON 转换为 CSV，并调用 evaluator 生成：

```text
experiments/cwe-<ID>/eval/codefuse_eval/metrics.json
experiments/cwe-<ID>/eval/codefuse_eval/tp.csv
experiments/cwe-<ID>/eval/codefuse_eval/fp.csv
experiments/cwe-<ID>/eval/codefuse_eval/fn.csv
```

## runner 使用的等价命令形态

```bash
GODEL_BIN=/home/ubuntu64/tools/static-analysis-tools/codefuse/sparrow-cli-2.1.0.linux/sparrow-cli/godel-script/usr/bin/godel
OFFICIAL_LIB=/home/ubuntu64/tools/static-analysis-tools/codefuse/sparrow-cli-2.1.0.linux/sparrow-cli/lib
LOCAL_LIB="$PWD/rules/codefuse-query/lib"
DB_ROOT="$PWD/dataset/codefuse-db"
CHECKER="$PWD/rules/codefuse-query/CWE-089/checker089.gdl"
OUTPUT_JSON="$PWD/experiments/cwe-089/results/codefuse-query/checker089.json"

TMP_PACKAGE_ROOT="$(mktemp -d)"
cp -R "$OFFICIAL_LIB/." "$TMP_PACKAGE_ROOT/"
cp -R "$LOCAL_LIB/." "$TMP_PACKAGE_ROOT/"

"$GODEL_BIN" \
  -p "$TMP_PACKAGE_ROOT" \
  -f "$DB_ROOT" \
  -Of \
  -r "$CHECKER" \
  --output-json "$OUTPUT_JSON"
```

## 注意事项

- Godel 2.1.0 对 package root 的处理较严格，因此 runner 会临时合并官方 lib 和本地 lib。
- 新 checker 应优先通过 `eval_checker.sh` 运行，避免手工命令遗漏 package root workaround。
- 如果 query 能生成 JSON 但 evaluator 失败，优先检查 CWE 编号、CSV 转换结果和 ground truth 支持情况。
