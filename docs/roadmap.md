# 路线图

## 1. 当前状态

CodeFuse Security Rule Pack 已经具备可复用的 Java 安全规则框架：

- 模块化 source model：`JavaServletSources.gdl`
- 模块化 helper layer：`TaintHelpers.gdl`
- 模块化 taint engine：`TaintTracking.gdl`
- CWE-022 / CWE-078 / CWE-079 / CWE-089 的 sink 模块
- sanitizer 模块和占位实现
- 支持本地 package path 的可复现 runner
- 已有 checker：
  - CWE-022 Path Traversal
  - CWE-078 Command Injection
  - CWE-079 XSS
  - CWE-089 SQL Injection

## 2. 短期路线：更多 Checker

下一阶段优先新增更多 checker，用来验证该框架在不同漏洞类型中的复用能力。

候选 checker：

- CWE-090
- CWE-327
- CWE-328
- CWE-330
- CWE-501
- CWE-614
- CWE-643

新增 checker 的开发规则：

- 必须复用 `JavaServletSources.gdl` 和 `TaintTracking.gdl`。
- 不允许复制 `is_tainted_expr` / `is_tainted_var`。
- 只新增 CWE-specific sink 和 sanitizer 模块。
- 先以 recall-first 的方式补齐 sink 覆盖。
- 只有在完成 TP / FP / FN 评测后，才进入 precision patch。

## 3. 中期路线：框架加固

框架加固的目标是让 checker 编写更一致，并减少重复 wrapper 代码：

- `SecurityReporting.gdl`
- `SinkHelpers.gdl`
- `JavaWebSources.gdl`，作为统一的 source 入口
- `SpringMvcSources.gdl`，用于 Spring Boot 注解建模
- 标准 checker 模板
- 稳定的评测脚本和 package path 处理

## 4. 长期路线：精度研究

剩余 false positives 不只是规则定义问题，很多需要比当前 broad taint engine 更强的静态分析精度。

研究方向：

- 局部 strong update
- collection/key-sensitive taint
- 简单分支裁剪
- field-sensitive taint
- context-sensitive helper modeling
- 可解释 taint reason / debug path

这些实验应放在隔离分支中进行。没有跨 checker 回归证据前，不应直接合入主线 `TaintTracking.gdl`。

## 5. 实验策略

- 主分支优先保证稳定、可复用的 checker 框架。
- precision 实验应隔离进行，并且易于回滚。
- 任何 `TaintTracking.gdl` 修改都必须对所有已有 checker 跑回归。
- benchmark-specific suppression 必须明确标记为 benchmark-only。
- 每个 checker patch 都必须报告 TP / FP / FN / Precision / Recall / F1。

## 6. 里程碑

M1:

- 4 个稳定 checker：CWE-022 / CWE-078 / CWE-079 / CWE-089

M2:

- 6 个使用同一框架的稳定 checker

M3:

- 统一 Java Web source model

M4:

- 第一个不破坏已有 checker 的 precision extension

M5:

- 可 upstream 的 rule pack / 可用于作品集展示的技术报告
