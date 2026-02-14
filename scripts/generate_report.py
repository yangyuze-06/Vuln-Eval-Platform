import json
from pathlib import Path
from datetime import date   # 用于自动生成日期

BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_JSON = BASE_DIR / "reports" / "data" / "metrics.json"

OUTPUT_MD_EN = BASE_DIR / "reports" / "report.md"
OUTPUT_MD_ZH = BASE_DIR / "reports" / "report_zh.md"

with open(INPUT_JSON, "r", encoding="utf-8") as f:
    data = json.load(f)

overall = data["OVERALL"]["tools"]["codeql"]

precision = overall["precision"]
recall = overall["recall"]
f1 = overall["f1"]

# ===== 收集 CWE precision，用于分析最高/最低 =====
cwe_precisions = []

for cwe, info in data.items():
    if cwe == "OVERALL":
        continue
    if "tools" in info and "codeql" in info["tools"]:
        cwe_precisions.append((cwe, info["tools"]["codeql"]["precision"]))

# 排序方便计算最值
cwe_precisions.sort(key=lambda x: x[1])

min_precision = cwe_precisions[0][1]
max_precision = cwe_precisions[-1][1]

# 支持并列最高/最低
best_cwes = [cwe for cwe, p in cwe_precisions if abs(p - max_precision) < 1e-9]
worst_cwes = [cwe for cwe, p in cwe_precisions if abs(p - min_precision) < 1e-9]

best_precision = max_precision
worst_precision = min_precision

best_cwe_str = ", ".join(best_cwes)
worst_cwe_str = ", ".join(worst_cwes)

today = date.today().isoformat()


# =======================
# 英文报告
# =======================
md_en = f"""# CodeQL Evaluation Report

## Overall Performance

- **Precision:** {precision:.2f}
- **Recall:** {recall:.2f}
- **F1-score:** {f1:.2f}

CodeQL achieved a recall of **{recall:.2f}**, indicating that all known vulnerabilities in the benchmark were detected.

The overall precision is **{precision:.2f}**, meaning that some false positives remain.

---

## CWE-level Analysis

- **Best precision:** {best_cwe_str} ({best_precision:.2f})
- **Lowest precision:** {worst_cwe_str} ({worst_precision:.2f})

---

## Figures

### Overall Performance
![Overall](figs/overall_metrics.png)

### Performance by CWE
![Metrics](figs/metrics_by_cwe.png)

### Detection Counts
![Counts](figs/counts_by_cwe.png)

---

## Technical Interpretation

From the evaluation results, CodeQL demonstrates **strong vulnerability coverage** with perfect recall on this benchmark.

However, the precision score indicates that **false positives still exist**.
This is expected in static analysis tools, where conservative data-flow tracking is preferred.

In real-world auditing:

- High recall prevents missing vulnerabilities  
- Moderate precision means manual review may still be needed  

This experiment validates:

- CodeQL is suitable as a **baseline security analysis tool**
- The evaluation pipeline supports future experiments:
  - Multi-tool comparison
  - Rule improvement validation
  - Static-analysis research

---

## Reproducibility

All results are automatically generated from the evaluation pipeline:


---

## Author


**L1ngSh1**  
Generated on: {today}
"""


# =======================
# 中文报告
# =======================
md_zh = f"""# CodeQL 漏洞检测评估报告

## 总体表现

- **准确率（Precision）：** {precision:.2f}
- **召回率（Recall）：** {recall:.2f}
- **F1 分数：** {f1:.2f}

CodeQL 在基准测试中实现了 **{recall:.2f}** 的召回率，说明所有已知漏洞均被检测到。

总体准确率为 **{precision:.2f}**，表明仍存在一定数量的误报。

---

## 各 CWE 类型分析

- **准确率最高：** {best_cwe_str}（{best_precision:.2f}）
- **准确率最低：** {worst_cwe_str}（{worst_precision:.2f}）

---

## 图表展示

### 总体表现
![Overall](figs/overall_metrics.png)

### 各 CWE 指标对比
![Metrics](figs/metrics_by_cwe.png)

### 检测数量统计
![Counts](figs/counts_by_cwe.png)

---

## 技术分析与总结

从实验结果来看，CodeQL 在 OWASP Benchmark 数据集上实现了 **100% 的召回率**，
说明其默认规则在漏洞覆盖能力上非常充分。

但整体准确率约为 **{precision:.2f}**，
这表明检测过程中仍存在一定比例的误报。

这种情况在静态分析工具中是常见的，因为：

- 静态分析通常采用保守策略  
- 更倾向于避免漏报  
- 因此可能扩大潜在危险路径的匹配范围  

在真实工程实践中：

- **高召回率** 可以确保不遗漏关键漏洞  
- **适度误报** 可以通过人工审核或规则优化降低  

本实验不仅验证了 CodeQL 的检测能力，
还构建了完整自动化评估流程，包括：

- SARIF 解析
- 指标计算
- 可视化生成
- 自动报告输出

该流程具备良好的可复现性和扩展性，
未来可用于：

- 多工具横向对比（CodeQL vs CodeFuse-Query）
- 新规则效果评估
- 静态分析研究平台建设

---

## 可复现性说明

所有结果均由自动化评估流程生成：



## 作者

**L1ngSh1**  
生成日期：{today}
"""

OUTPUT_MD_EN.write_text(md_en, encoding="utf-8")
OUTPUT_MD_ZH.write_text(md_zh, encoding="utf-8")

print("✅ English report:", OUTPUT_MD_EN)
print("✅ 中文报告:", OUTPUT_MD_ZH)
