# CWE-643 Godel Checker Analysis

## 1. Metrics Summary

指标来自 `experiments/cwe-643/eval/codefuse_eval/metrics.json`。

| Metric | Value |
|---|--:|
| Raw alerts | 32 |
| Dedup alerts | 32 |
| TP | 14 |
| FP | 18 |
| FN | 1 |
| Precision | 0.4375 |
| Recall | 0.9333 |
| FNR | 0.0667 |
| FPR | 0.9000 |
| FDR | 0.5625 |
| F1 | 0.5957 |
| Outside-scope FP | 0 |

## 2. Checker Type

- [x] Taint-based (使用 `TaintTracking.gdl`)

## 3. Source / Sink / Sanitizer Summary

### Sources
HTTP Servlet request API via `JavaServletSources.gdl`。

### Sinks
XPath 查询 API，包括：
- `XPath.evaluate`, `XPath.compile`
- `XPathExpression.evaluate`
- 其他 `XPathInjectionSinks.gdl` 中定义的 XPath 执行方法

### Sanitizers / Barriers
`XPathInjectionSanitizers.gdl` 提供 XPath 注入特定的 sanitizer/barrier 模型。

## 4. FP / FN Analysis

- **FP (18)**: Precision 最低（0.4375），FP 率最高。数据集极小（cwe_scope_total=35），18 个 FP 在小样本中占比很高：
  - XPath 注入的 source/sink 建模可能不够精确
  - Taint propagation 过宽（AST upward + generic call-result）在小数据集上效应放大
  - 缺乏 XPath 特定的常量/安全模式 barrier
- **FN (1)**: 1 个未覆盖的 XPath 注入变体（可能是特定 API 或间接调用）

## 5. Known Limitations

- 数据集极小（35 test cases），统计指标不够稳定
- XPath sink 模型可能不够完整（`XPathFactory`, `XPath.evaluate` 的多态重载等）
- 缺乏 XPath expression 是否为常量的安全检查

## 6. Next Steps

- 分析 1 个 FN 的具体 test case
- 审查 18 个 FP 是否属于 XPath 安全使用模式
- 考虑增加 XPath constant expression barrier
- 数据集太小，建议优先在真实项目上验证
