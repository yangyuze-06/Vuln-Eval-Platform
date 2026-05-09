# Vuln-Eval-Platform 🔐
### Security Evaluation Lab for Static Analysis Tools

[👉 点击这里查看中文版本 (Chinese Version)](docs/README_zh-CN.md)

![License](https://img.shields.io/badge/license-MIT-green)
![OWASP](https://img.shields.io/badge/OWASP-Benchmark-important)
![Created by L1ngSh1](https://img.shields.io/badge/Created%20by-L1ngSh1-purple)

---

## 📌 Project Introduction

**Vuln-Eval-Platform** is a static analysis evaluation framework oriented towards security research.
It is used to uniformly evaluate the detection capabilities of different vulnerability detection tools on the **OWASP Benchmark dataset**.

This project supports:

- Evaluation of the CodeQL static analysis tool
- Evaluation of the CodeFuse-Query static analysis tool
- Comparison of multi-CWE vulnerability detection
- Automated statistical analysis of evaluation metrics
- Reproducible experimental process design

This framework aims to solve the problem of lacking a unified evaluation standard among different security tools,
providing an engineered, scalable platform for vulnerability detection evaluation.

⚠ This project is primarily used for security research and tool evaluation experiments.

---

## 🆕 Release Notes

### v2.0 (Current Version)

- Completed 11 CodeFuse-Query / GodelScript Java SAST checkers.
- Established a modular rule framework for `source / helper / taint / sink / sanitizer`.
- Added unified evaluation entry point: `scripts/evaluation/eval_checker.sh <CWE>`.
- The current 11 checkers have all achieved `Recall = 1.0000` on the OWASP Benchmark.
- The project has entered the regression, packaging, and precision research stages.

### v1.1

- Refined the early automated evaluation process.
- Added `run_eval.sh`, result conversion, metrics aggregation, and basic report generation.

### v1.0

- Integrated the OWASP Benchmark.
- Completed the basic architecture of the static analysis tool evaluation platform.
- Supported CodeQL / CodeFuse result normalization and single-CWE evaluation.

---

## 🧩 System Architecture

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
Detection Result Export
(CodeQL SARIF / CodeFuse JSON)
│
▼
Result Normalization
(SARIF → CSV / JSON → CSV)
│
▼
Ground Truth Comparison
│
▼
Evaluation Metrics Output
```

---

## 🎯 Project Goals

- Build a unified vulnerability detection evaluation framework
- Compare the detection capabilities of different static analysis tools
- Provide automated evaluation workflows
- Support the reproduction of security research experiments
- Provide an extensible rule management system

---

## 📂 Project Structure

```
Vuln-Eval-Lab
│
├── dataset                    # Datasets and Analysis Databases
│   ├── benchmark              # OWASP Benchmark source code
│   │   ├── data
│   │   ├── src
│   │   └── target
│   ├── codeql-db              # CodeQL databases and results
│   │      
│   └── codefuse-db            # CodeFuse database directory
│
├── rules                      # Detection Rules
│   ├── codeql-query           # CodeQL rules for each CWE
│   └── codefuse-query         # CodeFuse rules for each CWE
│
├── experiments                # Experiment Directory
│   ├── cwe-022 ~ cwe-643      # Experiments for each CWE
│   │   ├── eval
│   │   ├── logs
│   │   └── results
│   └── examples               # Example experiments
│
├── scripts                    # Scripts Directory (grouped by function)
│   ├── converters             # Result format conversion
│   ├── evaluation             # Metric evaluation and calculation
│   └── reporting              # Chart and report generation
├── reports                    # Output Results
│   ├── data
│   └── figs
│
├── run_eval.sh                # One-click evaluation entry point
├── requirements.txt
├── expectedresults-1.2.csv    # Benchmark expected results
├── LICENSE
└── README.md
```

For more details on the experimental process, please refer to:

```
experiments/README.md
```

---

## 🔧 Install CodeQL

Refer to the official release page:

[https://github.com/github/codeql-cli-binaries/releases](https://github.com/github/codeql-cli-binaries/releases)

---

## 🔧 Install CodeFuse / Sparrow

[https://github.com/codefuse-ai/CodeFuse-Query](https://github.com/codefuse-ai/CodeFuse-Query)

---

# ⚡ Quick Start

```bash
git clone https://github.com/yangyuze-06/Vuln-Eval-Platform.git
cd Vuln-Eval-Platform

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt

# Evaluate a specific CWE (e.g., CWE-022)
bash scripts/evaluation/eval_checker.sh cwe-022

# Or run the one-click evaluation for all results
./run_eval.sh
```

---

## ⚡ One-Click Evaluation (Recommended in v1.1)

After completing the detection and generating SARIF files:

```bash
./run_eval.sh
```

This command will automatically:

* Check if SARIF files are complete
* Aggregate metrics for each CWE
* Generate performance visualization charts
* Output English evaluation report
* Output Chinese evaluation report

Result output locations:

```
reports/data/metrics.json
reports/figs/
reports/report.md
reports/report_zh.md
```

---

# 🧪 Experimental Workflow

Each CWE experiment uniformly follows these steps:

1. Build static analysis database
2. Execute vulnerability detection rules
3. Export detection results (CodeQL: SARIF, CodeFuse: JSON)
4. Normalize results to CSV
5. Ground Truth comparison
6. Calculate evaluation metrics

---

# 📊 Evaluation Metrics

This project uses a standard vulnerability detection evaluation metric system:

| Metric    | Meaning |
| --------- | -------- |
| TP        | True Positive (detected vulnerabilities) |
| FP        | False Positive (false alarms) |
| FN        | False Negative (missed vulnerabilities) |
| Precision | Detection Precision |
| Recall    | Vulnerability Recall |
| FNR       | False Negative Rate |
| FPR       | False Positive Rate |
| FDR       | False Discovery Rate |

---

# 📌 Currently Supported CWE Types

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

# 📈 Project Features

* Engineered vulnerability evaluation framework
* Supports unified evaluation of multiple tools
* Supports automatic metric calculation
* Supports experimental reproduction
* Supports modular rule management
* Supports one-click automatic evaluation pipeline (v1.1)
* Supports automatic generation of bilingual reports (English/Chinese)
* Supports performance visualization analysis

---

# 🚧 Future Plans

* Support more static analysis tools
* Add evaluation visualization modules
* Support automated experiment execution pipelines
* Support ROC / PR curve analysis
* Build a vulnerability detection rule benchmark library

---

# 📄 License

This project is released under the MIT Open Source License.
You are free to use, modify, and distribute this project under the terms of the license.
Please see the [LICENSE](LICENSE) file for complete license contents.

---

## 👨‍💻 Author

L1ngSh1

---

## ✍️ Author's Notes

This project originally stemmed from the author's thoughts during a security research internship regarding the lack of standardized evaluation methods for different static analysis tools.

The goal of Vuln-Eval-Platform is to build a structured, extensible, and reproducible vulnerability detection evaluation framework, allowing researchers to more systematically analyze the detection performance of static analysis tools on real vulnerability datasets.

This project is both a platform for research experiments and a record of the author's exploration in security research and engineering practices.

The project is still continuously evolving. Researchers interested in static analysis and vulnerability detection are welcome to participate in improving it, proposing suggestions, or contributing rules.

It would be a great comfort to the author if this project could be helpful in security research or teaching.
