# 路线图

## 1. 当前状态

CodeFuse Security Rule Pack 已经具备可复用的 Java 安全 checker 框架，并完成 11 个 checker：

- CWE-022 路径遍历
- CWE-078 命令注入
- CWE-079 XSS
- CWE-089 SQL 注入
- CWE-090 LDAP 注入
- CWE-643 XPath 注入
- CWE-327 危险或不安全加密算法
- CWE-328 弱哈希算法
- CWE-330 随机数不足
- CWE-614 敏感 Cookie 缺少 Secure 标志
- CWE-501 信任边界违规

共享框架包括：

- `JavaServletSources.gdl`
- `TaintHelpers.gdl`
- `TaintTracking.gdl`
- CWE-specific `sinks/*.gdl`
- CWE-specific `sanitizers/*.gdl`
- 支持本地 package-root 的统一评测 runner

## 2. 短期路线：稳定化和封装

下一阶段重点不是继续堆 checker，而是稳定和封装规则包。

优先事项：

- 每次框架或精度改动后，对 11 个已完成 checker 跑全量回归。
- 统一 checker 模板、命名和输出约定。
- 封装规则包，补齐 setup、runner 用法和结果路径说明。
- benchmark-specific suppression 必须明确标记，并与 upstream-ready 逻辑区分。
- 对 Recall 已经 1.0000 的 checker 继续做 CWE-local precision patch。

未来候选 checker：

- CWE-601 Open Redirect
- CWE-094 Code Injection
- CWE-502 Deserialization

## 3. 中期框架加固

框架加固应减少 checker 样板代码，同时不破坏当前稳定边界：

- `SecurityReporting.gdl`
- `SinkHelpers.gdl`
- 统一 Java Web source 入口
- 可选 Spring MVC source 建模
- taint-based 和 API misuse 两类标准 checker 模板
- 覆盖所有已完成 checker 的稳定回归脚本

## 4. 长期精度研究

剩余 FP 往往需要比当前 broad taint engine 更强的静态分析精度。

研究方向：

- 局部 strong update
- collection/key sensitivity
- path-sensitive branch reasoning
- helper return precision
- field-sensitive taint
- context-sensitive helper modeling
- 可解释 taint reason / debug path 输出

不要在主线轻易修改 `TaintTracking.gdl`。任何公共 taint engine 改动都必须对所有已完成 checker 做回归。

## 5. 实验策略

- 主线优先保证稳定、可复用的 checker 行为。
- precision 实验应隔离、可度量、易回滚。
- CWE-specific suppression 应放在对应 CWE sink/sanitizer 模块。
- benchmark-specific suppression 必须标记为 benchmark-only。
- 每个 checker patch 都必须报告 TP / FP / FN / Precision / Recall / F1。

## 6. 里程碑

M1：

- 4 个稳定污点型 checker：CWE-022 / CWE-078 / CWE-079 / CWE-089

M2：

- 模块化注入类扩展：CWE-090 / CWE-643

M3：

- API 误用 checker 路线：CWE-327 / CWE-328 / CWE-330

M4：

- Web 配置和对象状态 checker 路线：CWE-614 / CWE-501

M5：

- 具备回归、封装和技术报告的稳定 rule pack
