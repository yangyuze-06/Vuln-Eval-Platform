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

## 主要文档

- `architecture.md`：当前规则框架架构。
- `results.md`：已完成 checker 的评测结果。
- `roadmap.md`：后续稳定化、封装和精度研究路线。
- `how_to_add_checker.md`：新增 checker 的模板和约束。
- `run_codefuse_queries.md`：本地运行 CodeFuse-Query 规则的方法。
- `refactor_plan.md`：早期模块化重构计划归档。
