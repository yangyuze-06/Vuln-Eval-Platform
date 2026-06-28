# Cross-platform Evaluation Comparison

## Inputs

- **Left (v2b)**: `experiments/cwe-022/eval/codefuse_eval_v2b`
- **Right (v2)**: `experiments/cwe-022/eval/codefuse_eval_v2`
- **Ground Truth**: `None`
- **CWE**: CWE-022

## Metrics Diff

| Metric | v2b | v2 | Diff |
|--------|---------|---------|------|
| tp | 120 | 120 | +0 |
| fp | 108 | 108 | +0 |
| fn | 13 | 13 | +0 |
| precision | 0.5263 | 0.5263 | +0.0000 |
| recall | 0.9023 | 0.9023 | +0.0000 |
| f1 | 0.6648 | 0.6648 | +0.0000 |

## TP Set Diff

- **v2b count**: 120
- **v2 count**: 120
- **Common**: 120

## FP Set Diff

- **v2b count**: 108
- **v2 count**: 108
- **Common**: 108

## FN Set Diff

- **v2b count**: 13
- **v2 count**: 13
- **Common**: 13

## OUTSIDE_SCOPE Set Diff

- **v2b count**: 0
- **v2 count**: 0
- **Common**: 0

## Suspect Testcases

✅ No suspect testcases found (results match)

## Initial Diagnosis

✅ **Status**: Results are consistent across platforms
