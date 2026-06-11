# Full Regression Report - 2026-06-11

## Scope

- Commit: `4660061c42fec09e7a12d831d2f726983b6ee35a`
- Branch: `main`
- Platform: Linux `6.17.0-23-generic`, x86_64
- Filesystem: case-sensitive
- CodeFuse database: `dataset/codefuse-db`
- CodeQL database: `dataset/codeql-db`
- CodeQL CLI/database version: `2.23.9`
- CWE set: `022, 078, 079, 089, 090, 327, 328, 330, 501, 614, 643`
- CodeFuse completed: `2026-06-12T00:03:52+08:00`
- CodeQL completed: `2026-06-12T00:47:56+08:00`

## Execution Status

- CodeFuse checker execution: 11/11 passed
- CodeQL database analyze: 11/11 passed
- CodeQL SARIF v2 evaluation: 11/11 passed
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

Machine-readable data: [codefuse-full-regression-2026-06-11.tsv](data/codefuse-full-regression-2026-06-11.tsv).

## CodeQL Summary

| CWE | TP | FP all | FP in scope | FN | Precision all | Recall | F1 all | Outside scope |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| CWE-022 | 133 | 67 | 66 | 0 | 0.6650 | 1.0000 | 0.7988 | 1 |
| CWE-078 | 126 | 64 | 64 | 0 | 0.6632 | 1.0000 | 0.7975 | 0 |
| CWE-079 | 246 | 1475 | 90 | 0 | 0.1429 | 1.0000 | 0.2501 | 1385 |
| CWE-089 | 272 | 207 | 207 | 0 | 0.5678 | 1.0000 | 0.7244 | 0 |
| CWE-090 | 27 | 13 | 13 | 0 | 0.6750 | 1.0000 | 0.8060 | 0 |
| CWE-327 | 130 | 189 | 27 | 0 | 0.4075 | 1.0000 | 0.5791 | 162 |
| CWE-328 | 129 | 190 | 33 | 0 | 0.4044 | 1.0000 | 0.5759 | 157 |
| CWE-330 | 218 | 0 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 | 0 |
| CWE-501 | 83 | 24 | 24 | 0 | 0.7757 | 1.0000 | 0.8737 | 0 |
| CWE-614 | 36 | 0 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 | 0 |
| CWE-643 | 15 | 7 | 7 | 0 | 0.6818 | 1.0000 | 0.8108 | 0 |
| **Micro total** | **1415** | **2236** | **531** | **0** | **0.3876** | **1.0000** | **0.5586** | **1705** |

Using only in-scope FP, CodeQL micro precision is `0.7271` and micro F1 is
`0.8420`.

Machine-readable data: [codeql-full-regression-2026-06-11.tsv](data/codeql-full-regression-2026-06-11.tsv).

## Findings

1. The previous run only aggregated existing CodeQL CSV files. This run
   actually executed all CodeQL queries with `--rerun`.
2. All 11 newly generated CodeQL result sets are semantically identical to the
   existing March 2026 SARIF result sets. No analyzer drift was found.
3. The legacy aggregate's `FP=531` equals the new evaluator's total
   `fp_in_scope=531`. The larger `all_non_gt` value includes 1,705 findings
   outside each target CWE scope.
4. CWE-079 contributes 1,385 outside-scope CodeQL findings.
5. CWE-327 and CWE-328 contain byte-identical query files and generate
   byte-identical SARIF findings. They are not distinct checker models.
6. The v2 evaluator maps the single `CWE-328S` ground-truth row into CWE-328,
   producing 129 positives. The legacy/CodeFuse path reports 128.

CodeQL result hashes: [codeql-sarif-semantic-hashes-2026-06-11.tsv](data/codeql-sarif-semantic-hashes-2026-06-11.tsv).

Environment fingerprint: [env-fingerprint-linux-2026-06-11.json](data/env-fingerprint-linux-2026-06-11.json).

## Validation Commands

```bash
for cwe in 022 078 079 089 090 327 328 330 501 614 643; do
  bash scripts/evaluation/eval_checker.sh "$cwe"
done

codeql database analyze dataset/codeql-db rules/codeql-query/CWE-022 \
  --rerun --no-download \
  --format=sarifv2.1.0 \
  --output=experiments/full-regression-2026-06-11/codeql/sarif/cwe022.sarif \
  --threads=0

.venv/bin/python scripts/evaluation/eval_sarif_findings.py \
  --sarif experiments/full-regression-2026-06-11/codeql/sarif/cwe022.sarif \
  --ground-truth expectedresults-1.2.csv \
  --tool codeql \
  --cwe CWE-022 \
  --out experiments/full-regression-2026-06-11/codeql/eval/cwe-022/metrics.json \
  --fp-mode all_non_gt
```

## Remaining Risks

- Both static-analysis databases were reused rather than rebuilt.
- No macOS result bundle was available for a real Linux/macOS comparison.
- CodeQL and CodeFuse are not directly comparable until CWE-328S mapping,
  deduplication, and FP-scope policies are unified.
- Raw SARIF, per-finding CSV, and command logs remain under the ignored local
  `experiments/full-regression-2026-06-11/` directory.
