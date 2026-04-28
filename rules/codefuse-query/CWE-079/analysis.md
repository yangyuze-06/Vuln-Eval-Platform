# CWE-079 Godel Checker Analysis

## 1. Executive Summary

当前 `rules/codefuse-query/CWE-079/checker079.gdl` 是一个面向 Java Servlet-style XSS 的 taint checker。它以 HTTP request API 作为 source，以 HTTP response writer / JSP writer 输出 API 作为 sink，并通过 assignment、参数传递、返回值、AST upward propagation、generic call-result propagation 等规则传播 taint。

最终版本在 OWASP Benchmark CWE-079 评测上达到：

- Recall = `1.0000`
- Precision = `0.7193`
- TP = `246`
- FP = `96`
- FN = `0`
- Outside-scope FP = `0`

当前 checker 已经清除了主要的非 XSS 数据域误报，尤其是 non-web sink、sanitizer return re-taint、SQL/LDAP/XPath/XML 数据域污染。剩余 FP 主要来自 collection/path/object/context sensitivity，不适合继续用简单 suppress rule 或 benchmark-specific pattern 精修。

## 2. Final Metrics

指标来自 `experiments/cwe-079/eval/codefuse_eval/metrics.json`。

| Metric | Value |
|---|---:|
| Raw alerts | 342 |
| Unique testcase alerts | 342 |
| TP | 246 |
| FP | 96 |
| FN | 0 |
| Precision | 0.7193 |
| Recall | 1.0000 |
| F1 | 0.8367 |
| In-scope FP | 96 |
| Outside-scope FP | 0 |

## 3. Checker Scope and Semantics

### 3.1 Sources

Source 由 `is_http_source_call`、header enumeration 相关谓词和 `is_source_expr` 建模。当前覆盖的 request/input API 包括：

- `getParameter`
- `getParameterMap`
- `getParameterValues`
- `getParameterNames`
- `getHeader`
- `getHeaders`
- `getCookies`
- `getQueryString`
- `getPathInfo`
- `getRequestURI`
- `getRequestURL`
- `getServletPath`
- `getTheParameter`

另外，checker 显式建模 header enumeration flow：

- `getHeaderNames`
- `nextElement`
- `getHeaders`

这些规则用于覆盖 `Enumeration` 形式的 header name / header value 传播。

### 3.2 Sinks

Sink 由 `is_potential_xss_sink_call`、`is_web_response_sink_call`、`is_non_web_sink_call` 和 `is_xss_sink_call` 共同定义。

潜在输出 API 包括：

- `print`
- `println`
- `write`
- `format`
- `printf`
- `sendError`

Web response sink 判定要求调用文本看起来属于 HTTP/JSP 输出域，例如：

- `response.`
- `getWriter()`
- `getOutputStream()`
- `out.print`
- `out.println`
- `out.write`
- `out.format`
- `out.printf`
- `sendError`

Non-web sink filter 由 `is_non_web_sink_call` 实现，当前过滤：

- `System.out.print/println/write/printf/format`
- `System.err.print/println/write/printf/format`

这一过滤避免 `System.out.println(...)` 因包含 `out.` 而被误认为 JSP/response output。

### 3.3 Taint Propagation

核心 taint 谓词是 `is_tainted_expr` 和 `is_tainted_var`。当前支持：

- local variable initializer propagation
- assignment propagation
- actual argument to formal parameter propagation
- foreach iterable to iteration variable propagation
- collection / builder receiver taint
- AST upward propagation
- generic call-result propagation
- constructor argument propagation
- explicit inter-procedural return propagation

其中 collection / builder receiver taint 会在 `.put/.add/.addAll/.set/.insert/.append` 参数 tainted 时，把 receiver 变量标为 tainted。这保持了较高 recall，但也导致当前剩余的部分 collection FP。

Generic call-result propagation 会在 method call 的参数或 receiver tainted 时，把 call result 视为 tainted。它用于覆盖 `trim`、`substring`、`toString`、`String.valueOf`、`URLDecoder.decode`、`StringBuilder.toString` 等常见 taint-preserving transform。该规则已经通过 sanitizer return barrier 和 non-XSS domain barrier 收窄。

