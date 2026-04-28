> [!NOTE]
> 这是为了保留上下文而存档的历史重构计划文档。

# CodeFuse 安全 Checker 模块化重构计划（CWE-022 / CWE-078 / CWE-079）


## 1. 当前状态

CWE-022、CWE-078、CWE-079 最初都是单文件实验脚本。三者都加载 `coref_java_src.db`，都以 Java Servlet/request API 作为主要 taint source，并通过局部变量、赋值、实参到形参、foreach、receiver、AST upward、call-result、constructor-result、return-to-call 等规则传播 taint。

CWE-022 当前结构：`rules/codefuse-query/CWE-022/checker022.gdl` 中 `default_java_db()` 位于第 6 行，source wrapper 位于第 13-43 行，path sink 位于第 73-95 行，helper wrapper 位于第 101-127 行，完整 taint propagation 当前仍位于第 132-271 行，finding 输出位于第 276-330 行。

CWE-078 当前结构：`rules/codefuse-query/CWE-078/checker078.gdl` 中 `default_java_db()` 位于第 6 行，source wrapper 位于第 13-43 行，command sink 位于第 74-89 行，helper wrapper 位于第 95-121 行，完整 taint propagation 当前仍位于第 126-266 行，finding 输出位于第 271-328 行。

CWE-079 当前结构：`rules/codefuse-query/CWE-079/checker079.gdl` 中 `default_java_db()` 位于第 6 行，source wrapper 位于第 13-41 行，XSS sink 位于第 71-119 行，XSS sanitizer/barrier 位于第 124-279 行，helper wrapper 位于第 285-311 行，XSS taint propagation 当前仍位于第 316-477 行，finding 输出位于第 482-513 行。

已完成的模块化阶段：

- Phase 1：三者共用 `rules/codefuse-query/lib/security/java/JavaServletSources.gdl`。Servlet source、XSS source superset、source expr/source stmt、header enumeration call/source 已抽出。
- Phase 2：三者共用 `rules/codefuse-query/lib/security/java/TaintHelpers.gdl`。调用参数枚举、receiver 绑定、new 参数枚举、call target 绑定已抽出。

共享逻辑：

- Source modeling：Servlet/request source 由 `JavaServletSources.gdl` 统一提供；CWE-079 使用包含 `getRequestURL` 和 `getServletPath` 的 XSS source superset。
- Helper predicates：调用参数、receiver、constructor argument、call target 由 `TaintHelpers.gdl` 统一提供。
- Taint propagation：CWE-022 和 CWE-078 完全一致；CWE-079 与 022/078 共享大部分传播形状，但有 XSS 专用 receiver 限制、sanitizer call barrier、sanitized-return barrier 和 non-XSS domain barrier。
- Sink modeling：CWE-specific。CWE-022 是 file/path sink；CWE-078 是 command execution sink；CWE-079 是 response/JSP output sink。
- Sanitizer/barrier：当前只有 CWE-079 明确建模，仍保留在 `checker079.gdl`。
- Reporting/output：三者都输出 `ruleId, sinkFile, line`，输出字段不得在 Phase 1-5 中改变。

## 2. Shared Logic Inventory

