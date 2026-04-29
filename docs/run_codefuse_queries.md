# Running Modular CodeFuse-Query Checkers

The modular Java checkers import both the official CodeFuse schema modules and
the repository-local security modules under `rules/codefuse-query/lib`.

Use the evaluation runner:

```bash
./scripts/evaluation/eval_checker.sh 089
./scripts/evaluation/eval_checker.sh 022
./scripts/evaluation/eval_checker.sh 078
./scripts/evaluation/eval_checker.sh 079
```

The runner executes the underlying `godel` binary directly and writes the JSON
output to the existing path:

```text
experiments/cwe-<ID>/results/codefuse-query/checker<ID>.json
```

Equivalent command shape used by the runner:

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
