import json
import os
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# ===== 美观风格 =====
sns.set_theme(style="whitegrid")
plt.rcParams["figure.dpi"] = 120
plt.rcParams["font.size"] = 10

BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_JSON = BASE_DIR / "reports" / "data" / "metrics.json"
OUTPUT_DIR = BASE_DIR / "reports" / "figs"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

with open(INPUT_JSON, "r", encoding="utf-8") as f:
    data = json.load(f)

cwes = []
precision_list = []
recall_list = []
f1_list = []
tp_list = []
fp_list = []
fn_list = []

for cwe, info in data.items():
    if cwe == "OVERALL":
        continue
    
    if "tools" in info and "codeql" in info["tools"]:
        result = info["tools"]["codeql"]
        cwes.append(cwe)
        precision_list.append(result["precision"])
        recall_list.append(result["recall"])
        f1_list.append(result["f1"])
        tp_list.append(result["tp"])
        fp_list.append(result["fp"])
        fn_list.append(result["fn"])

x = np.arange(len(cwes))
width = 0.25


# =============================
# 图 1：Precision / Recall / F1
# =============================
fig, ax = plt.subplots(figsize=(16,6))

bars1 = ax.bar(x - width, precision_list, width, label="Precision", color="#4C72B0")
bars2 = ax.bar(x, recall_list, width, label="Recall", color="#DD8452")
bars3 = ax.bar(x + width, f1_list, width, label="F1", color="#55A868")

ax.set_xticks(x)
ax.set_xticklabels(cwes, rotation=45)
ax.set_ylim(0, 1.08)   
ax.set_title("CodeQL Performance by CWE", fontsize=14, weight="bold")

ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1))

for bars in [bars1, bars3]:
    for bar in bars:
        height = bar.get_height()
        ax.annotate(f'{height:.2f}',
                    xy=(bar.get_x() + bar.get_width()/2, height),
                    xytext=(0,4),
                    textcoords="offset points",
                    ha="center", va="bottom", fontsize=8)

plt.tight_layout()
plt.savefig(OUTPUT_DIR / "metrics_by_cwe.png", bbox_inches="tight")
plt.close()



# =============================
# 图 2：TP / FP / FN
# =============================
fig, ax = plt.subplots(figsize=(12,6))

bars1 = ax.bar(x - width, tp_list, width, label="TP", color="#4C72B0")
bars2 = ax.bar(x, fp_list, width, label="FP", color="#C44E52")
bars3 = ax.bar(x + width, fn_list, width, label="FN", color="#8172B3")

ax.set_xticks(x)
ax.set_xticklabels(cwes, rotation=45)
ax.set_title("Detection Counts by CWE", fontsize=14, weight="bold")
ax.legend()

plt.tight_layout()
plt.savefig(OUTPUT_DIR / "counts_by_cwe.png")
plt.close()


# =============================
# 图 3：Overall（高级版）
# =============================
overall = data["OVERALL"]["tools"]["codeql"]

fig, ax = plt.subplots(figsize=(7,5))

metrics = ["Precision", "Recall", "F1"]
values = [overall["precision"], overall["recall"], overall["f1"]]

colors = ["#4C72B0", "#DD8452", "#55A868"]

bars = ax.bar(metrics, values, color=colors, width=0.6)

ax.set_ylim(0, 1.08)

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

ax.set_title("Overall Performance (CodeQL)", fontsize=15, weight="bold", pad=15)

for bar in bars:
    height = bar.get_height()
    ax.annotate(f'{height:.2f}',
                xy=(bar.get_x() + bar.get_width()/2, height),
                xytext=(0,6),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=12,
                weight="bold")

plt.tight_layout()
plt.savefig(OUTPUT_DIR / "overall_metrics.png", bbox_inches="tight")
plt.close()

