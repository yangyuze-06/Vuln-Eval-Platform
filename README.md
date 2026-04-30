# Vuln-Eval-Lab 🔐
### Static Analysis Evaluation Lab & Java SAST Checker Rule Pack

![License](https://img.shields.io/badge/license-MIT-green)
![Status](https://img.shields.io/badge/status-active-success)
![Python](https://img.shields.io/badge/python-3.8+-blue)
![JDK](https://img.shields.io/badge/JDK-17+-orange)
![OWASP](https://img.shields.io/badge/OWASP-Benchmark-important)
![CodeQL](https://img.shields.io/badge/CodeQL-supported-red)
![CodeFuse--Query](https://img.shields.io/badge/CodeFuse--Query-supported-blueviolet)
![GodelScript](https://img.shields.io/badge/GodelScript-rule%20pack-purple)
![Java SAST](https://img.shields.io/badge/Java-SAST-orange)
![Security Research](https://img.shields.io/badge/security-research-blue)
![Created by L1ngSh1](https://img.shields.io/badge/Created%20by-L1ngSh1-purple)

---

## 📌 项目简介

**Vuln-Eval-Lab** 最初用于统一评测 **CodeQL**、**CodeFuse-Query** 等静态分析工具在 **OWASP Benchmark** 上的表现，提供结果标准化、ground truth 对比和指标统计能力。

在评测过程中，项目进一步发展出一套基于 **CodeFuse-Query / GodelScript** 的模块化 **Java SAST checker rule pack**。因此项目现在包含两条主线：

1. 多工具静态分析评测 pipeline
2. GodelScript Java security checker rule pack

本项目面向安全研究、规则开发和可复现实验，不改变早期多工具评测平台的定位。

---

## ✅ 当前状态

- 已完成 11 个 CWE checker
- 当前 11 个 checker 在 OWASP Benchmark 上 Recall 均为 1.0000
- 已形成 source / helper / taint / sink / sanitizer 模块化框架
- 已支持 `eval_checker.sh <CWE>` 单 CWE 可复现评测
- CodeQL / SARIF 评测能力作为多工具评测 pipeline 保留
- 当前阶段重点进入 regression、packaging、precision research

---

## 🧪 已完成 Checker

| CWE | 名称 | 类型 | Precision | Recall | F1 |
| --- | --- | --- | ---: | ---: | ---: |
| CWE-022 | 路径遍历 | Taint-based | 0.5519 | 1.0000 | 0.7112 |
| CWE-078 | 命令注入 | Taint-based | 0.5650 | 1.0000 | 0.7221 |
| CWE-079 | XSS | Taint-based | 0.7193 | 1.0000 | 0.8367 |
| CWE-089 | SQL 注入 | Injection | 0.6445 | 1.0000 | 0.7839 |
| CWE-090 | LDAP 注入 | Injection | 0.5510 | 1.0000 | 0.7105 |
| CWE-643 | XPath 注入 | Injection | 0.4545 | 1.0000 | 0.6250 |
| CWE-327 | 危险加密算法 | API misuse | 0.8280 | 1.0000 | 0.9059 |
| CWE-328 | 弱哈希算法 | API misuse | 0.9922 | 1.0000 | 0.9961 |
| CWE-330 | 随机数不足 | API misuse | 1.0000 | 1.0000 | 1.0000 |
| CWE-614 | Cookie Secure Flag 缺失 | Web config | 1.0000 | 1.0000 | 1.0000 |
| CWE-501 | 信任边界违规 | Object-state | 0.7094 | 1.0000 | 0.8300 |

完整 TP / FP / FN 见 [docs/results.md](docs/results.md)。

---

## 🧩 架构概览

```text
OWASP Benchmark
   ↓
CodeFuse database / CodeQL database
   ↓
Rules
   ├── CodeFuse-Query / GodelScript checkers
   └── CodeQL queries
   ↓
Result normalization
   ├── CodeFuse JSON → CSV
   └── CodeQL SARIF → CSV
   ↓
Ground truth comparison
   ↓
Metrics / TP / FP / FN
```

Godel rule pack 内部结构：

```text
JavaServletSources.gdl
   ↓
TaintHelpers.gdl
   ↓
TaintTracking.gdl
   ↓
CWE-specific sinks/*.gdl
   ↓
CWE-specific sanitizers/*.gdl
   ↓
checkerXXX.gdl
```

- taint-based checker 复用 `TaintTracking`
- API misuse checker 不强行使用 taint
- `checkerXXX.gdl` 保持 thin checker 风格

更多架构说明见 [docs/architecture.md](docs/architecture.md)。

---

## ⚡ 快速开始

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

运行单个 CodeFuse-Query / GodelScript checker：

```bash
./scripts/evaluation/eval_checker.sh 089
```

运行统一评测入口：

```bash
./run_eval.sh
```

CodeQL / CodeFuse 实验命令、结果转换和报告生成流程见 [docs/evaluation_workflow.md](docs/evaluation_workflow.md)。新增 checker 的流程见 [docs/how_to_add_checker.md](docs/how_to_add_checker.md)。

---

## 📂 项目结构

```text
Vuln-Eval-Lab
├── dataset/                  # OWASP Benchmark 与分析数据库
├── rules/
│   ├── codefuse-query/       # GodelScript Java checker rule pack
│   └── codeql-query/         # CodeQL queries
├── experiments/              # 各 CWE 实验结果与评测输出
├── scripts/
│   ├── converters/           # JSON / SARIF 到 CSV 转换
│   ├── evaluation/           # 指标评测与 runner
│   └── reporting/            # 汇总与报告
├── docs/                     # 架构、运行、结果与扩展文档
├── reports/                  # 汇总报告与图表
├── run_eval.sh
├── requirements.txt
└── expectedresults-1.2.csv
```

---

## 🎯 适用场景

- 评测 CodeQL、CodeFuse-Query 等静态分析工具在 OWASP Benchmark 上的表现
- 开发和回归验证 Java SAST checker
- 研究 checker precision / recall trade-off
- 构建可复现的安全规则实验流程

---

## 📚 文档

- [架构说明](docs/architecture.md)
- [评测结果](docs/results.md)
- [实验与评测流程](docs/evaluation_workflow.md)
- [运行 CodeFuse-Query checker](docs/run_codefuse_queries.md)
- [新增 checker 指南](docs/how_to_add_checker.md)
- [路线图](docs/roadmap.md)

---

## 🤝 贡献指南

欢迎提交 Issue 或 Pull Request 参与项目改进。适合贡献的方向包括新增 CWE checker、优化现有 checker precision、完善评测脚本和补充实验文档。

---

## 📄 License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

---

## 👨‍💻 Author

Created by **L1ngSh1**.
