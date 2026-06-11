# VEP Cross-platform Reproducibility Diagnostics

本目录包含用于诊断 VEP 跨平台评测结果不一致的诊断工具。

## 工具列表

### 1. `collect_env_fingerprint.py`

**功能**: 采集当前平台的环境指纹

**使用方法**:

```bash
python scripts/diagnostics/collect_env_fingerprint.py --out docs/env_fingerprint_$(uname -s).json
```

**输出内容**:

- 操作系统信息 (Darwin/Linux)
- 文件系统大小写敏感性
- Python/Java/Maven 版本
- CodeQL/Gödel 版本
- Git commit/branch/status
- 关键文件 SHA-256 校验和

**使用场景**:

在 Mac 和 Linux 上分别运行此脚本，对比两边环境差异。

---

### 2. `compare_eval_results.py`

**功能**: 比较两个评测结果目录，找出 TP/FP/FN 差异

**使用方法**:

```bash
python scripts/diagnostics/compare_eval_results.py \
  --left experiments/cwe-022/eval/mac_eval \
  --right experiments/cwe-022/eval/linux_eval \
  --left-label mac \
  --right-label linux \
  --ground-truth expectedresults-1.2.csv \
  --cwe CWE-022 \
  --out docs/repro_compare_CWE-022.md \
  --verbose
```

**输入支持**:

- Eval 目录 (包含 metrics.json, tp.csv, fp.csv, fn.csv)
- 单个 metrics.json 文件
- 单个 CSV 文件

**输出内容**:

- Metrics 指标对比 (TP/FP/FN/Precision/Recall/F1)
- TP/FP/FN/Outside-scope testcase 集合差异
- 仅 Mac 独有的 testcases
- 仅 Linux 独有的 testcases
- 初步根因诊断建议

**使用场景**:

定位跨平台评测结果不一致的具体 testcase。

---

## 典型工作流

### Step 1: 在两个平台采集环境指纹

Mac:
```bash
python scripts/diagnostics/collect_env_fingerprint.py --out docs/env_fingerprint_Darwin.json
```

Linux:
```bash
python scripts/diagnostics/collect_env_fingerprint.py --out docs/env_fingerprint_Linux.json
```

### Step 2: 保存两边评测结果

在两个平台分别运行评测，保留结果目录：

Mac:
```bash
bash scripts/evaluation/eval_checker.sh 022
cp -r experiments/cwe-022/eval/codefuse_eval_v2b experiments/cwe-022/eval/mac_eval
```

Linux:
```bash
bash scripts/evaluation/eval_checker.sh 022
cp -r experiments/cwe-022/eval/codefuse_eval_v2b experiments/cwe-022/eval/linux_eval
```

### Step 3: 对比评测结果

```bash
python scripts/diagnostics/compare_eval_results.py \
  --left experiments/cwe-022/eval/mac_eval \
  --right experiments/cwe-022/eval/linux_eval \
  --left-label mac \
  --right-label linux \
  --ground-truth expectedresults-1.2.csv \
  --cwe CWE-022 \
  --out docs/repro_compare_CWE-022.md \
  --verbose
```

### Step 4: 分析 suspect testcases

根据报告中的 suspect testcases，检查：

1. 该 testcase 在两边 raw findings (SARIF/JSON) 中是否存在
2. 该 testcase 在两边 normalized CSV 中是否存在
3. 该 testcase 的路径、行号、ruleId 是否一致
4. 该 testcase 在 ground truth 中的预期状态

### Step 5: 定位根因

根据 Step 4 的检查结果，判断差异发生在哪一层：

- **Analyzer 层**: raw findings 本身不同 → 工具版本/数据库/配置问题
- **Converter 层**: raw 有但 CSV 无 → 转换器 bug
- **Normalization 层**: CSV 有但 testcase 名不对 → 路径标准化问题
- **Evaluator 层**: CSV 正确但分类错误 → evaluator 匹配逻辑问题
- **Ground Truth 层**: expectedresults 不一致 → 文件版本问题

---

## 注意事项

1. 这些工具是只读诊断工具，不会修改任何结果文件
2. 环境指纹采集会在临时目录进行大小写敏感性测试，测试后会自动清理
3. 比较工具能处理空 CSV、缺失字段、不同字段名的情况
4. 所有错误和差异都不会导致脚本失败 (exit 0)，只有文件缺失或解析失败才 exit 非 0

---

## 常见问题

**Q: 如果我只有一个平台的结果怎么办？**

A: 先运行环境指纹采集，然后在另一个平台重新评测，再使用 compare 工具。

**Q: 如果我不知道哪个 CWE 有差异怎么办？**

A: 遍历所有 CWE 目录，对每个 CWE 运行 compare 工具，找出有差异的。

**Q: 如果两边目录结构不一致怎么办？**

A: compare 工具可以直接指定 metrics.json 或 CSV 文件路径，不要求目录结构完全一致。

**Q: 如何验证脚本本身没问题？**

A: 运行 `python -m compileall scripts/diagnostics` 检查语法，运行 `--help` 检查参数解析。
