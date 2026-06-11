# CWE-328 Godel Checker Analysis

## 1. Metrics Summary

指标来自 `experiments/cwe-328/eval/codefuse_eval/metrics.json`。

| Metric | Value |
|---|--:|
| Raw alerts | 129 |
| Dedup alerts | 129 |
| TP | 128 |
| FP | 1 |
| FN | 0 |
| Precision | 0.9922 |
| Recall | 1.0000 |
| FNR | 0.0000 |
| FPR | 0.0093 |
| FDR | 0.0078 |
| F1 | 0.9961 |
| Outside-scope FP | 1 |

## 2. Checker Type

- [x] API-misuse (直接匹配不安全的哈希算法 API)

## 3. Source / Sink / Sanitizer Summary

### Sources
不适用（API-misuse 类型）。

### Sinks
弱哈希算法调用，包括：
- `MessageDigest.getInstance("MD2")` / `MessageDigest.getInstance("MD5")`
- `MessageDigest.getInstance("SHA-1")` (部分场景)
- 其他 `WeakHashSinks.gdl` 中定义的危险哈希算法

### Sanitizers / Barriers
无需 taint sanitizer；通过算法名称白名单/黑名单直接控制。

## 4. FP / FN Analysis

- **Precision = 0.9922, Recall = 1.0**: 近乎完美的表现。
- **FP (1)**: 仅 1 个 outside-scope FP（`cwe_scope_total=235`, `outside_scope_findings=1`），可能是跨 CWE 边界（CWE-328 vs CWE-328S）的 test case 分类问题。

## 5. Known Limitations

- Weak hash 检测相对简单直接（API + 算法名匹配），当前覆盖已接近理论上限
- CWE-328（Weak Hash）与 CWE-327（Broken Crypto）在 Benchmark 中存在边界模糊的 test case

## 6. Next Steps

- 分析唯一的 outside-scope FP 确定是否为 Benchmark 分类 artifact
- 与 CWE-327 checker 合并或共享 `WeakHashSinks.gdl` 与 `CryptoAlgorithmSinks.gdl` 的重叠部分
