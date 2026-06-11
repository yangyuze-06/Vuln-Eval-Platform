# CWE-090 Godel Checker Analysis

## 1. Metrics Summary

指标来自 `experiments/cwe-090/eval/codefuse_eval/metrics.json`。

| Metric | Value |
|---|--:|
| Raw alerts | 49 |
| Dedup alerts | 49 |
| TP | 27 |
| FP | 22 |
| FN | 0 |
| Precision | 0.5510 |
| Recall | 1.0000 |
| FNR | 0.0000 |
| FPR | 0.6875 |
| FDR | 0.4490 |
| F1 | 0.7105 |
| Outside-scope FP | 0 |

## 2. Checker Type

- [x] Taint-based (使用 `TaintTracking.gdl`)

## 3. Source / Sink / Sanitizer Summary

### Sources
HTTP Servlet request API via `JavaServletSources.gdl`。

### Sinks
LDAP 查询 API，包括 `DirContext.search`, `InitialDirContext.search`, `DirContext.lookup` 等 JNDI LDAP 方法。

### Sanitizers / Barriers
`LdapInjectionSanitizers.gdl` 提供 LDAP 注入特定的 sanitizer/barrier 模型，包括 `ESAPI.encoder().encodeForLDAP` 等。

## 4. FP / FN Analysis

- **Recall = 1.0**：所有 LDAP 注入漏洞均被检测到，覆盖率完美。
- **FP (22)**: 数据集较小（cwe_scope_total=59），FP 主要来自：
  - Taint propagation 过宽（AST upward + generic call-result）
  - LDAP search result 被 receiver taint 继续传播
  - 常量和安全模式缺乏 barrier 识别

## 5. Known Limitations

- LDAP 数据集较小（27 TP + 32 TN），统计显著性有限
- Non-LDAP domain barrier 不完善（LDAP 查询结果不应继续传播为 LDAP injection taint）
- 缺乏 LDAP filter escaping 安全模式的识别

## 6. Next Steps

- 增加 LDAP filter escape / DN encoding 相关的 sanitizer 模型
- 考虑 LDAP search result barrier（查询结果不应回传为 sink）
- 在小数据集上谨慎调参，避免 overfitting
