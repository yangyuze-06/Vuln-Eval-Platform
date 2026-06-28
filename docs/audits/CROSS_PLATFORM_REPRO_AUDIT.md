# VEP Cross-platform Reproducibility Audit

## 审计背景

**问题描述**: 同一套 VEP 评测在 macOS 和 Linux 平台跑出的结果不一致，具体表现为某个 CWE 在 macOS 平台比 Linux 平台多出 1 个 FN。

**审计目标**: 定位跨平台结果不一致的根本原因，不修改评测逻辑，只做诊断。

**审计范围**:
- 环境差异诊断
- 评测结果差异定位
- Testcase 级别根因分析
- 可能原因分类和验证方法

---

## 当前状态

### 文件布局分析

当前仓库结构：

```
experiments/
├── cwe-022/
│   ├── results/
│   │   ├── codefuse/cwe022.csv
│   │   ├── codefuse-query/cwe022_codefuse.csv
│   │   ├── codeql/cwe022.sarif
│   │   └── codeql/cwe022.csv
│   └── eval/
│       ├── codefuse_eval/
│       ├── codefuse_eval_v2/
│       ├── codefuse_eval_v2b/
│       ├── codefuse_eval_v2b_inscope/
│       ├── codefuse_eval_v2b_review/
│       └── codefuse_eval_phase2_final_precheck/
├── cwe-078/
├── cwe-079/
├── cwe-089/
├── cwe-090/
├── cwe-327/
├── cwe-328/
├── cwe-330/
├── cwe-501/
├── cwe-614/
└── cwe-643/
```

每个 eval 目录包含：
- `metrics.json`: 评测指标
- `tp.csv`: True Positive testcases
- `fp.csv`: False Positive testcases
- `fn.csv`: False Negative testcases
- `outside_scope.csv`: Out-of-scope testcases

### 当前 macOS 环境指纹

已采集当前 macOS 环境指纹（见 `docs/audits/env_fingerprint_current.json`）：

- **操作系统**: Darwin (macOS-26.5.1-arm64)
- **文件系统**: case-insensitive ⚠️
- **Python**: 3.14.5
- **Java**: OpenJDK 17.0.19
- **Maven**: 3.9.15
- **CodeQL**: 2.25.3
- **Git commit**: be4ea7ea
- **expectedresults 校验和**: `94d19209...`

⚠️ **关键发现**: macOS 文件系统默认 **大小写不敏感**，这可能是导致跨平台差异的重要因素。

---

## 诊断工具

已创建两个诊断脚本（详见 `scripts/diagnostics/README.md`）：

### 1. `collect_env_fingerprint.py`

**功能**: 采集平台环境指纹

**已验证功能**:
- ✅ 平台信息采集
- ✅ 文件系统大小写敏感性测试
- ✅ 工具版本采集
- ✅ Git 状态采集
- ✅ 关键文件 SHA-256 校验

**使用方法**:
```bash
# macOS
python3 scripts/diagnostics/collect_env_fingerprint.py --out docs/env_fingerprint_Darwin.json

# Linux
python3 scripts/diagnostics/collect_env_fingerprint.py --out docs/env_fingerprint_Linux.json
```

### 2. `compare_eval_results.py`

**功能**: 比较两个评测结果，找出差异 testcases

**已验证功能**:
- ✅ 读取 eval 目录
- ✅ 解析 metrics.json
- ✅ 解析 tp/fp/fn/outside_scope.csv
- ✅ 自动识别 testcase 字段名
- ✅ 计算集合差异
- ✅ 生成 Markdown 报告
- ✅ 处理空 CSV
- ✅ 指标对比

**测试结果**: 对 CWE-022 的 v2b vs v2 评测结果比较，工具正常运行，未发现差异。

**使用方法**:
```bash
python3 scripts/diagnostics/compare_eval_results.py \
  --left experiments/cwe-022/eval/mac_eval \
  --right experiments/cwe-022/eval/linux_eval \
  --left-label mac \
  --right-label linux \
  --cwe CWE-022 \
  --out docs/repro_compare_CWE-022.md \
  --verbose
```

---

## 跨平台差异可能原因分析

### Confirmed（已确认的差异）

1. **文件系统大小写敏感性不同**
   - macOS: case-insensitive（默认 APFS）
   - Linux: case-sensitive（ext4/xfs）
   - **影响**: 如果 testcase 提取或路径匹配依赖文件名大小写，可能导致结果不一致
   - **验证方法**: 检查 expectedresults-1.2.csv 中 testcase 名是否存在大小写变体

### Likely（高度可能）

2. **路径标准化差异**
   - macOS: `/Users/...`, `/private/var/...` (symlink)
   - Linux: `/home/...`, `/var/...`
   - **影响**: 如果路径标准化逻辑未正确处理平台差异，可能导致 testcase 提取失败
   - **验证方法**: 
     - 检查 raw SARIF/JSON 中的 `artifactLocation.uri`
     - 检查 normalized CSV 中的 `sinkFile` 路径
     - 检查路径标准化代码（converter/normalizer）

