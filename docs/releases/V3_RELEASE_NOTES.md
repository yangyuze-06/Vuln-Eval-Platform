# Vuln-Eval-Platform v3.0.0 Release Notes

**Theme:** Unified and Reproducible Evaluation Pipeline

V3 consolidates CodeFuse-Query and CodeQL experiments behind one manifest-driven command. It adds portable tool discovery, environment gates, normalized v2 evaluation, multi-CWE aggregation, combined and standalone bilingual reports, golden regression tests, and CI.

## Highlights

- One pipeline for `run → evaluate → aggregate → report`.
- `--tool codefuse`, `--tool codeql`, and `--tool both`.
- Combined comparison report plus `reports/codefuse/` and `reports/codeql/` standalone reports.
- Resumable execution by default; `--no-skip-existing` forces a fresh run.
- 11 Java SAST checkers with Recall 1.0000 on the committed baseline.
- CWE-328 `328S` ground-truth semantics protected by a golden test.
- Python 3.9/3.11 GitHub Actions coverage.

## Baseline (`all_non_gt`)

| Tool | TP | FP | FN | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|
| CodeFuse-Query | 1415 | 552 | 0 | 0.7194 | 1.0000 | 0.8368 |
| CodeQL | 1415 | 2236 | 0 | 0.3876 | 1.0000 | 0.5586 |

## Upgrade

```bash
source .venv/bin/activate
pip install -r requirements.txt
python scripts/verify_manifest.py
python -m pytest

python scripts/evaluation/run_pipeline.py --tool both --cwe all \
  --stages aggregate,report
```

For a fresh tool run, add the database overrides and `--no-skip-existing`.

## macOS JAVA_HOME

CodeFuse/Sparrow requires a real JDK Home. A Homebrew keg prefix such as `/opt/homebrew/opt/openjdk@17` is insufficient.

```bash
export JAVA_HOME="/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home"
export PATH="$JAVA_HOME/bin:$PATH"
python scripts/check_codefuse_java_env.py
```

## Compatibility and known limits

- `vep.eval.v2` and `vep.aggregate.v2` schemas are unchanged.
- `run_eval.sh` and `eval_checker.sh` remain compatibility wrappers.
- Pipeline evaluate-only mode consumes normalized CSV, not raw SARIF alone.
- `--aggregate-name` is intentionally unavailable with `--tool both`; default per-tool names prevent collisions.
- Precision optimization is deferred to V3.x and does not block this release.
