# Full Regression Report - macOS fixed DB - 2026-06-18

## Scope

- Commit: `877f5c0 fix(codefuse): prevent macOS builds with invalid JAVA_HOME`
- Platform: macOS arm64
- CodeFuse database: `dataset/codefuse-db-mac-fixed/coref_java_src.db`
- Source: `dataset/benchmark/src/main/java`
- JDK: Homebrew OpenJDK 21 `Contents/Home`
- CWE set: `022, 078, 079, 089, 090, 327, 328, 330, 501, 614, 643`
- CodeFuse completed: `2026-06-18T01:04:27+08:00`

## Execution Status

- Java environment gate: PASS
- Mini probe: PASS
- Fixed Mac DB gate: PASS
- Linux vs fixed Mac DB diff: PASS
- CodeFuse checker execution: 11/11 passed
- FN regression: none

## CodeFuse Summary

| CWE | TP | FP | FN | Precision | Recall | F1 | Outside scope |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| CWE-022 | 133 | 108 | 0 | 0.5519 | 1.0000 | 0.7112 | 0 |
| CWE-078 | 126 | 97 | 0 | 0.5650 | 1.0000 | 0.7221 | 0 |
| CWE-079 | 246 | 96 | 0 | 0.7193 | 1.0000 | 0.8367 | 0 |
| CWE-089 | 272 | 150 | 0 | 0.6445 | 1.0000 | 0.7839 | 0 |
| CWE-090 | 27 | 22 | 0 | 0.5510 | 1.0000 | 0.7105 | 0 |
| CWE-327 | 130 | 27 | 0 | 0.8280 | 1.0000 | 0.9059 | 0 |
| CWE-328 | 128 | 1 | 0 | 0.9922 | 1.0000 | 0.9961 | 1 |
| CWE-330 | 218 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 | 0 |
| CWE-501 | 83 | 34 | 0 | 0.7094 | 1.0000 | 0.8300 | 0 |
| CWE-614 | 36 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 | 0 |
| CWE-643 | 15 | 18 | 0 | 0.4545 | 1.0000 | 0.6250 | 0 |
| **Micro total** | **1414** | **553** | **0** | **0.7189** | **1.0000** | **0.8364** | **1** |

Machine-readable data: [codefuse-full-regression-mac-fixed-2026-06-18.tsv](data/mac-fixed-validation/codefuse-full-regression-mac-fixed-2026-06-18.tsv).

## Comparison

| build | TP | FP | FN | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|
| Linux 2026-06-11 | 1414 | 553 | 0 | 0.7189 | 1.0000 | 0.8364 |
| Old Mac current experiment outputs | 1347 | 545 | 67 | 0.7119 | 0.9526 | 0.8149 |
| Fixed Mac | 1414 | 553 | 0 | 0.7189 | 1.0000 | 0.8364 |

The fixed Mac run matches the Linux CodeFuse baseline. The old Mac FN total was 67; fixed Mac FN total is 0.

## Validation Commands

```bash
python3 scripts/check_codefuse_java_env.py --require-version 21 --require-modules
sparrow database create -s dataset/benchmark/src/main/java -lang java -o dataset/codefuse-db-mac-fixed
python3 scripts/diagnose_codefuse_db_diff.py --db dataset/codefuse-db-mac-fixed/coref_java_src.db --out reports/codefuse-db-mac-fixed-gate.md
python3 scripts/diagnose_codefuse_db_diff.py --linux dataset/codefuse-db-linux/coref_java_src.db --mac dataset/codefuse-db-mac-fixed/coref_java_src.db --out reports/codefuse-db-diff-mac-fixed.md
# godel/checker outputs were written under reports/data/mac-fixed-validation/
```

## Remaining Risks

- The rebuilt DB is a local artifact and is intentionally not committed.
- Linux remains the recommended formal benchmark oracle; fixed Mac is now valid for local cross-checks.