### 3.4 Sanitizers and Barriers

Sanitizer 由 `is_xss_sanitizer_call` 和 `is_sanitizer_expr` 建模。当前覆盖：

- `htmlEscape`
- `encodeForHTML`
- `escapeHtml`
- `escapeHtml4`
- `HTMLEntityEncode`

Sanitizer return barrier 由以下谓词实现：

- `var_has_sanitized_value`
- `is_sanitized_return_expr`
- `method_has_sanitized_return`
- `method_has_unsanitized_return`
- `is_sanitized_return_method`
- `is_sanitized_call_result`

它支持两类常见模式：

- `return sanitizer(x)`
- `y = sanitizer(x); return y`

当某个 method 的所有 return 都可证明来自 sanitizer expression 时，该 method call result 不会再被 generic call-result propagation 因参数 tainted 而重新污染。Explicit return taint propagation 仍然保留：如果 callee 明确 return tainted expression，调用结果仍然 tainted。

### 3.5 Non-XSS Domain Barriers

Non-XSS domain barrier 解决的问题是：SQL/LDAP/XPath/XML 查询 API 的参数可以被用户输入影响，但查询结果本身不应被简单视为 XSS taint continuation。

当前谓词包括：

- `is_sql_jdbc_domain_call`
- `is_ldap_jndi_domain_call`
- `is_xpath_xml_dom_domain_call`
- `is_non_xss_domain_call_result`
- `is_non_xss_domain_expr`

SQL/JDBC domain 覆盖示例：

- `executeQuery`
- `executeUpdate`
- `execute`
- `queryForObject`
- `queryForList`
- `query`
- `getString`
- `getObject`
- `getInt/getLong/getDouble/getFloat/getBoolean`

LDAP/JNDI domain 覆盖示例：

- `search`
- `next`
- `nextElement`
- `getAttributes`
- `getAll`
- `getAttribute`

XPath/XML/DOM domain 覆盖示例：

- `evaluate`
- `getTextContent`
- `getNodeValue`
- `getAttribute`
- `getElementsByTagName`
- `item`

这些 barrier 同时作用于 generic call-result propagation 和 AST upward propagation，避免 XML/DOM receiver taint 继续向上污染 DOM result call。

## 4. Optimization History

### 4.1 Baseline MVP

Baseline MVP 指标 based on experiment logs：

- Recall = `1.0000`
- Precision ~= `0.3832`
- TP = `246`
- FP = `396`
- FN = `0`
- Raw alerts = `642`

Baseline 的核心问题不是漏报，而是大量低质量 FP，尤其是 non-web sink 和 non-XSS data domain 被纳入 XSS flow。

### 4.2 Exp1: Non-web Sink Filter

问题：

- `System.out.println(...)` 被误认为 XSS sink。
- 根因是 `System.out.println` 文本同时包含 `out.`。原 GDL 逻辑中的 `return false` 没有形成全局否定，后续正向 sink 条件仍然能让该 call 成为 sink。

修复：

- 新增 `is_non_web_sink_call`
- 在 `is_xss_sink_call` 中加入 `!is_non_web_sink_call(c)`

指标变化 based on experiment logs：

| Metric | Before | After | Delta |
|---|---:|---:|---:|
| FP | 396 | 250 | -146 |
| Precision | 0.3832 | 0.4960 | +0.1128 |
| Recall | 1.0000 | 1.0000 | 0 |

### 4.3 Exp2: Sanitizer Return Barrier

问题：

- Callee 内部已经执行 sanitizer，例如 `HtmlUtils.htmlEscape(param)` 或 `ESAPI.encoder().encodeForHTML(param)`。
- Caller 侧调用 `doSomething(request, param)` 时，generic call-result propagation 看到参数 tainted，又把 method call result 重新标为 tainted。

修复：

