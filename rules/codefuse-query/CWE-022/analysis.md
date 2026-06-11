# CWE-022 Godel Checker Analysis

## 1. Metrics Summary

指标来自 `experiments/cwe-022/eval/codefuse_eval/metrics.json`。

| Metric | Value |
|---|--:|
| Raw alerts | 228 |
| Dedup alerts | 228 |
| TP | 120 |
| FP | 108 |
| FN | 13 |
| Precision | 0.5263 |
| Recall | 0.9023 |
| FNR | 0.0977 |
| FPR | 0.8000 |
| FDR | 0.4737 |
| F1 | 0.6648 |
| Outside-scope FP | 0 |

## 2. Checker Type

- [x] Taint-based (使用 `TaintTracking.gdl`)

## 3. Source / Sink / Sanitizer Summary

### Sources
HTTP Servlet request API（`getParameter`, `getHeader`, `getCookies`, `getQueryString`, `getPathInfo`, `getRequestURI` 等），包含 header enumeration flow（`getHeaderNames` → `nextElement` → `getHeaders`）。

### Sinks
文件路径相关 API，包括构造器类（`File`, `FileInputStream`, `FileOutputStream`, `FileReader`, `FileWriter`, `RandomAccessFile`, `ZipFile`）和 NIO 方法类（`Files.newInputStream`, `Files.newOutputStream`, `Files.readAllBytes`, `Files.readAllLines`, `Files.readString`, `Files.write`）。

### Sanitizers / Barriers
当前主要依赖 `PathTraversalSanitizers.gdl` 中的 sanitizer 模型。

## 4. FP / FN Analysis

- **FP 主要来源 (108)**: AST upward propagation 过宽导致过度污染；receiver taint 规则激进（tainted arg → tainted receiver）；generic call-result propagation 缺乏 sanitizer return barrier。
- **FN (13)**: 部分路径遍历场景未覆盖，可能包括 `getResource` 等非标准路径 API 或特定 wrapper 模式。

## 5. Known Limitations

- Source/sink 建模大量依赖 `getPrintableText().contains()` 字符串匹配，对 import、全限定名、重载方法敏感
- AST upward propagation 过宽（child tainted → parent tainted）
- Receiver taint 规则激进，导致链式污染
- Sink 粒度偏粗（`new File()` 直接作为最终 sink，实际可能只是构造路径对象）
- 缺少基于 API 符号解析的语义建模

## 6. Next Steps

- Source/sink 从字符串匹配迁移到 receiver 类型 + 方法签名语义建模
- 分离"路径对象构造"与"真实文件 I/O" sink
- 收紧 propagation 规则（限制 AST upward、receiver taint 改为白名单）
- 补充 sanitizer return barrier 以减少 generic propagation FP

---

详细的重构分析见 `analysis-and-backup/analysis.md`。
