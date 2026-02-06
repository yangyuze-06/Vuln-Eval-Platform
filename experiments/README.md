# Experiments 实验说明

本目录用于说明漏洞检测评测实验的整体流程与结构设计。

该实验框架主要用于对 **CodeQL、CodeFuse 等静态分析工具**
在 **OWASP Benchmark 数据集** 上的检测效果进行统一评测。

---

## 一、实验总体流程

每个 CWE 实验统一遵循如下流程：

1. 构建静态分析数据库  
2. 执行漏洞检测规则  
3. 导出 SARIF 检测结果  
4. 将 SARIF 转换为 CSV 格式  
5. 与 OWASP Benchmark Ground Truth 进行比对  
6. 统计评测指标：

- TP（真实检测出的漏洞数量）
- FP（误报数量）
- FN（漏报数量）
- Precision（检测准确率）
- Recall（漏洞召回率）
- FNR（漏报率）
- FPR（误报率）
- FDR（误检率）

---

## 二、实验目录结构说明

推荐项目结构如下：



本项目采用统一实验结构，结构如下：

SECURITY-EVAL-LAB
│
├── dataset
│ └── benchmark
│ ├── src # OWASP Benchmark 源码
│ ├── data # Benchmark 配置文件
│ └── pom.xml # Maven 构建文件
│
├── rules
│ ├── codeql-query # CodeQL 规则
│ └── codefuse-query # CodeFuse 规则
│
├── scripts
│ ├── sarif_to_csv.py
│ ├── aggregate_results.py
│ └── eval_xxx.py
│
├── experiments
│ ├── README.md
│ └── cwe-xxx # 单 CWE 实验目录（通过 create.sh 创建）
│
├── reports
| └── summary.json # 评测结果汇总
|
├── expectedresults-1.2.csv
|
---

## 三、CodeQL 实验执行流程

### 1. 构建数据库

示例：
codeql database create owasp-benchmark-db
--language=java
--source-root=/Security-Eval-Lab/dataset/codeql-db

可以放在dataset/codeql-db文件下
---

### 2. 执行规则检测

示例：CWE-089 SQL 注入检测：

codeql database analyze owasp-benchmark-db
rules/codeql-query/CWE-089
--format=sarifv2.1.0
--output=results/cwe089.sarif


---

## 四、CodeFuse 实验执行流程

### 1. 构建数据库

示例：
cd ~/Security-Eval-Lab
sparrow database create \
  -s ~/Security-Eval-Lab/dataset/benchmark/src/main/java \
  -lang java \
  -o ~/Security-Eval-Lab/dataset/codefuse-db

可以放在dataset/codefuse-db文件下

### 2. 执行规则检测
（根据 Sparrow CLI 工具进行规则执行）

示例：

sparrow query run \
  --database dataset/codefuse-db \
  --query rules/codefuse-query/CWE-089 \
  --output results/codefuse_cwe089.sarif


---

## 五、结果转换与评测

### 1. SARIF 转 CSV

python3 scripts/sarif_to_csv.py

---

### 2. 单 CWE 评测

python3 scripts/eval_codeql_cwe.py

---

### 3. 汇总评测结果

python3 scripts/aggregate_results.py

---

## 六、实验结果说明

实验过程中会生成：

- SARIF 检测结果
- CSV 格式检测结果
- 统计指标结果

由于结果文件体积较大，本仓库不包含完整实验输出文件。

用户可通过上述流程自行复现实验结果。

---

## 七、支持评测 CWE 类型

当前实验覆盖如下漏洞类型：

- CWE-022
- CWE-078
- CWE-079
- CWE-089
- CWE-090
- CWE-327
- CWE-328
- CWE-330
- CWE-501
- CWE-614
- CWE-643
