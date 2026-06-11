# CWE-614 Godel Checker Analysis

## 1. Metrics Summary

指标来自 `experiments/cwe-614/eval/codefuse_eval/metrics.json`。

| Metric | Value |
|---|--:|
| Raw alerts | 36 |
| Dedup alerts | 36 |
| TP | 36 |
| FP | 0 |
| FN | 0 |
| Precision | 1.0000 |
| Recall | 1.0000 |
| FNR | 0.0000 |
| FPR | 0.0000 |
| FDR | 0.0000 |
| F1 | 1.0000 |
| Outside-scope FP | 0 |

## 2. Checker Type

- [x] API-misuse (直接匹配不安全的 Cookie 配置)

## 3. Source / Sink / Sanitizer Summary

### Sources
不适用（API-misuse 类型）。

### Sinks
不安全的 Cookie 配置 API，包括：
- `Cookie.setSecure(false)` 或缺少 `setSecure(true)` 调用
- `Cookie.setHttpOnly(false)` 或缺少 `setHttpOnly(true)` 调用
- 其他 `CookieSecuritySinks.gdl` 中定义的不安全 Cookie 设置

### Sanitizers / Barriers
无需 taint sanitizer；通过 Cookie API 调用直接判定。

## 4. FP / FN Analysis

- **Precision = 1.0, Recall = 1.0**: 完美指标。
- 该 CWE 的数据集较小（36 TP + 31 TN），Checker 对 Cookie 安全配置的检测准确且完整。

## 5. Known Limitations

- 仅覆盖 `javax.servlet.http.Cookie` API
- 未覆盖 Spring 框架的 `ResponseCookie` builder 模式
- 未检测 Cookie 被创建后、添加到 response 前被修改的复杂场景
- 真实项目中 Cookie 配置可能来自配置文件/环境变量，静态检测无法判定

## 6. Next Steps

- 当前 Benchmark 版本可作为 baseline
- 扩展覆盖 Spring `ResponseCookie.from()` / `ResponseCookie.of()` builder
- 考虑检测 `Cookie.setMaxAge` / `Cookie.setDomain` / `Cookie.setPath` 等更广泛的安全配置