| Component | Used By | Current Location | Responsibility | Suggested New Module | Refactor Risk |
|---|---|---|---|---|---|
| Java DB loader | 022/078/079 | 各 checker `default_java_db()` | 加载 `coref_java_src.db` | `JavaDB.gdl` | 低 |
| Servlet source model | 022/078/079 | `JavaServletSources.gdl` | 识别 request parameter/header/cookie/query/path source | 已抽出 | 低 |
| Header enumeration source | 022/078/079 | `JavaServletSources.gdl` + checker wrapper | 建模 `getHeaderNames/getHeaders/nextElement` | 已部分抽出；依赖 taint 的 expression flow 随 Phase 3 进入 taint engine | 中 |
| Tainted call argument helper | 022/078/079 | checker wrapper + `TaintHelpers.gdl` | 判断调用是否有 tainted argument | `TaintTracking.gdl` wrapper | 中 |
| Tainted receiver helper | 022/078/079 | checker wrapper + `TaintHelpers.gdl` | 判断 receiver/call site 是否 tainted | `TaintTracking.gdl` wrapper | 中 |
| Tainted constructor argument helper | 022/078/079 | checker wrapper + `TaintHelpers.gdl` | 判断 new expression 是否有 tainted argument | `TaintTracking.gdl` wrapper | 中 |
| Call target binding | 022/078/079 | `TaintHelpers.gdl` | 绑定 method/constructor call target | 已抽出 | 中 |
| Local variable propagation | 022/078/079 | checker `is_tainted_var` | initializer 到 variable | `TaintTracking.gdl` | 中 |
| Assignment propagation | 022/078/079 | checker `is_tainted_var` | assignment source 到 destination variable | `TaintTracking.gdl` | 中 |
| Actual-to-formal propagation | 022/078/079 | checker `is_tainted_var` | tainted actual 到 formal parameter | `TaintTracking.gdl` | 高 |
| Foreach propagation | 022/078/079 | checker `is_tainted_var` | iterable 到 iteration parameter | `TaintTracking.gdl` | 中 |
| Receiver-state propagation | 022/078/079 | checker `is_tainted_var` | receiver object state taint | `TaintTracking.gdl`；079 保持 XSS 专用限制 | 高 |
| Variable use propagation | 022/078/079 | checker `is_tainted_expr` | tainted var usage 到 expr | `TaintTracking.gdl` | 中 |
| Upward AST propagation | 022/078/079 | checker `is_tainted_expr` | child expr 到 parent expr | `TaintTracking.gdl`；079 保持 barrier 条件 | 高 |
| Call-result propagation | 022/078/079 | checker `is_tainted_expr` | tainted arg/receiver 到 call result | `TaintTracking.gdl`；079 保持 barrier 条件 | 高 |
| Constructor-result propagation | 022/078/079 | checker `is_tainted_expr` | tainted constructor arg 到 new result | `TaintTracking.gdl` | 中 |
| Return-to-call propagation | 022/078/079 | checker `is_tainted_expr` | tainted return result 到 call expression | `TaintTracking.gdl` | 高 |
| Path traversal sink | 022 | `checker022.gdl` | 文件/路径危险 API | Phase 4 `sinks/PathTraversalSinks.gdl` | 低 |
| Command injection sink | 078 | `checker078.gdl` | command/process API | Phase 4 `sinks/CommandInjectionSinks.gdl` | 中 |
| XSS sink | 079 | `checker079.gdl` | response/JSP output API | Phase 4 `sinks/XssSinks.gdl` | 中 |
| XSS sanitizer/barrier | 079 | `checker079.gdl` | HTML escape、sanitized return、non-XSS domain barrier | 后续 sanitizer phase | 高 |
| Finding output | 022/078/079 | 各 checker finding predicate | 输出 `ruleId, sinkFile, line` | Phase 5 `SecurityReporting.gdl` | 低 |
| Debug reason output | 022 debug | `analysis-and-backup/checker_taint_no_fallback_debug.gdl` | 输出 reason | Phase 5 `SecurityDebug.gdl` | 中 |
| Benchmark/eval scripts | 022/078/079 | `scripts/converters`, `scripts/evaluation` | JSON/CSV 转换和指标计算 | 保留 scripts；补 package path runner | 低 |

## 3. Proposed Architecture

```text
rules/codefuse-query/lib/security/java/
  JavaDB.gdl
  JavaServletSources.gdl
  TaintHelpers.gdl
  TaintTracking.gdl
  Sanitizers.gdl
  SecurityReporting.gdl
  SecurityDebug.gdl

rules/codefuse-query/lib/security/java/sinks/
  PathTraversalSinks.gdl
  CommandInjectionSinks.gdl
  XssSinks.gdl

rules/codefuse-query/queries/security/java/
  CWE022_PathTraversal.gdl
  CWE078_CommandInjection.gdl
  CWE079_Xss.gdl

rules/codefuse-query/tests/security/java/
  cwe022/
  cwe078/
  cwe079/
```

