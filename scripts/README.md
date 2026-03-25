# 脚本使用说明（终端 + VSCode）

本文覆盖 `scripts/` 目录下每一个 Python 脚本，给出中文说明、终端示例和 VSCode 运行方式。

## 1. 脚本清单

- `scripts/converters/sarif_to_csv.py`
- `scripts/converters/codefuse_json_to_csv.py`
- `scripts/evaluation/eval_codefuse_results.py`
- `scripts/evaluation/aggregate_results.py`
- `scripts/evaluation/eval_codeql_cwexxx.py`
- `scripts/reporting/plots_metrics.py`
- `scripts/reporting/generate_report.py`

## 2. 运行前提

- 在仓库根目录执行命令（即 `Vuln-Eval-Lab` 根目录）。
- 建议 Python 3.8+。
- 建议先激活虚拟环境：

```bash
cd /path/to/Vuln-Eval-Lab
source .venv/bin/activate
```

## 3. 各脚本详细用法

### 3.1 `scripts/converters/sarif_to_csv.py`

功能：将 CodeQL SARIF 转为 CSV。  
注意：此脚本当前是“写死输入输出路径”的方式，运行前请先改脚本顶部常量：

- `SARIF_FILE = "..."`
- `OUTPUT_CSV = "..."`

终端示例：

```bash
cd /path/to/Vuln-Eval-Lab
python3 scripts/converters/sarif_to_csv.py
```

VSCode 运行：

1. 打开 `scripts/converters/sarif_to_csv.py`，先修改 `SARIF_FILE` 和 `OUTPUT_CSV`。  
2. 点击右上角 `Run Python File` 即可。  
3. 或使用 `launch.json`：

```json
{
  "name": "sarif_to_csv.py",
  "type": "python",
  "request": "launch",
  "program": "${workspaceFolder}/scripts/converters/sarif_to_csv.py",
  "cwd": "${workspaceFolder}",
  "console": "integratedTerminal"
}
```

---

### 3.2 `scripts/converters/codefuse_json_to_csv.py`

功能：将 Sparrow/CodeFuse JSON 转成评测用 CSV（默认列：`testcase,ruleId,file,line`）。

常用参数：

- `input_json`：输入 JSON
- `output_csv`：输出 CSV
- `--include-reason`：额外输出 `reason` 列
- `--no-dedup-testcase`：关闭 testcase 去重
- `--default-rule`：缺省 `ruleId`
- `--unknown-label`：无法提取 testcase 时的标签

终端示例（CWE-022）：

```bash
cd /path/to/Vuln-Eval-Lab
python3 scripts/converters/codefuse_json_to_csv.py \
  experiments/cwe-022/results/codefuse-query/checker_taint_no_fallback_debug.json \
  experiments/cwe-022/results/codefuse-query/cwe022_codefuse.csv
```

终端示例（保留 reason）：

```bash
python3 scripts/converters/codefuse_json_to_csv.py \
  experiments/cwe-022/results/codefuse-query/checker_taint_no_fallback_debug.json \
  experiments/cwe-022/results/codefuse-query/cwe022_codefuse_with_reason.csv \
  --include-reason
```

VSCode 运行（`launch.json`）：

```json
{
  "name": "codefuse_json_to_csv.py",
  "type": "python",
  "request": "launch",
  "program": "${workspaceFolder}/scripts/converters/codefuse_json_to_csv.py",
  "cwd": "${workspaceFolder}",
  "console": "integratedTerminal",
  "args": [
    "experiments/cwe-022/results/codefuse-query/checker_taint_no_fallback_debug.json",
    "experiments/cwe-022/results/codefuse-query/cwe022_codefuse.csv",
    "--include-reason"
  ]
}
```

---

### 3.3 `scripts/evaluation/eval_codefuse_results.py`

功能：将 CodeFuse 检测结果与 `expectedresults-1.2.csv` 对比，输出 `metrics.json / tp.csv / fp.csv / fn.csv / outside_scope.csv`。

必填参数：

- `--expected`
- `--results`
- `--cwe`
- `--outdir`

可选参数：

- `--format auto|json|csv`（默认 `auto`）
- `--fp-mode in_scope|all_non_gt`（默认 `all_non_gt`）

终端示例（输入为 JSON）：

```bash
cd /path/to/Vuln-Eval-Lab
python3 scripts/evaluation/eval_codefuse_results.py \
  --expected expectedresults-1.2.csv \
  --results experiments/cwe-022/results/codefuse-query/checker_taint_no_fallback_debug.json \
  --cwe CWE-022 \
  --outdir experiments/cwe-022/eval/codefuse-debug-json \
  --format json \
  --fp-mode all_non_gt
```

终端示例（输入为 CSV）：

```bash
python3 scripts/evaluation/eval_codefuse_results.py \
  --expected expectedresults-1.2.csv \
  --results experiments/cwe-022/results/codefuse-query/cwe022_codefuse.csv \
  --cwe CWE-022 \
  --outdir experiments/cwe-022/eval/codefuse-csv \
  --format csv \
  --fp-mode in_scope
```

