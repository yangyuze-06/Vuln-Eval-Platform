# 🔐 SECURITY-EVAL-LAB

![License](https://img.shields.io/badge/license-MIT-green)
![Python](https://img.shields.io/badge/python-3.8+-blue)
![CodeQL](https://img.shields.io/badge/CodeQL-supported-red)
![Static Analysis](https://img.shields.io/badge/static-analysis-framework-orange)

---

## 📌 项目简介

**SECURITY-EVAL-LAB** 是一个面向安全研究的静态分析评测框架，
用于统一评估不同漏洞检测工具在 **OWASP Benchmark 数据集** 上的检测能力。

本项目支持：

- CodeQL 静态分析评测
- CodeFuse 静态分析评测
- 多 CWE 漏洞检测对比
- 自动化评测指标统计
- 可复现实验流程设计

该框架旨在解决不同安全工具之间缺乏统一评测标准的问题，
提供工程化、可扩展的漏洞检测评测平台。

⚠ 本项目主要用于安全研究与工具评测实验。

---

## 🧩 系统架构

```

OWASP Benchmark Source Code
│
▼
Static Analysis Database
│
▼
Detection Rules Execution
(CodeQL / CodeFuse Query)
│
▼
SARIF Result Export
│
▼
SARIF → CSV Conversion
│
▼
Ground Truth Comparison
│
▼
Evaluation Metrics Output

```

---

## 🎯 项目目标

- 构建统一漏洞检测评测框架  
- 对比不同静态分析工具检测能力  
- 提供自动化评测流程  
- 支持安全研究实验复现  
- 提供可扩展规则管理体系  

---

## 📂 项目结构

```

SECURITY-EVAL-LAB
│
├── dataset
│   └── benchmark              # OWASP Benchmark 数据集源码
│
├── rules
│   ├── codeql-query           # CodeQL 检测规则
│   └── codefuse-query         # CodeFuse 检测规则
│
├── scripts                    # 实验评测脚本
│   ├── sarif_to_csv.py
│   ├── eval_codeql_cwe.py
│   └── aggregate_results.py
│
├── experiments                # 实验执行目录
│   ├── create.sh              # 实验目录自动生成脚本
│   └── cwe-xxx                # 单 CWE 实验目录
│
├── reports                    # 实验结果统计输出
│
└── requirements.txt

```

更多实验流程说明请参考：

```

experiments/README.md

````

---

# ⚙️ 环境配置

建议使用 Python 虚拟环境运行本项目。

### 📦 依赖环境

- Python 3.8+
- CodeQL CLI
- Sparrow / CodeFuse CLI

---

## 🐍 Python 环境配置

### 1. 创建虚拟环境

```bash
python3 -m venv .venv
````

---

### 2. 激活虚拟环境

```bash
source .venv/bin/activate
```

激活成功后终端将显示：

```
(.venv)
```

---

### 3. 安装 Python 依赖

```bash
pip install -r requirements.txt
```

---

### 4. 退出虚拟环境

```bash
deactivate
```

---

## 🔧 安装 CodeQL

参考官方文档：

[https://codeql.github.com/docs/codeql-cli/](https://codeql.github.com/docs/codeql-cli/)

---

## 🔧 安装 CodeFuse / Sparrow

请参考对应工具官方安装说明。

---

# ⚡ Quick Start

```bash
git clone https://github.com/L1ngSh1/SECURITY-EVAL-LAB.git
cd SECURITY-EVAL-LAB

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt

cd experiments
bash create.sh
```

---

# 🧪 实验流程

每个 CWE 实验统一遵循以下流程：

1. 构建静态分析数据库
2. 执行漏洞检测规则
3. 导出 SARIF 检测结果
4. SARIF 转 CSV
5. Ground Truth 对比
6. 统计评测指标

---

# 📊 评测指标

本项目采用标准漏洞检测评测指标体系：

| 指标        | 含义       |
| --------- | -------- |
| TP        | 真实检测漏洞数量 |
| FP        | 误报数量     |
| FN        | 漏报数量     |
| Precision | 检测准确率    |
| Recall    | 漏洞召回率    |
| FNR       | 漏报率      |
| FPR       | 误报率      |
| FDR       | 误检率      |

---

# 🔍 CodeQL 实验示例

## 构建数据库

```bash
codeql database create owasp-benchmark-db \
  --language=java \
  --source-root=dataset/benchmark
```

---

## 执行规则检测

```bash
codeql database analyze owasp-benchmark-db \
  rules/codeql-query/CWE-089 \
  --format=sarifv2.1.0 \
  --output=experiments/cwe-089/results/codeql/cwe089.sarif
```

---

# 🔍 CodeFuse 实验示例

## 构建数据库

```bash
sparrow database create \
  -s dataset/benchmark/src/main/java \
  -lang java \
  -o dataset/codefuse-db
```

---

## 执行规则检测

```bash
sparrow query run \
  --database dataset/codefuse-db \
  --query rules/codefuse-query/CWE-089 \
  --output experiments/cwe-089/results/codefuse-query/cwe089.sarif
```

---

# 📁 结果分析

## SARIF 转 CSV

```bash
python scripts/sarif_to_csv.py
```

---

## 单 CWE 评测

```bash
python scripts/eval_codeql_cwe.py
```

---

## 汇总统计结果

```bash
python scripts/aggregate_results.py
```

实验统计结果将输出至：

```
reports/
```

---

# 📌 当前支持 CWE 类型

* CWE-022
* CWE-078
* CWE-079
* CWE-089
* CWE-090
* CWE-327
* CWE-328
* CWE-330
* CWE-501
* CWE-614
* CWE-643

---

# 📈 项目特点

* 工程化漏洞评测框架
* 支持多工具统一评测
* 支持自动指标统计
* 支持实验复现
* 支持规则模块化管理

---

# 🚧 未来规划

* 支持更多静态分析工具
* 增加评测可视化模块
* 支持自动实验执行流水线
* 支持 ROC / PR 曲线分析
* 构建漏洞检测规则基准库

---

# 🤝 贡献指南

欢迎提交 Issue 或 Pull Request 参与项目改进。

---

# 📄 License

This project is licensed under the MIT License.

---

## 👨‍💻 作者：
L1ngSh1