后续新增 CWE checker 必须优先复用 `JavaServletSources.gdl`、`TaintHelpers.gdl`、`TaintTracking.gdl` 和 reporting/sink/sanitizer 模块。新 checker 文件只负责 CWE-specific sink、CWE-specific sanitizer/barrier、ruleId 和 message，不允许复制旧的 taint engine。

`TaintTracking.gdl` 初期必须保持当前 broad taint semantics。Phase 3 只做搬迁，不做 precision/recall 优化。

## 4. Public API Design

| API | 输入 | 输出含义 | Public/Internal | 使用方 | 是否保留旧 wrapper |
|---|---|---|---|---|---|
| `isServletTaintSourceCall(c)` | `MethodAccessExpression` | Servlet/request source call | Public | 022/078 | 是 |
| `isServletXssTaintSourceCall(c)` | `MethodAccessExpression` | XSS source superset | Public | 079 | 是 |
| `isServletTaintSourceExpr(e)` | `Expression` | Servlet source expr | Public | 022/078 | 是 |
| `isServletXssTaintSourceExpr(e)` | `Expression` | XSS source expr | Public | 079 | 是 |
| `callArgument(c,arg)` | call, expr | call argument relation | Public helper | 022/078/079 | 否 |
| `callReceiverReference(c,recv)` | call, ref expr | reference receiver relation | Public helper | 022/078 | 否 |
| `callReceiverExpression(c,recv)` | call, expr | expression receiver relation | Public helper | 079 | 否 |
| `newArgument(n,arg)` | new expr, expr | constructor argument relation | Public helper | 022/078/079 | 否 |
| `callTargetsCallable(c,callee)` | call, callable | call target binding | Public helper | 022/078/079 | 是 |
| `isTaintedExpr(e)` | `Expression` | 标准 servlet taint expr | Public | 022/078 | 是：`is_tainted_expr` |
| `isTaintedVar(v)` | `Variable` | 标准 servlet taint var | Public | 022/078 | 是：`is_tainted_var` |
| `isXssTaintedExpr(e)` | `Expression` | 保持 XSS barrier 语义的 taint expr | Public | 079 | 是：`is_tainted_expr` |
| `isXssTaintedVar(v)` | `Variable` | 保持 XSS barrier 语义的 taint var | Public | 079 | 是：`is_tainted_var` |
| `flowsTo(src,sink)` | expr, expr | 未来 path tracking 占位 | Public future | future | 否 |
| `isPathTraversalSinkCall(c)` | call | path sink | Phase 4 | 022 | 是 |
| `isCommandInjectionSinkCall(c)` | call | command sink | Phase 4 | 078 | 是 |
| `isXssSinkCall(c)` | call | XSS sink | Phase 4 | 079 | 是 |
| `emitFinding(...)` | ruleId/file/line | reporting | Phase 5 | 022/078/079 | 是 |

## 5. New Checker Development Guide

新增 checker 标准流程：

1. 先判断能否复用 `JavaServletSources.gdl`。
2. 默认复用 `TaintTracking.gdl`，不允许复制 `is_tainted_expr` / `is_tainted_var`。
3. 新 checker 只新增 CWE-specific sinks、sanitizers/barriers、reporting ruleId/message。
4. 如果新增 source 是框架级输入，例如 Spring Boot `@RequestParam`，扩展 source module，不写在单个 checker 里。
5. 如果新增 propagation 是通用传播规则，进入 `TaintTracking.gdl`。
6. 如果只是某个 CWE 的特例，进入对应 sink/sanitizer 模块。
7. 每个新 checker 必须附带 minimal Java tests、expected output、benchmark/eval command、README update。

模板：

