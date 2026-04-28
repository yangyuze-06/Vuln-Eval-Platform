# 架构设计

## 模块结构
框架被组织为核心库中可复用的组件：

- **JavaServletSources**: 建模标准的 HTTP 请求输入 API（参数、Header、Cookie）。
- **TaintHelpers**: 提供调用参数、接收者（receiver）和构造函数绑定的通用谓词。
- **TaintTracking**: 核心递归引擎，负责在程序中传播污点。
- **sinks/* **: 特定漏洞的汇点模型（例如 `PathTraversalSinks`, `CommandInjectionSinks`）。
- **sanitizers/* **: 验证和清理逻辑，用于阻断污点流（例如 `XssSanitizers`）。

## 数据流
分析遵循线性逻辑流：
**来源 (Source)** (用户输入) → **污点追踪 (Taint Tracking)** (数据传播) → **汇点 (Sink)** (敏感 API)

任何通过 **污点追踪** 引擎连接 **来源** 到 **汇点** 的路径都将被报告为潜在漏洞，除非该路径遇到了 **清洗器 (Sanitizer)**。
