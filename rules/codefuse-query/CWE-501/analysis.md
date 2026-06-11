# CWE-501 Godel Checker Analysis

## 1. Metrics Summary

指标来自 `experiments/cwe-501/eval/codefuse_eval/metrics.json`。

| Metric | Value |
|---|--:|
| Raw alerts | 112 |
| Dedup alerts | 112 |
| TP | 78 |
| FP | 34 |
| FN | 5 |
| Precision | 0.6964 |
| Recall | 0.9398 |
| FNR | 0.0602 |
| FPR | 0.7907 |
| FDR | 0.3036 |
| F1 | 0.8000 |
| Outside-scope FP | 0 |

## 2. Checker Type

- [x] Taint-based (使用 `TaintTracking.gdl`)

## 3. Source / Sink / Sanitizer Summary

### Sources
HTTP Servlet request API via `JavaServletSources.gdl`。

### Sinks
Trust boundary violation sinks，包括：
- HTTP Session 属性设置（`HttpSession.setAttribute`）
- 其他 `TrustBoundarySinks.gdl` 中定义的可信边界违规点

### Sanitizers / Barriers
`TrustBoundarySanitizers.gdl` 提供信任边界 sanitizer/barrier 模型，包括 session attribute 验证、输入清理等。

## 4. FP / FN Analysis

- **FP (34)**: Trust boundary 的语义较为模糊，"可信边界"的定义依赖上下文：
  - Session attribute 赋值不一定构成违规（取决于后续是否被信任使用）
  - 部分 test case 中 session attribute 的值来自安全来源
  - Taint propagation 过宽（AST upward, generic call-result）
- **FN (5)**: 少数信任边界违规模式未覆盖，可能涉及非标准 session API 或特定 wrapper 模式

## 5. Known Limitations

- "信任边界违规"本质上是上下文敏感的语义问题，纯 taint tracking 无法完全区分
- Session attribute 的 source/sink 边界模糊（赋值本身不是漏洞，"信任使用"才是）
- 缺乏对数据在 session 存储后被"信任消费"的 downstream tracking

## 6. Next Steps

- 分析 5 个 FN 的具体根因（可能是特定 session API 变体）
- 考虑增加 sanitizer 以排除明显的安全赋值模式
- 探索"信任使用"下游追踪（session attribute 被读取并用于安全关键操作）