```rust
use coref::java::*
use security::java::JavaServletSources::*
use security::java::TaintHelpers::*
use security::java::TaintTracking::*

fn cweXXXFinding(ruleId: string, sinkFile: string, line: int) -> bool {
    for (sink in MethodAccessExpression(default_java_db())) {
        if (isXxxSink(sink) && callHasTaintedArgument(sink) && ruleId = "CWE-XXX") {
            return true
        }
    }
}

fn main() {
    output(cweXXXFinding())
}
```

## 6. Migration Plan

- Phase 0 Baseline Freeze：保存旧 CSV、metrics、hit-set。
- Phase 1 Extract shared source model：抽 `JavaServletSources.gdl`，三个 checker 输出完全一致。
- Phase 2 Extract helper predicates：抽 `TaintHelpers.gdl`，三个 checker 输出完全一致。
- Phase 3 Extract `TaintTracking.gdl`：抽 `is_tainted_expr` / `is_tainted_var` 和公共传播逻辑，保持 broad semantics，三个 checker 输出完全一致。
- Phase 4 Extract sink modules：抽 `PathTraversalSinks.gdl`、`CommandInjectionSinks.gdl`、`XssSinks.gdl`，三个 checker 输出完全一致。
- Phase 5 Extract reporting/debug modules：抽 `SecurityReporting.gdl`、`SecurityDebug.gdl`，三个 checker 输出完全一致。
- Phase 6 Tests + README + PR packaging：补 minimal tests、expected CSV、benchmark report、PR description。

## 7. Framework Hardening

Phase 5A adds sanitizer/barrier modules for framework reuse without changing checker behavior:

```text
rules/codefuse-query/lib/security/java/sanitizers/
  GlobalSanitizers.gdl
  PathTraversalSanitizers.gdl
  CommandInjectionSanitizers.gdl
  XssSanitizers.gdl
```

`GlobalSanitizers.gdl` is reserved for language/framework-neutral sanitizers that are safe across multiple CWE families. A predicate belongs here only when its semantics are not tied to a specific vulnerability class and every consumer can use it without changing the meaning of another checker.

CWE-specific sanitizer modules contain only sanitizer or barrier logic for that CWE family. For example, XSS HTML escaping and non-XSS domain result barriers belong in `XssSanitizers.gdl`; path canonicalization or allowlist handling would belong in `PathTraversalSanitizers.gdl` only after a phase explicitly enables that behavior. Default-false placeholders are allowed so new checkers can depend on stable module APIs without silently enabling filtering.

New checker files must not define sanitizer/barrier models directly in the main checker. They must call the appropriate global or CWE-specific sanitizer module through a small compatibility wrapper, and they must not wire sanitizer/barrier predicates into taint propagation unless the phase explicitly requires it and regression output remains identical.

## 8. Regression Strategy

每个阶段都保存：

- `phaseN_new_cwe022.csv`, `phaseN_new_cwe022_metrics.json`, `phaseN_diff_cwe022_hits.csv`
- `phaseN_new_cwe078.csv`, `phaseN_new_cwe078_metrics.json`, `phaseN_diff_cwe078_hits.csv`
- `phaseN_new_cwe079.csv`, `phaseN_new_cwe079_metrics.json`, `phaseN_diff_cwe079_hits.csv`

比较维度：

- exact hit-set by `ruleId,file,line`
- TP / FP / FN
- Precision / Recall / F1
- total findings count
- changed testcase list

Phase 1-5 默认要求 exact output equivalence。任何 diff 都视为 regression，除非 `update.txt` 解释并人工确认。

## 9. PR Readiness Checklist

- 三个 CWE 的 README。
- query comments。
- module comments。
- minimal tests。
- benchmark reports。
- no OWASP Benchmark testcase-name hacks。
- no line-number hacks。
- license compatibility。
- upstream naming style。
- performance notes。
- limitations：path-insensitive、context-insensitive、heap/collection imprecision、printable-text matching。
- future extension points：Spring Boot sources、better sanitizer modeling、path graph reporting。
