# Vuln-Eval-Lab 文档

## 简介

本项目是一个模块化 Java SAST 规则框架，用于在 OWASP Benchmark 上开发、评测和迭代 CodeFuse-Query / GodelScript 安全检查器。项目目标是把公共 source、helper、taint engine 与 CWE-specific sink、sanitizer、scope filter 解耦，让新增规则保持轻量、可评测、可回归。

## 已支持的检查器

- CWE-022：路径遍历
- CWE-078：操作系统命令注入
- CWE-079：跨站脚本
- CWE-089：SQL 注入
- CWE-090：LDAP 注入
- CWE-643：XPath 注入
- CWE-327：危险或不安全加密算法
- CWE-328：弱哈希算法
- CWE-330：随机数不足
- CWE-614：敏感 Cookie 缺少 Secure 标志
- CWE-501：信任边界违规

## 架构概览

框架遵循解耦架构：

- 来源建模：统一建模 Servlet/request 输入入口。
- 污点追踪：共享递归数据流引擎。
- 汇点建模：每个 CWE 维护自己的敏感 API 模型。
- 清洗器和范围过滤：每个 CWE 维护自己的 sanitizer、barrier 和 scope filter。
- 评测流水线：统一将 Godel JSON 结果转换为 CSV，并与 ground truth 计算 TP / FP / FN / Precision / Recall / F1。

## 文档分类

### 当前状态

- [current/architecture.md](current/architecture.md)：当前规则框架架构。
- [current/results.md](current/results.md)：已完成 checker 的评测结果。
- [current/roadmap.md](current/roadmap.md)：后续稳定化、封装和精度研究路线。
- [current/refactor_status_report.md](current/refactor_status_report.md)：本轮重构推进状态整理。

### 操作指南

- [guides/evaluation_workflow.md](guides/evaluation_workflow.md)：CodeQL、CodeFuse-Query 实验命令与结果评测流程。
- [guides/run_codefuse_queries.md](guides/run_codefuse_queries.md)：本地运行 CodeFuse-Query 规则的方法。
- [guides/how_to_add_checker.md](guides/how_to_add_checker.md)：新增 checker 的模板和约束。
- [guides/codefuse_macos_jdk_setup.md](guides/codefuse_macos_jdk_setup.md)：macOS CodeFuse/Sparrow JDK 配置。
- [guides/QUICK_START_PHASE2.md](guides/QUICK_START_PHASE2.md)：Phase 2 v2 evaluator 快速使用和验证。

### 重构归档

- [refactor/PHASE1_SUMMARY.md](refactor/PHASE1_SUMMARY.md)：Phase 1 实施总结。
- [refactor/PHASE2_FINAL_SUMMARY.md](refactor/PHASE2_FINAL_SUMMARY.md)：Phase 2 完整收尾总结。
- [refactor/PHASE2_EVALUATION_CORE.md](refactor/PHASE2_EVALUATION_CORE.md)：Phase 2 统一评估核心设计。
- [refactor/PHASE2B_EVALUATOR_DETAILS.md](refactor/PHASE2B_EVALUATOR_DETAILS.md)：Phase 2B evaluator 细节。
- [refactor/PHASE3_PLAN.md](refactor/PHASE3_PLAN.md)：Phase 3 工具抽象层与统一实验入口计划（当前阶段）。
- [refactor/architecture_notes.md](refactor/architecture_notes.md)：早期架构诊断与路线图。
- [refactor/refactor_plan.md](refactor/refactor_plan.md)：早期模块化重构计划归档。

### 审计和排障

- [audits/CROSS_PLATFORM_REPRO_AUDIT.md](audits/CROSS_PLATFORM_REPRO_AUDIT.md)：跨平台复现审计。
- [audits/PARITY_M34_CODEFUSE_PIPELINE.md](audits/PARITY_M34_CODEFUSE_PIPELINE.md)：Phase 3 M3.4 pipeline 对齐审计。
- [audits/test_compare_cwe022_v2b_vs_v2.md](audits/test_compare_cwe022_v2b_vs_v2.md)：CWE-022 v2/v2b 对比。
- [audits/env_fingerprint_current.json](audits/env_fingerprint_current.json)：当前环境指纹。
- [audits/java-database/](audits/java-database/)：CodeFuse Java DB macOS/Linux 根因调查报告。

### 模板和参考

- [templates/analysis-template.md](templates/analysis-template.md)：CWE checker 分析模板。
- [godels-file/](godels-file/)：GödelScript 语言和工具链参考资料。