- 新增 sanitized return method / sanitized call result 判断。
- 在 generic call-result propagation 中加入 `!is_sanitized_call_result(call)`。
- 保留 explicit inter-procedural return taint，不阻断真实 tainted return。

指标变化 based on experiment logs：

| Metric | Before | After | Delta |
|---|---:|---:|---:|
| FP | 250 | 212 | -38 |
| Precision | 0.4960 | 0.5371 | +0.0411 |
| Recall | 1.0000 | 1.0000 | 0 |

### 4.4 Exp3: Non-XSS Domain Call-result Barrier

问题：

- SQL / LDAP / XPath / XML 查询 API 的参数 tainted 时，generic call-result propagation 会把查询结果也当成 XSS taint continuation。
- 这造成 outside-scope FP，例如 SQLi/LDAPi/XPathi 相关测试中的结果输出被报告为 CWE-079。

修复：

- 新增 SQL/JDBC domain call barrier。
- 新增 LDAP/JNDI domain call barrier。
- 新增 XPath/XML/DOM domain call barrier。
- Generic call-result propagation 加入 `!is_non_xss_domain_call_result(call)`。
- AST upward propagation 加入 `!is_non_xss_domain_expr(e)`，防止 DOM/XML call result 被 receiver taint 继续污染。

指标变化 based on experiment logs：

| Metric | Before | After | Delta |
|---|---:|---:|---:|
| FP | 212 | 96 | -116 |
| Precision | 0.5371 | 0.7193 | +0.1822 |
| Recall | 1.0000 | 1.0000 | 0 |
| Outside-scope FP | 116 | 0 | -116 |

## 5. Rejected Experiments

这些实验不是简单失败，而是合理停止点：继续保留会引入过高复杂度、性能成本、或 benchmark overfitting 风险。

### 5.1 Collection Key/Index Sensitivity

目标是处理 map/list receiver 整体 taint 导致的 safe key/index FP，例如：

- `map.put("safeKey", safeValue)` 与 `map.put("taintedKey", taintedValue)` 后，`map.get("safeKey")` 被误报。
- `list.add(safe); list.add(tainted); list.add(safe); remove(0); get(1)` 这类 index shift 后 safe value 被误报。

结论：

- 完整 receiver/key/index proof 在 Datalog 中成本过高。
- Cheap literal pattern 容易变成 `keyA/keyB/get(1)` 这类 benchmark-specific rule。
- 最终回滚，不合并。

### 5.2 Sink-side Safe Constant Filter

目标是仅在最终 finding 前过滤明显 safe 的 sink argument。

结论：

- 剩余 FP 很少是 `println("safe")` 这种 direct literal sink arg。
- `format/printf` 中 literal format string 不代表输出安全，真实输出通常在 `Object[] obj` 或后续 format 参数中。
- 实验曾导致 TP 损失，因此回滚。

### 5.3 Final Guarded Precision Polish

最终精修阶段对剩余 96 个 FP 进行分类，没有找到满足以下条件的 micro-filter：

- removed FP >= 5
- lost TP = 0
- 不依赖 benchmark-specific pattern
- 实现复杂度低
- 可用真实 Java Web 语义解释

最终没有修改代码。

## 6. Remaining FP Analysis

剩余 FP 分类基于 `experiments/cwe-079/eval/codefuse_eval/fp.csv` 和对应 benchmark 源码抽样分析。

| Category | Count | Reason |
|---|---:|---|
| Collection imprecision | 36 | requires map/list key-index or helper-return collection reasoning |
| Path infeasible / constant branch | 49 | requires path sensitivity / constant condition / switch reasoning |
| Other / too risky | 11 | helper, reflection, factory, static safe value, object/context modeling |

Sink API 分布：

| Sink API | FP Count |
|---|---:|
| `printf` | 30 |
| `write` | 22 |
| `println` | 18 |
| `format` | 15 |
| `print` | 11 |

这些 FP 不适合继续用简单 GDL rule 精修：

