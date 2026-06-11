# CWE-089 Godel Checker Analysis

## 1. Metrics Summary

指标来自 `experiments/cwe-089/eval/codefuse_eval/metrics.json`。

| Metric | Value |
|---|--:|
| Raw alerts | 417 |
| Dedup alerts | 417 |
| TP | 267 |
| FP | 150 |
| FN | 5 |
| Precision | 0.6403 |
| Recall | 0.9816 |
| FNR | 0.0184 |
| FPR | 0.6466 |
| FDR | 0.3597 |
| F1 | 0.7750 |
| Outside-scope FP | 0 |

## 2. Checker Type

- [x] Taint-based (使用 `TaintTracking.gdl`)

## 3. Source / Sink / Sanitizer Summary

### Sources
HTTP Servlet request API via `JavaServletSources.gdl`。覆盖 `getParameter`, `getParameterMap`, `getParameterValues`, `getHeader`, `getHeaders`, `getCookies`, `getQueryString` 等标准入口。

### Sinks
SQL 执行 API，包括：
- `Statement.executeQuery/executeUpdate/execute`
- `PreparedStatement` 拼接相关
- Spring `JdbcTemplate.query/queryForObject/queryForList`
- 其他 JDBC SQL 执行方法

### Sanitizers / Barriers
`SqlInjectionSanitizers.gdl` 提供 SQL 注入特定的 sanitizer/barrier 模型，包括 `ESAPI.encoder().encodeForSQL` 等。

## 4. FP / FN Analysis

- **FP (150)**: SQL 注入是最复杂的注入类型之一。FP 主要来自：
  - 常量折叠/死代码分支无法被 AST 引擎识别
  - PreparedStatement 参数化安全模式与字符串拼接模式共存时的 over-taint
  - Collection/list receiver taint 传播过宽
- **FN (5)**: 少数 SQL 注入变体未覆盖，可能涉及非标准 JDBC wrapper 或 ORM 框架特定 API

## 5. Known Limitations

- PreparedStatement 安全使用与危险拼接的区分不够精确
- 缺乏常量折叠和路径敏感性
- ORM 框架（Hibernate, JPA）的特定 sink 模型覆盖不足
- Generic call-result propagation 将查询结果也标记为 taint，可能放大污染

## 6. Next Steps

- 细化 PreparedStatement vs Statement 的 sink 区分
- 增加 ORM 框架特定 sink（Hibernate Criteria, JPA native query）
- 考虑对已知安全的参数化模式增加 barrier
- 分析 5 个 FN 的具体根因并补充规则