VSCode 运行（`launch.json`）：

```json
{
  "name": "eval_codefuse_results.py",
  "type": "python",
  "request": "launch",
  "program": "${workspaceFolder}/scripts/evaluation/eval_codefuse_results.py",
  "cwd": "${workspaceFolder}",
  "console": "integratedTerminal",
  "args": [
    "--expected", "expectedresults-1.2.csv",
    "--results", "experiments/cwe-022/results/codefuse-query/cwe022_codefuse.csv",
    "--cwe", "CWE-022",
    "--outdir", "experiments/cwe-022/eval/codefuse-csv",
    "--format", "csv",
    "--fp-mode", "all_non_gt"
  ]
}
```

---

### 3.4 `scripts/evaluation/aggregate_results.py`

功能：自动扫描 `experiments/*/results`，汇总各 CWE 指标到 `reports/data/metrics.json`。

注意：

- 本脚本会读取：
  - `results/codeql/*.csv`
  - `results/codefuse/*.csv`
- 如果你的 CodeFuse CSV 在 `results/codefuse-query/`，请先复制到 `results/codefuse/`。

终端示例：

```bash
cd /path/to/Vuln-Eval-Lab
mkdir -p experiments/cwe-022/results/codefuse
cp experiments/cwe-022/results/codefuse-query/cwe022_codefuse.csv \
   experiments/cwe-022/results/codefuse/cwe022.csv

python3 scripts/evaluation/aggregate_results.py
```

VSCode 运行：

1. 打开 `scripts/evaluation/aggregate_results.py`  
2. 点击 `Run Python File`  
3. 或使用 `launch.json`：

```json
{
  "name": "aggregate_results.py",
  "type": "python",
  "request": "launch",
  "program": "${workspaceFolder}/scripts/evaluation/aggregate_results.py",
  "cwd": "${workspaceFolder}",
  "console": "integratedTerminal"
}
```

---

### 3.5 `scripts/evaluation/eval_codeql_cwexxx.py`

功能：从汇总 JSON 生成 CodeQL 图表，输出到 `reports/figs/`。  
注意：当前脚本读取的是 `reports/data/summery.json`（文件名就是 `summery`）。

终端示例：

```bash
cd /path/to/Vuln-Eval-Lab
python3 scripts/evaluation/eval_codeql_cwexxx.py
```

VSCode 运行：

1. 打开 `scripts/evaluation/eval_codeql_cwexxx.py`
2. 点击 `Run Python File`
3. 或使用 `launch.json`：

```json
{
  "name": "eval_codeql_cwexxx.py",
  "type": "python",
  "request": "launch",
  "program": "${workspaceFolder}/scripts/evaluation/eval_codeql_cwexxx.py",
  "cwd": "${workspaceFolder}",
  "console": "integratedTerminal"
}
```

---

### 3.6 `scripts/reporting/plots_metrics.py`

功能：读取 `reports/data/metrics.json`，输出图表：

- `reports/figs/metrics_by_cwe.png`
- `reports/figs/counts_by_cwe.png`
- `reports/figs/overall_metrics.png`

终端示例：

```bash
cd /path/to/Vuln-Eval-Lab
python3 scripts/reporting/plots_metrics.py
```

VSCode 运行：

1. 打开 `scripts/reporting/plots_metrics.py`
2. 点击 `Run Python File`
3. 或使用 `launch.json`：

```json
{
  "name": "plots_metrics.py",
  "type": "python",
  "request": "launch",
  "program": "${workspaceFolder}/scripts/reporting/plots_metrics.py",
  "cwd": "${workspaceFolder}",
  "console": "integratedTerminal"
}
```

---

### 3.7 `scripts/reporting/generate_report.py`

功能：读取 `reports/data/metrics.json`，生成中英文报告：

- `reports/report.md`
- `reports/report_zh.md`

终端示例：

```bash
cd /path/to/Vuln-Eval-Lab
python3 scripts/reporting/generate_report.py
```

VSCode 运行：

1. 打开 `scripts/reporting/generate_report.py`
2. 点击 `Run Python File`
3. 或使用 `launch.json`：

```json
{
  "name": "generate_report.py",
  "type": "python",
  "request": "launch",
  "program": "${workspaceFolder}/scripts/reporting/generate_report.py",
  "cwd": "${workspaceFolder}",
  "console": "integratedTerminal"
}
```

## 4. 推荐执行顺序（CodeFuse 结果评测）

```bash
# 1) JSON -> CSV
python3 scripts/converters/codefuse_json_to_csv.py <input.json> <output.csv>

# 2) 单 CWE 评测（可选）
python3 scripts/evaluation/eval_codefuse_results.py \
  --expected expectedresults-1.2.csv \
  --results <output.csv> \
  --cwe CWE-022 \
  --outdir experiments/cwe-022/eval/codefuse

# 3) 汇总
python3 scripts/evaluation/aggregate_results.py

# 4) 画图 + 报告
python3 scripts/reporting/plots_metrics.py
python3 scripts/reporting/generate_report.py
```
