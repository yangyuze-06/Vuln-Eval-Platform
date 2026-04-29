# Vuln-Eval-Lab docs

## 简介
本项目是一个**模块化 SAST 规则框架**，旨在实现高精度的漏洞检测。它通过将核心分析逻辑与特定的漏洞模式解耦，提供了一种结构化的静态分析规则构建方法。

## 支持的漏洞类型
目前框架支持：
- **CWE-022**: 路径遍历 (Path Traversal)
- **CWE-078**: 操作系统命令注入 (OS Command Injection)
- **CWE-079**: 跨站脚本攻击 (XSS)
- **CWE-089**: 数据库查询注入 (SQL Injection)

## 架构概览
框架遵循**解耦架构**：
- **来源建模 (Source Modeling)**：标准化的请求输入入口点。
- **污点追踪 (Taint Tracking)**：共享的、递归的数据流引擎。
- **汇点建模 (Sink Modeling)**：特定漏洞的敏感执行点。