3. **Testcase 提取逻辑差异**
   - **场景**: 如果 testcase 名从文件路径中提取（例如从 `BenchmarkTest00060.java` 提取 `BenchmarkTest00060`）
   - **影响**: 路径格式差异可能导致正则表达式匹配失败
   - **验证方法**: 
     - 检查 `scripts/evaluation/eval_findings.py` 中的 testcase 提取逻辑
     - 对 suspect testcase 打印原始路径和提取结果

### Possible（可能但需验证）

4. **Analyzer 结果本身不同**
   - **原因**: CodeQL/CodeFuse 在不同平台可能产生不同的 database 或 findings
   - **影响**: raw SARIF/JSON 本身就不同
   - **验证方法**: 比较两边 raw SARIF/JSON 文件的 sha256

5. **工具版本不同**
   - **原因**: 两边使用的 CodeQL/CodeFuse/JDK/Python 版本不同
   - **影响**: 分析结果可能不同
   - **验证方法**: 比较两边环境指纹 JSON

6. **Database/Build 不一致**
   - **原因**: 两边不是从相同的源代码构建的 database
   - **影响**: 分析覆盖范围可能不同
   - **验证方法**: 
     - 检查 `dataset/` 目录是否一致
     - 检查 CodeQL database 创建命令是否相同

7. **非确定性排序/去重**
   - **原因**: Python `set`/`dict` 在不同平台可能顺序不同，导致 dedup 保留不同的 finding
   - **影响**: 多个 finding 指向同一 testcase 时，保留的 finding 可能不同
   - **验证方法**: 
     - 检查 evaluator/converter 是否有排序逻辑
     - 检查是否有依赖 dict/set 迭代顺序的代码

8. **换行符/编码差异**
   - **原因**: CSV 文件在两边可能有 CRLF vs LF 差异
   - **影响**: CSV 解析可能失败或字段值包含隐藏字符
   - **验证方法**: 运行 `file <csv_file>` 和 `hexdump -C <csv_file> | head`

9. **Ground Truth 文件不一致**
   - **原因**: 两边使用的 `expectedresults-1.2.csv` 不是同一个版本
   - **影响**: 评测标准不同
   - **验证方法**: 比较两边 expectedresults 的 sha256

---

## 定位流程

要定位 "macOS 多 1 个 FN" 的根因，需要回答以下 5 个问题：

### 核心问题链

1. **多出来的 FN 是哪个 testcase？**
   - 比较 Mac 和 Linux 的 `fn.csv`
   - 找出 Mac 独有的 FN testcases

2. **Linux 这边该 testcase 是什么状态？**
   - 检查 Linux 的 `tp.csv`, `fp.csv`, `outside_scope.csv`
   - 可能状态: TP / FP / Outside-scope / 缺失

3. **Mac raw result 里有没有这个 finding？**
   - 检查 Mac 的 raw SARIF/JSON
   - 搜索该 testcase 的文件名/路径

4. **Mac normalized CSV 里有没有这个 finding？**
   - 检查 Mac 的 `results/codefuse/cweXXX.csv` 或 `results/codeql/cweXXX.csv`
   - 搜索该 testcase

5. **Mac evaluator 为什么没把它算 TP？**
   - 检查 evaluator 匹配逻辑
   - 检查 ground truth 中该 testcase 的预期状态

### 分层诊断

根据上述 5 个问题的答案，判断差异发生在哪一层：

| 层级 | 症状 | 根因 |
|------|------|------|
| **Analyzer** | Linux raw 有，Mac raw 无 | 工具在 Mac 上漏报 |
| **Converter** | Mac raw 有，Mac CSV 无 | 转换器丢失 finding |
| **Normalization** | Mac CSV 有，但 testcase 名不对 | 路径标准化/testcase 提取失败 |
| **Evaluator** | Mac CSV 正确，但分类错误 | evaluator 匹配逻辑 bug |
| **Ground Truth** | Mac 和 Linux 用的 expectedresults 不同 | 文件版本不一致 |

---

## 下一步行动

### 立即可做（当前 Mac 环境）

1. ✅ 已完成: 采集 Mac 环境指纹
2. ✅ 已完成: 创建诊断工具
3. ✅ 已完成: 验证诊断工具

### 需要在 Linux 上执行

4. **采集 Linux 环境指纹**:
   ```bash
   python3 scripts/diagnostics/collect_env_fingerprint.py --out docs/env_fingerprint_Linux.json
   ```

5. **在 Linux 上重新评测**（保留结果）:
   ```bash
   # 对出问题的 CWE 重新评测
   bash scripts/evaluation/eval_checker.sh <CWE_NUMBER>
   
   # 保存结果到带平台标识的目录
   cp -r experiments/cwe-<CWE>/eval/codefuse_eval_v2b \
         experiments/cwe-<CWE>/eval/linux_eval
   ```

### 对比分析

6. **比较环境指纹**:
   - 对比 `env_fingerprint_Darwin.json` 和 `env_fingerprint_Linux.json`
   - 特别关注: 工具版本、文件系统、关键文件校验和

