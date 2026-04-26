# 💡 Idea: 向 CodeFuse-Query 官方贡献高级漏洞规则库 (PR)

## 背景 (Background)
CodeFuse-Query 作为一个强大的开源代码属性图（CPG）引擎，其基础架构极其优秀。然而，开源社区目前普遍缺乏**工业级、开箱即用的高级安全漏洞检测规则（Checkers）**。我们基于 OWASP Benchmark 历经实战打磨、具有 100% 召回率和极高精确度的 CWE-078 和 CWE-022 规则，具有巨大的开源贡献价值。

## 目标 (Objective)
通过 Pull Request (PR) 向 CodeFuse-Query 官方仓库贡献高质量的安全规则，填补官方规则库的生态空白，同时建立我们在静态程序分析 (SAST) 和 DevSecOps 领域的开源技术影响力。

## 执行路径 (Execution Plan)

这套重构思想深度借鉴了 **CodeQL** 的标准化模块设计，将“底层的污点传播引擎”与“上层的特定漏洞检测逻辑”彻底解耦。

### 1. 核心解耦与模块化重构 (Refactoring & Modularization)
目前 `checker022.gdl` 和 `checker078.gdl` 中都冗余了约 200 多行的通用污点传播逻辑（如 `is_tainted_var`、`is_tainted_expr`、跨函数调用追踪等）。
- **做法**：新建一个底层公共数据流/污点追踪库（例如命名为 `TaintTracking.gdl` 或 `JavaServletTaint.gdl`）。
- **效果**：未来的漏洞检测脚本只需要通过 `use TaintTracking;` 引入底层追踪能力，然后仅仅定义自己专属的 Sink（执行点，如 `Runtime.exec` 或 `new File`）。这能让单个漏洞规则的代码量从近 400 行锐减至 50 行左右，架构极具专业性与扩展性。

### 2. 泛化污点源模型 (Generalize Source Modeling)
- 目前的 Source 引擎完美覆盖了标准的 Java EE Servlet API (`request.getParameter`, `request.getCookies` 等)。
- **做法**：在向官方提交 PR 时，可以在规则注释和 README 中清晰界定其适用范围（"This rule pack supports standard Java EE Servlet API taint sources."）。未来甚至可以很方便地在这个模块里平滑扩充 Spring Boot Annotations (`@RequestParam`, `@PathVariable` 等) 的识别支持。

### 3. 准备开源审查的测试用例 (Test Cases for PR Review)
官方 Reviewer 在合并 PR 前需要进行严格的回归测试与验证。
- **做法**：随 PR 附带准备 2-3 个极简的 Java 测试文件：
  - `TestTP.java`: 包含跨越多个函数的真实命令注入代码（证明 Inter-procedural 污点追踪能力有效）。
  - `TestFP.java`: 包含使用安全数据源或污点流断裂的代码（证明规则不只是一顿乱报，具备极佳的 Precision）。

## 预期收益 (Expected Impact)
- **繁荣开源生态**：为 CodeFuse 补齐企业级安全分析的 "Zero to One" 关键拼图。
- **打造技术护城河**：成为顶尖底层编译原理/安全图引擎项目的核心代码贡献者。
- **架构能力升维**：将团队的静态规则开发能力，正式从“实验室写脚本”拉升至“CodeQL 级别的模块化架构师”水准！
