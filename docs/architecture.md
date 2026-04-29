# 架构设计

Java 规则包由少量共享框架模块和轻量的 CWE-specific checker 组成。

## 支持的 checker 类型

当前规则库支持四类 checker：

1. 污点型漏洞检查器
2. 注入类检查器
3. API 误用 / 密码学检查器
4. Web 配置 / 对象状态检查器

污点型 checker 复用共享 source model 和 taint propagation。API 误用和对象状态类 checker 主要依赖局部 API 谓词；只有 CWE 语义确实需要不可信数据流时才使用 taint。

## 公共模块

- `JavaServletSources.gdl`：Servlet 和 HTTP request source 建模。
- `TaintHelpers.gdl`：调用实参、receiver、构造函数参数、call target 等 helper 谓词。
- `TaintTracking.gdl`：共享 broad taint propagation engine。
- `sinks/*.gdl`：CWE-specific sink/API 模型。
- `sanitizers/*.gdl`：CWE-specific sanitizer、barrier 和 scope filter。

## checker 使用方式

复用 `TaintTracking.gdl` 的 checker：

- CWE-022 路径遍历
- CWE-078 命令注入
- CWE-079 XSS
- CWE-089 SQL 注入
- CWE-090 LDAP 注入
- CWE-643 XPath 注入
- CWE-501 信任边界违规

不以 `TaintTracking.gdl` 作为主要机制的 checker：

- CWE-327 危险或不安全加密算法
- CWE-328 弱哈希算法
- CWE-330 随机数不足
- CWE-614 敏感 Cookie 缺少 Secure 标志

## 数据流形态

污点型分析遵循：

`Source` -> `TaintTracking` -> `Sink` -> `Sanitizer / Scope Filter`

如果 `TaintTracking.gdl` 能把 source 连接到 sink，就报告 finding；除非 CWE-specific sanitizer、barrier 或 scope filter 明确抑制。

API 误用分析遵循：

`API Call / Constructor` -> `CWE-specific Predicate` -> `Finding`

这类 checker 直接报告不安全 API 使用，例如弱加密算法、弱哈希、弱随机 API 或 Cookie 安全配置缺失。

## 设计原则

- 新 checker 应保持 thin：`checkerXXX.gdl` 主要负责连接 source、sink、sanitizer 和 reporting。
- 可复用的 CWE-specific API 建模应放在 `sinks/*.gdl` 或 `sanitizers/*.gdl` 中。
- 不复制 taint propagation 逻辑；注入和数据流类 checker 应调用 `TaintTracking.gdl`。
- 不要把 taint tracking 强行用于 API 误用 checker。
- CWE-specific suppression 和 scope filter 应留在对应 sanitizer 或 sink 模块。
- `TaintTracking.gdl`、`JavaServletSources.gdl`、`TaintHelpers.gdl` 等公共模块只有在完成全量回归后才应修改。