7. **比较评测结果**:
   ```bash
   python3 scripts/diagnostics/compare_eval_results.py \
     --left experiments/cwe-<CWE>/eval/mac_eval \
     --right experiments/cwe-<CWE>/eval/linux_eval \
     --left-label mac \
     --right-label linux \
     --cwe CWE-<CWE> \
     --out docs/repro_compare_CWE-<CWE>.md \
     --verbose
   ```

8. **定位 suspect testcases**:
   - 根据比较报告，找出差异 testcases
   - 对每个 testcase，执行上述"核心问题链"的 5 个检查

9. **分析 raw findings**:
   ```bash
   # 检查 Mac raw SARIF
   jq '.runs[].results[] | select(.locations[].physicalLocation.artifactLocation.uri | contains("BenchmarkTest<ID>"))' \
     experiments/cwe-<CWE>/results/codefuse/cwe<CWE>.sarif.json
   
   # 检查 Linux raw SARIF（同样命令）
   ```

10. **检查路径标准化**:
    - 比较两边 normalized CSV 中 suspect testcase 的路径格式
    - 检查 converter 代码中的路径处理逻辑

---

## 自我 Review

### ✅ PASS

**已完成**:
- ✅ 创建只读诊断脚本（不修改任何评测文件）
- ✅ 脚本能处理空 CSV、缺失字段、不同字段名
- ✅ 脚本不依赖第三方包（仅标准库）
- ✅ 脚本通过 `python3 -m compileall` 检查
- ✅ `--help` 参数正常工作
- ✅ 实际运行测试通过（采集环境指纹、比较结果）
- ✅ 文档清晰说明使用方法和工作流
- ✅ 明确区分 Confirmed / Likely / Possible 原因
- ✅ 提供具体验证方法

**未做**:
- ❌ 未修改任何 GDL/QL 规则
- ❌ 未修改 Java benchmark
- ❌ 未移动任何目录
- ❌ 未删除旧结果
- ❌ 未重写 evaluator
- ❌ 未进入 Phase 3
- ❌ 未运行重型分析命令

**限制**:
- 当前仓库只有 Mac 结果，无法直接比较
- 需要在 Linux 上重新运行评测才能进行对比
- 未识别出具体哪个 CWE 有差异（需要用户提供）

### ⚠️ Warnings

1. **缺少 Linux 结果**: 当前无法完成完整的跨平台比较，需要用户在 Linux 上运行评测
2. **evaluator.py 等文件缺失**: 环境指纹显示 `evaluator.py`, `findings.py` 等文件为 `missing`，可能这些文件已被重构或移动
3. **未识别具体 CWE**: 用户提到"某个 CWE 多 1 个 FN"，但未指明具体是哪个 CWE

---

## 剩余 TODO

1. **用户提供信息**:
   - 具体是哪个 CWE 出现差异？
   - 已有的 Mac 和 Linux 结果目录路径？
   - 或者需要在 Linux 上重新运行评测？

2. **运行对比**:
   - 在 Linux 上运行环境指纹采集
   - 在 Linux 上运行评测（或提供已有结果路径）
   - 运行 `compare_eval_results.py` 找出差异

3. **深入分析**:
   - 定位具体 testcase
   - 检查 raw findings
   - 检查 normalized CSV
   - 检查路径标准化逻辑
   - 检查 evaluator 匹配逻辑

4. **根因确认**:
   - 根据分层诊断结果，确定是哪一层的问题
   - 提出针对性的修复方案（如果需要）

---

## 命令速查

### 在 Mac 上运行
```bash
# 已完成
python3 scripts/diagnostics/collect_env_fingerprint.py --out docs/env_fingerprint_Darwin.json
```

### 在 Linux 上运行
```bash
# 采集环境指纹
python3 scripts/diagnostics/collect_env_fingerprint.py --out docs/env_fingerprint_Linux.json

# 运行评测（替换 <CWE> 为具体编号，如 022）
bash scripts/evaluation/eval_checker.sh <CWE>

# 保存结果
cp -r experiments/cwe-<CWE>/eval/codefuse_eval_v2b \
      experiments/cwe-<CWE>/eval/linux_eval
```

### 对比结果（任一平台）
```bash
# 比较评测结果
python3 scripts/diagnostics/compare_eval_results.py \
  --left experiments/cwe-<CWE>/eval/mac_eval \
  --right experiments/cwe-<CWE>/eval/linux_eval \
  --left-label mac \
  --right-label linux \
  --cwe CWE-<CWE> \
  --out docs/repro_compare_CWE-<CWE>.md \
  --verbose

# 检查差异报告
cat docs/repro_compare_CWE-<CWE>.md
```

---

## 参考资料

- **诊断工具文档**: `scripts/diagnostics/README.md`
- **当前环境指纹**: `docs/audits/env_fingerprint_current.json`
- **测试比较报告**: `docs/audits/test_compare_cwe022_v2b_vs_v2.md`
- **Ground Truth**: `expectedresults-1.2.csv`
- **CWE Manifest**: `configs/cwe_manifest.yml`

---

**Last Updated**: 2026-06-11  
**Audit Status**: Phase 0 Complete - Tools Ready, Awaiting Linux Results