- Collection imprecision 需要 receiver identity、key/index value、write/read order、remove/set/add 语义。
- Path infeasible 需要常量表达式求值、branch feasibility、switch target reasoning。
- Helper/reflection/factory 案例需要 object sensitivity、call target resolution、method summary 和 context sensitivity。
- Format/printf 案例需要准确识别所有 relevant output argument，不能只看 format string。

## 7. Why This Is Near the Engineering Limit

当前 checker 已经解决了 taint-based CWE-079 checker 中最主要的工程误报来源：

- wrong sink domain：通过 non-web sink filter 排除 `System.out/System.err`。
- sanitizer return re-taint：通过 sanitizer return barrier 阻断 sanitized method call result 被 generic propagation 重新污染。
- non-XSS data domain pollution：通过 SQL/LDAP/XPath/XML domain barrier 清除 outside-scope FP。

剩余问题需要的是分析能力升级，而不是简单规则补丁：

- flow sensitivity：识别变量后续 safe overwrite 是否 kill 旧 taint。
- path sensitivity：识别常量条件、不可达分支、switch target。
- object sensitivity：区分不同 map/list/builder 实例和 factory 返回对象。
- collection key/index sensitivity：区分同一 receiver 上不同 key/index 的 taint。
- context-sensitive XSS modeling：区分 HTML body、attribute、JavaScript、CSS、URL 等输出上下文。
- framework-specific modeling：覆盖真实项目中的 Spring MVC、template engine、custom response wrapper 等。

继续在 benchmark 上写 suppress rule，容易用复杂度换很小 precision 增益，并带来 recall 回退风险。

## 8. Generalization and Overfitting Discussion

当前最终版中合理泛化的规则包括：

- `System.out/System.err` 不是 web response sink。
- Sanitizer return barrier：`return sanitizer(x)` 或 `y = sanitizer(x); return y` 的 method call result 不应被 generic propagation 重新污染。
- SQL/LDAP/XML/XPath 查询结果不是 XSS taint-preserving transformation。

存在 overfitting 风险、并已明确避免的规则包括：

- `BenchmarkTestXXX` 特判。
- 文件名 / 行号特判。
- `keyA/keyB/get(1)` 这类 benchmark collection pattern。
- broad variable-name heuristic。
- 过宽的 `clean/sanitize` 方法名匹配。
- 只看 `format/printf` 第一个 literal format string 就 suppress finding。

当前最终版没有引入 benchmark-specific pattern。

## 9. Known Limitations

- 主要面向 Servlet-style XSS。
- Spring MVC / WebGoat source/sink model 尚未覆盖。
- Collection key/index insensitive。
- Path insensitive。
- Flow-insensitive overwrite kill 不完善。
- `format/printf` 参数建模有限，尤其是 `Object[]` 和 varargs 展开。
- 未做 HTML body / HTML attribute / JavaScript / CSS / URL context-sensitive sanitizer matching。
- Reflection / factory / helper summary 有限。
- 对 framework abstraction、template rendering、custom response wrapper 的覆盖有限。

## 10. Next Steps

建议后续不要继续 OWASP Benchmark precision micro-tuning，而是：

1. 保存当前版本为 final benchmark version。
2. 在真实 Java Web 项目上验证。
3. 为 Spring MVC 添加 source/sink model，例如：
   - `@RequestParam`
   - `@PathVariable`
   - `@RequestBody`
   - `Model.addAttribute`
   - `ResponseEntity.body`
   - WebGoat `AttackResult.feedback`
4. 建立真实项目人工审计流程，记录 true positive、false positive、missing framework model。
5. 如果继续研究分析能力，优先考虑 path/context/object sensitivity，而不是继续写 ad-hoc suppress rule。

## 11. Final Recommendation

当前 CWE-079 checker 可以作为 taint-based Godel checker 的 final benchmark version。

建议停止 OWASP Benchmark 上的 precision micro-tuning。当前指标已经达到：

- Recall = `1.0000`
- Precision = `0.7193`
- Outside-scope FP = `0`

下一阶段应转向 real-world validation 和 framework-specific source/sink modeling。继续在 benchmark 上精修，边际收益低，且更可能引入 overfitting 或 recall regression。
