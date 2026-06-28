# CodeFuse 安全 Checker 模块化重构计划

## 1. 背景

CWE-022、CWE-078、CWE-079 最初都是单文件实验脚本。三者都加载 `coref_java_src.db`，以 Java Servlet/request API 作为主要 taint source，并通过局部变量、赋值、实参到形参、foreach、receiver、AST upward、call-result、constructor-result、return-to-call 等规则传播 taint。

重构目标是把重复的 source、helper、taint propagation、sink、sanitizer 和 reporting 逻辑逐步拆分，形成可复用的 Java security checker framework。

## 2. 已完成的模块化阶段

- Phase 1：抽出 `JavaServletSources.gdl`，统一 Servlet source、XSS source superset、source expression/source statement 和 header enumeration source。
- Phase 2：抽出 `TaintHelpers.gdl`，统一调用参数、receiver、constructor argument 和 call target 绑定。
- Phase 3：抽出 `TaintTracking.gdl`，统一 `isTaintedExpr` / `isTaintedVar` 和 broad taint propagation。
- Phase 4：抽出 sink modules，例如 `PathTraversalSinks.gdl`、`CommandInjectionSinks.gdl`、`XssSinks.gdl`。
- Phase 5：引入 sanitizer/barrier 模块和新增 checker 模板，支持更多 CWE。

## 3. 共享逻辑清单

| 组件 | 使用方 | 当前位置 | 职责 | 风险 |
| --- | --- | --- | --- | --- |
| Java DB loader | 各 checker | `checkerXXX.gdl` | 加载 `coref_java_src.db` | 低 |
| Servlet source model | 022/078/079/089/090/643/501 | `JavaServletSources.gdl` | 识别 request parameter/header/cookie/query/path source | 低 |
| Taint helper predicates | 污点型 checker | `TaintHelpers.gdl` | 绑定 call argument、receiver、new argument、call target | 中 |
| Local variable propagation | 污点型 checker | `TaintTracking.gdl` | initializer 到 variable | 中 |
| Assignment propagation | 污点型 checker | `TaintTracking.gdl` | assignment source 到 destination variable | 中 |
| Actual-to-formal propagation | 污点型 checker | `TaintTracking.gdl` | tainted actual 到 formal parameter | 高 |
| Foreach propagation | 污点型 checker | `TaintTracking.gdl` | iterable 到 iteration parameter | 中 |
| Receiver-state propagation | 污点型 checker | `TaintTracking.gdl` | receiver object state taint | 高 |
| AST upward propagation | 污点型 checker | `TaintTracking.gdl` | child expression 到 parent expression | 高 |
| Call-result propagation | 污点型 checker | `TaintTracking.gdl` | tainted arg/receiver 到 call result | 高 |
| Return-to-call propagation | 污点型 checker | `TaintTracking.gdl` | tainted return result 到 call expression | 高 |
| Sink modeling | 各 checker | `sinks/*.gdl` | CWE-specific sink/API 模型 | 低到中 |
| Sanitizer/barrier/scope filter | 各 checker | `sanitizers/*.gdl` | CWE-specific suppression 和边界控制 | 中 |
| Finding output | 各 checker | `checkerXXX.gdl` | 输出 `ruleId, sinkFile, line` | 低 |

## 4. 目标架构

```text
rules/codefuse-query/lib/security/java/
  JavaServletSources.gdl
  TaintHelpers.gdl
  TaintTracking.gdl
  sinks/
  sanitizers/

rules/codefuse-query/CWE-XXX/
  checkerXXX.gdl

tests/codefuse-query/java/cweXXX/
```

新增 CWE checker 必须优先复用共享 source、helper、taint engine、sink/sanitizer 模块。主 checker 文件只负责 CWE-specific 连接和 reporting，不允许复制旧 taint engine。

## 5. Public API 约定

| API | 含义 | 使用方 |
| --- | --- | --- |
| `isServletTaintSourceCall(c)` | Servlet/request source call | 污点型 checker |
| `isServletTaintSourceExpr(e)` | Servlet/request source expression | 污点型 checker |
| `isServletXssTaintSourceCall(c)` | XSS source superset | CWE-079 |
| `callArgument(c,arg)` | call argument relation | helper |
| `callReceiverReference(c,recv)` | receiver reference relation | helper |
| `newArgument(n,arg)` | constructor argument relation | helper |
| `callTargetsCallable(c,callee)` | call target binding | helper |
| `isTaintedExpr(e)` | 标准 servlet taint expression | 污点型 checker |
| `isTaintedVar(v)` | 标准 servlet taint variable | 污点型 checker |
| `isXssTaintedExpr(e)` | 带 XSS barrier 语义的 taint expression | CWE-079 |
| `isXssTaintedVar(v)` | 带 XSS barrier 语义的 taint variable | CWE-079 |

## 6. 新 Checker 开发规则

1. 先判断是否需要 taint engine。
2. 注入类和 source-to-sink 漏洞默认复用 `JavaServletSources.gdl` 和 `TaintTracking.gdl`。
3. API misuse checker 不要强行使用 taint。
4. 新 checker 只新增 CWE-specific sink、sanitizer/barrier、scope filter 和 reporting ruleId。
5. 如果新增 source 是框架级输入，例如 Spring MVC `@RequestParam`，应扩展 source module，而不是写在单个 checker 里。
6. 如果新增 propagation 是通用传播规则，应进入 `TaintTracking.gdl`，并对所有 checker 做回归。
7. 如果只是某个 CWE 的特例，应进入对应 sink/sanitizer 模块。
8. 每个新 checker 应附带最小 Java 测试、benchmark/eval command 和实验报告。

## 7. 回归策略

每个阶段都应保存：

- 新 CSV 结果
- metrics.json
- hit-set diff
- TP / FP / FN
- Precision / Recall / F1
- changed testcase list

默认要求 hit-set 等价。任何 diff 都视为 regression，除非实验报告解释并人工确认。

## 8. 后续加固方向

- `SecurityReporting.gdl`
- `SinkHelpers.gdl`
- 统一 Java Web source 入口
- Spring MVC source 建模
- 标准 checker 模板
- 可解释 taint reason / debug path

## 9. PR 准备清单

- 每个 CWE 有简短 README 或 analysis report。
- query 和 module 注释清楚。
- minimal tests 存在。
- benchmark report 存在。
- 不使用 OWASP Benchmark testcase-name hack。
- 不使用具体行号 hack。
- 说明当前限制：path-insensitive、context-insensitive、heap/collection imprecision、printable-text matching。
