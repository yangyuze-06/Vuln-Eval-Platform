# Vuln-Eval-Platform 🔐
### Security Evaluation Lab for Static Analysis Tools


![License](https://img.shields.io/badge/license-MIT-green)
![Status](https://img.shields.io/badge/status-active-success)
![Python](https://img.shields.io/badge/python-3.8+-blue)
![JDK](https://img.shields.io/badge/JDK-17+-orange)
![CodeQL](https://img.shields.io/badge/CodeQL-supported-red)
![OWASP](https://img.shields.io/badge/OWASP-Benchmark-important)
![Security Research](https://img.shields.io/badge/security-research-blue)
![Evaluation](https://img.shields.io/badge/framework-evaluation-important)
![Debut Project](https://img.shields.io/badge/project-debut-blueviolet)
![Created by L1ngSh1](https://img.shields.io/badge/Created%20by-L1ngSh1-purple)

---

## 📌 项目简介

**SECURITY-EVAL-LAB** 是一个面向安全研究的静态分析评测框架，
用于统一评估不同漏洞检测工具在 **OWASP Benchmark 数据集** 上的检测能力。

本项目支持：

- CodeQL 静态分析工具评测
- CodeFuse-Query 静态分析工具评测
- 多 CWE 漏洞检测对比
- 自动化评测指标统计
- 可复现实验流程设计

该框架旨在解决不同安全工具之间缺乏统一评测标准的问题，
提供工程化、可扩展的漏洞检测评测平台。

⚠ 本项目主要用于安全研究与工具评测实验。

---

## 🆕 版本说明

### v1.1（当前版本）

- 新增一键评估入口 `run_eval.sh`
- 自动检测各 CWE 实验 SARIF 文件
- 新增scripts脚本
- 自动汇总 Precision / Recall / F1 等指标
- 自动生成性能可视化图表
- 自动输出英文报告与中文报告
- 完整评估流程无需手动逐脚本执行

### v1.0（平台基础版本）

SECURITY-EVAL-LAB 的首个完整版本，
实现了从 0 到 1 的漏洞检测评测平台搭建。

- 设计统一静态分析评测架构
- 接入 OWASP Benchmark 数据集
- 实现 SARIF 结果标准化处理流程
- 构建单 CWE 自动评测与统计机制
- 实现跨 CWE 汇总指标计算模块
- 建立可复现实验目录与执行流程
- 构建规则与实验结果的工程化管理体系

该版本使平台具备完整的静态分析工具评测能力，
能够独立支撑静态分析工具检测效果的系统化实验。


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
├── run_eval.sh                # ⭐ v1.1 一键评估入口
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
- Sparrow / CodeFuse-Query CLI
- Java JDK 17+

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

[https://github.com/codefuse-ai/CodeFuse-Query](https://github.com/codefuse-ai/CodeFuse-Query)

---

# ⚡ Quick Start

```bash
git clone https://github.com/yangyuze-06/SECURITY-EVAL-LAB.git
cd SECURITY-EVAL-LAB

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt

cd experiments
bash create.sh
```

---

## ⚡ 一键评估（v1.1 推荐）

在完成检测并生成 SARIF 文件后：

```bash
./run_eval.sh
```

该命令将自动：

* 检测 SARIF 文件是否齐全
* 汇总各 CWE 指标
* 生成性能可视化图
* 输出英文评估报告
* 输出中文评估报告

结果输出位置：

```
reports/data/metrics.json
reports/figs/
reports/report.md
reports/report_zh.md
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
  --source-root=dataset/benchmark \
  --command="mvn clean package -DskipTests -Dspotless.skip=true"
```

---

## 执行规则检测

```bash
codeql database analyze owasp-benchmark-db \
  rules/codeql-query/CWE-xxx \
  --format=sarifv2.1.0 \
  --output=experiments/cwe-xxx/results/codeql/cwexxx.sarif
```

---

# 🔍 CodeFuse 实验示例

## 构建数据库

```bash
sparrow database create \
  -s dataset/benchmark/src/main/java \
  -lang java \
  -o dataset/codefuse-db
  -overwrite
```

---

## 执行规则检测

```bash
sparrow query run \
  --database dataset/codefuse-db \
  --query rules/codefuse-query/CWE-089 \
  --output experiments/cwe-xxx/results/codefuse-query/cwexxx.sarif
```

---

# 📁 结果分析

## SARIF 转 CSV（v1.0 手动）

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

---

## ⭐ 自动评估流程（v1.1 推荐）

```bash
./run_eval.sh
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
* 支持一键自动评估 pipeline（v1.1）
* 支持自动生成中英双语报告
* 支持性能可视化分析

---

# 🚧 未来规划

* 关于codefuse-query的gdl查询还在建设中
* 支持更多静态分析工具
* 增加评测可视化模块
* 支持自动实验执行流水线
* 支持 ROC / PR 曲线分析
* 构建漏洞检测规则基准库

---

# 🤝 贡献指南

欢迎提交 Issue 或 Pull Request 参与项目改进。

---

# 📄 许可证

本项目基于 MIT 开源许可证发布
您可以在遵守许可证条款的前提下自由使用、修改和分发本项目
完整许可证内容请参见 [LICENSE](LICENSE) 文件

---

## 👨‍💻 作者：

L1ngSh1

---

## ✍️ 作者的碎碎念

本项目最初源于作者在安全研究实习期间，对不同静态分析工具评测方式缺乏统一标准的思考。

Vuln-Eval-Platform 的目标是构建一个结构化、可扩展、可复现的漏洞检测评测框架，使研究者能够更加系统地分析静态分析工具在真实漏洞数据集上的检测表现。

该项目既是一个研究实验平台，也记录了作者在安全研究与工程实践中的探索过程。

项目目前仍在持续演进中，欢迎对静态分析与漏洞检测感兴趣的研究者参与改进、提出建议或贡献规则。

如果本项目能够在安全研究或教学中提供帮助，将是作者非常欣慰的事情。

---