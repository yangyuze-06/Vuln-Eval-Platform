# CodeFuse/Sparrow macOS vs Linux DB Root Cause v2

**生成时间**: 2026-06-17
**调查方式**: 只读诊断（two local SQLite DB diff + 环境采集 + 证据链交叉验证）
**对比对象**:
- `dataset/codefuse-db-linux/coref_java_src.db` (259 MB, 2026-02-05)
- `dataset/codefuse-db-mac/coref_java_src.db` (258 MB, 2026-06-12 16:12)

**结论分级约定**: `Confirmed` 有直接证据 / `Likely` 证据强但留口 / `Possible` 合理但未证 / `Ruled out` 已排除 / `Unknown` 待补。

---

## 1. Executive Summary

- **`Confirmed`**: Mac 库与 Linux 库结构几乎一致（130 张表全同，仅 5 张行数不同），节点总数相等；差异本质是 **27871 个 method-access 表达式从 `*_with_type` 掉到 `*_without_type`**（接收者类型未绑定），而不是节点缺失。
- **`Confirmed`**: DB 证据精确定位到 **`java.*` JDK 类型解析结果缺失**——`reference_type` 中 `java.*` 全限定名从 **842 → 38（−95%）**；而项目内部类型 `org.owasp.*` **891 = 891 完全一致**、第三方 jar 类型 `javax.*` 基本保留（32 → 25）。
- **`Confirmed`**: 受影响的恰是污点类 CWE（022/078/079/089/501/643，共 67 FN）。其污点链上的 **中继类型**（`java.lang.String`/`StringBuilder` 1→0）与 **sink 类型**（`java.lang.Runtime`/`ProcessBuilder` 1→0）在 Mac 库里丢失；而 crypto/LDAP 的 sink 落在 `javax.*`（未丢），故 327/328/330/614/090 无漏报。
- **`Likely`**: Mac 端建库时 **JDK 系统/启动类路径（java.base 等）没有进入 Sparrow 的类型解析路径**，而应用依赖 jar 进入了。最可能的触发点是 **JDK 发现失败**（本机 `/usr/libexec/java_home` 现在就报 "Unable to locate a Java Runtime"）。
- **建议**: 正式评测 **只用 Linux 库**。Mac 库判为非权威、不可用于正式数据。已提供只读 CI gate（`scripts/diagnose_codefuse_db_diff.py`），当前对 Mac 库返回 **FAIL / exit 1**。

---

## 2. What Was Already Known

来自既有报告（`reports/mac-linux-discrepancy-analysis.md`、`mac-missing-testcases-detailed.md`、`mac-missing-testcases.json`）：

| 平台 | TP | FP | FN | Recall |
|------|----|----|----|--------|
| Linux | 1414 | 553 | 0 | 1.0000 |
| Mac   | 1347 | 545 | 67 | 0.9526 |

- 67 个 FN 分布在 6 个污点类 CWE：022(13)、078(25)、079(18)、089(5)、501(5)、643(1)。
- 5 个 CWE 完全一致：090、327、328、330、614。
- v1 报告已给出方向性判断（"Linux 找到完整 FQN、Mac 没找到"），但**未区分** JDK / 第三方 / 项目类型，且把 servlet source 当作差异点（本轮证伪，见 §9）。

---

## 3. Environment Evidence

| 维度 | Linux（建库时） | Mac（建库时, 据 FN json） | Mac（现在 2026-06-17） |
|------|----------------|--------------------------|------------------------|
| OS / arch | Linux 6.17 x86_64 | macOS arm64 | macOS 26.5.1, Darwin 25.5.0, arm64 |
| Java | OpenJDK **21.0.10** | OpenJDK **21.0.11** | OpenJDK **17.0.19** (Homebrew) |
| `/usr/libexec/java_home -V` | (已注册 JDK) | 未知 | **失败**："Unable to locate a Java Runtime" |
| `JAVA_HOME` | — | 未知 | `/opt/homebrew/opt/openjdk@17`（Homebrew keg，未向 macOS 注册） |
| GodelScript | 1.1.20240702 | 未知 | sparrow-cli 在 `CODEFUSE_HOME` |
| 文件系统 | case-sensitive | APFS（默认 case-insensitive） | 同 |

来源：`reports/data/env-fingerprint-linux-2026-06-11.json`、`mac-missing-testcases.json`、本轮 `uname/java -version//usr/libexec/java_home`。

**建库命令**（`docs/evaluation_workflow.md`、`dataset/codefuse-db-linux/command.txt`）：
```
sparrow database create -s <src>/main/java -lang java -o <out>
```
→ **未显式传 classpath / JDK / 依赖 jar**，Sparrow 需自行发现 JDK 与依赖。

关键观察：
- 两端建库都用 **Java 21**（21.0.10 vs 21.0.11，仅 patch 差异）→ 排除"JDK8 rt.jar vs JDK9+ 模块化"作为差异点（见 §9）。
- 现网 Mac 的 `/usr/libexec/java_home` **失败**：若 Sparrow 依赖该机制定位 JDK，会拿不到 JDK 系统类。这与 `java.*` 类型几乎全失的现象一致。
- **`Unknown`**: 6/12 建库当时 Java 为 21.0.11，与现网 17.0.19 不同；当时 `java_home` 是否同样失败无法回溯。本节"现在"列仅作旁证，不作为建库时的确证。

---

## 4. DB Table Count Diff

130 张表完全相同，仅 5 张行数不同，且 **成对抵消**（自动生成于 `reports/codefuse-db-diff-latest.md`）：

| table | linux | mac | delta |
|---|---:|---:|---:|
| method_access_expression_with_type | 32371 | 4500 | **−27871** |
| method_access_expression_without_type | 39455 | 67326 | **+27871** |
| constructor_invocation | 3683 | 5172 | +1489 |
| new_expression | 6026 | 4537 | −1489 |
| reference_type | 1840 | 1111 | −729 |

- method-access 总数两端均 71826；构造类总数两端均 9709 → **节点没丢**，只是从"有类型"降级为"无类型"。
- `method_access_expression with_type 占比`：Linux **45.1%** vs Mac **6.3%**。

**`Confirmed`**: 差异是类型绑定丢失，不是 AST 节点缺失。

---

## 5. FQN Degradation Evidence

`reference_type.qualified_name` 按包前缀分类：

| category | linux | mac | delta |
|---|---:|---:|---:|
| total_nonnull | 1840 | 1111 | −729 |
| **java.*** (JDK) | **842** | **38** | **−804 (−95%)** |
| javax.* (第三方 jar) | 32 | 25 | −7 |
| jakarta.* | 0 | 0 | 0 |
| **org.owasp.*** (项目内部) | **891** | **891** | **0** |
| simple_name（无点，降级回退） | 61 | 144 | +83 |

关键 sink/source/relay FQN 是否存在（`reference_type` 计数）：

| qualified_name | linux | mac | 用途 |
|---|---:|---:|---|
| java.lang.String | 1 | **0** | 通用污点中继 |
| java.lang.StringBuilder | 1 | **0** | 通用污点中继 |
| java.lang.StringBuffer | 1 | **0** | 通用污点中继 |
| java.lang.Runtime | 1 | **0** | CWE-078 sink |
| java.lang.ProcessBuilder | 1 | **0** | CWE-078 sink |
| java.util.List | 5 | 2 | 容器中继 |
| java.sql.Statement | 1 | 1 | CWE-089 sink（顶层在） |
| java.sql.Connection | 1 | 1 | CWE-089 sink |
| javax.naming.directory.DirContext | 1 | 1 | CWE-090 sink（**未丢→090 无 FN**） |
| javax.xml.xpath.XPath | 1 | 1 | CWE-643 sink（顶层在） |
| javax.servlet.http.HttpServletRequest | **0** | **0** | source（**两端都为 0**，见 §9） |

**`Confirmed`**:
1. DB 层退化表现为 **JDK `java.*` 类型解析结果缺失**：`java.*` 掉 95%，而项目类（`org.owasp.*`）与第三方 jar 类（`javax.*`）基本完好。触发机制仍归入 §8 的 Likely/Possible。
2. 故对照鲜明——`java.lang.Runtime/ProcessBuilder`（078 sink）与 `java.lang.String/StringBuilder`（万能中继）在 Mac 库消失；crypto/LDAP/XML sink 在 `javax.*` 保留。

Linux 独有的 819 个 FQN 已落盘：`reports/data/linux_only_fqn.txt`（含 `java.io.*`、`java.lang.*`、`java.sql.*` 等大量 JDK 类）。

---

## 6. with_type vs without_type Evidence（type discovery vs method resolution）

两表 schema：

```
method_access_expression_with_type   (element_hash_id, type_hash_id NOT NULL, referen_method_hash_id NOT NULL, argument_list_hash_id)
method_access_expression_without_type(element_hash_id,                        referen_method_hash_id NOT NULL, argument_list_hash_id)
```

- 两表都有 `referen_method_hash_id` → **被调用方法的引用 token 仍被捕获**（method-name 解析没坏）。
- 仅 `with_type` 有 `type_hash_id` → **接收者/声明类型** 只在 `with_type` 被解析。
- `type_hash_id` 关联 `reference_type.oid`（已验证：join 命中 17195 行）。

**`Confirmed`** 对用户"type discovery vs method resolution"问题的回答：
- 这是 **type discovery 失败（DB 中 JDK `java.*` 类型解析结果大面积缺失）**，进而 **传导为 method-access 的 receiver-type 绑定失败**（`with_type`→`without_type`）。
- **不是** 语法/方法名解析失败（method 引用仍在），**不是** 源码索引失败（见 §5 项目类完好）。

样本（receiver type 取自 Linux `with_type`，即在 Mac 上被降级的那批调用）——BenchmarkTest00077（CWE-078）：
```
java.lang.String  x3   (中继)
java.lang.Process x1   (Runtime.exec 返回)
```
两者都是 `java.*` → 在 Mac 全部降级。

---

## 7. Link to Extra FN Cases

把 `mac-missing-testcases.json` 的 67 个文件与 DB 关联（`location → file` join）。

**聚合（全部 67 个 FN 文件）**：

| build | with_type | without_type |
|---|---:|---:|
| Linux | 579 | 649 |
| Mac | **73** | 1155 |

→ Mac 仅保住 Linux 的 **73 / 579 ≈ 12.6%** 类型解析；接收者类型崩塌恰好集中在变成 FN 的那批文件。

**被降级调用的接收者类型来源分桶**（Linux 端 `with_type`，`reports/data/fn_files_linux_receiver_types.tsv`）：

| 来源 | 计数 | 典型类型 |
|------|-----:|---------|
| **java.*** (JDK) | **247** | String×144, Process×25, Object×24, StringBuilder×22, String[]×18, Runtime×4, ProcessBuilder×1, ResultSet×1, Path×1, InputStream×1 |
| other（JDK 基元数组等） | 44 | byte[]×38, char[]×5 |
| javax.* | 4 | XPath / DocumentBuilder（对应唯一的 643 用例 00207） |
| **org.owasp.*** (项目) | **0** | — |

逐文件抽查（`with_type` 计数）：

| 用例 | CWE | Linux | Mac |
|------|-----|------:|----:|
| BenchmarkTest00077 | 078 | 12 | **0** |
| BenchmarkTest00060 | 022 | 5 | **0** |
| BenchmarkTest00207 | 643 | 12 | **1** |

**`Confirmed`** 用户四问的回答：
1. **多出的 FN 是否依赖 with_type？** 是。FN 文件里 ~95% 被降级调用的接收者是 `java.*`，**0 个是项目内部类**。
2. **涉及哪类 API？** 主要是 **JDK 类**（`String`/`StringBuilder` 中继、`Runtime`/`ProcessBuilder`/`Process` 命令注入 sink），少量第三方（XPath/DOM）。
3. **Linux 为何能命中？** Linux 库的 `java.*` 类型完整，sink/relay 都有 FQN，污点链能从 source 经 String 中继到达 sink。
4. **Mac 缺的是哪张表哪种 FQN？** `reference_type` 里的 `java.*`（−804），导致 `method_access_expression_with_type` 大量降级到 `without_type`（−27871）。

**污点链断裂机理**：taint 规则按 FQN 匹配 sink（如 `java.lang.Runtime.exec`）与中继摘要（如 `java.lang.String`/`StringBuilder.append` 的 taint propagation）。Mac 库这些 FQN 缺失 → 对应 method-access 进入 `without_type`（无 `type_hash_id`）→ sink 不识别、中继不传播 → 路径断 → FN。

**为何只掉到 95% 而非全崩**：只有"依赖 `java.*` 类型敏感匹配"的路径断裂；类型无关 / 项目内部短路径仍存活。crypto/LDAP 的 sink 在 `javax.*`（未丢）→ 327/328/330/614/090 全过。

---

## 8. Most Likely Root Cause

**`Likely`（综合 §3–§7）**：

> Mac 端 `sparrow database create` 在构建类型模型时 **没有把 JDK 系统/启动类（java.base 等）纳入类型解析路径**，而应用依赖 jar（servlet-api 等 → `javax.*`）被正常纳入。结果是 `reference_type` 里 `java.*` 几乎全失，所有以 `java.*` 为接收者的 method-access 退化为 `without_type`，污点链中继与 sink 匹配失效，污点类 CWE 产生 67 个 FN；非污点 / sink 在 `javax.*` 的 CWE 不受影响。

触发点 **`Possible`**（三选一，需建库日志确认）：
- (a) **JDK 发现失败**：Sparrow 经 `JAVA_HOME` / `/usr/libexec/java_home` 定位 JDK，本机该机制现已失效；若 6/12 建库时同样未正确指向 JDK，则 `java.base` 不会进入解析路径。**与现象最吻合**。
- (b) **arm64 + 模块化 JDK 读取问题**：Sparrow 的 Java 抽取后端在 macOS-arm64 上未能读取模块化运行时镜像（`jrt-fs`/`lib/modules`/`ct.sym`）。但 Linux 同为 Java 21 模块化却成功，故此项需平台特异性证据。
- (c) **Sparrow/GodelScript 版本差异**：两机 sparrow-cli 版本不同导致解析后端行为差异。

---

## 9. Alternative Hypotheses Ruled In/Out

| 假设 | 结论 | 依据 |
|------|------|------|
| Mac 缺 AST 节点 / 调用图不完整 | **Ruled out** | 130 表全同；method-access、constructor 总数两端相等（§4） |
| 源码索引 / 项目 package 解析问题 | **Ruled out** | `org.owasp.*` FQN 891 = 891（§5）；FN 文件里 0 个项目内部接收者被降级（§7） |
| servlet source 类型解析失败是差异点 | **Ruled out** | `javax.servlet.http.HttpServletRequest` 两端都为 0，Linux 仍 100% recall（§5）→ source 识别不走 reference_type FQN |
| JDK8 rt.jar vs JDK9+ 模块化 是差异点 | **Ruled out（作为差异点）** | 两端建库都是 Java 21 模块化（§3）；Linux 模块化能解析出 842 个 java.* |
| Java patch 差异 21.0.10 vs 21.0.11 致 95% 丢失 | **Ruled out** | patch 级差异不可能造成整族 `java.*` 丢失 |
| JDK 类型模型未加载（java.* 解析失败） | **Ruled in（Likely）** | `java.*` 842→38；relay/sink FQN 1→0；FN 文件降级接收者 95% 为 java.*（§5–§7） |
| 触发点 = JDK 发现失败（JAVA_HOME/java_home） | **Possible** | 现网 `/usr/libexec/java_home` 失败；建库未传 classpath（§3） |
| 触发点 = arm64 模块镜像读取 / sparrow 版本差异 | **Possible** | 无直接证据，需建库日志 / 版本比对 |

---

## 10. Recommended Fix

**P0 — 正式评测固定 Linux 库（`Confirmed` 可执行）**
- 所有正式指标 / 论文数据使用 Linux 建库结果（`java.*` 完整、Recall=100%）。
- Mac 库标记为 **非权威、不可用于正式数据**。
- 已有只读 gate 佐证：`python3 scripts/diagnose_codefuse_db_diff.py --db dataset/codefuse-db-mac/coref_java_src.db` → **FAIL / exit 1**。

**P1 — Mac 重建库时显式提供 JDK 与依赖（验证触发点 a）**
- 建库前确保 `JAVA_HOME` 指向真实 JDK 21，并验证 `"$JAVA_HOME"/bin/java -version` 可用、`"$JAVA_HOME"/lib/modules` 或 `jmods` 存在。
- 若 sparrow 支持显式 classpath/依赖参数，传入 benchmark 的 maven 依赖（servlet-api 等）与 JDK；用 `dataset/benchmark/pom.xml` 解析依赖。
- 重建后用本脚本复查 `java.*` 是否回升到数百量级、`method_access_expression_with_type` 是否回到 ~32k。

**P2 — 环境锁定（建议新增）**
- `configs/codefuse-env-linux.lock.md`、`configs/codefuse-env-mac.lock.md`，记录：OS / arch / Java version / sparrow(GodelScript) version / build command / classpath / DB sha256 / 关键表行数（`method_access_expression_with_type`、`reference_type.java.*`）。

**P3 — CI sanity gate（已交付）**
- `scripts/diagnose_codefuse_db_diff.py`，只读，规则：
  - `mac with_type ≥ 95% × linux with_type`（diff 模式）；
  - `java.*` reference types ≥ 200，且 `java.lang.String / java.util.List / java.lang.Runtime` 必须可解析（单库 gate 模式）；
  - 不满足则提示"不要用于正式评测"，exit 1。

---

## 11. Commands to Reproduce

**(a) 表级 / FQN / gate 一键复现**
```bash
python3 scripts/diagnose_codefuse_db_diff.py \
  --linux dataset/codefuse-db-linux/coref_java_src.db \
  --mac   dataset/codefuse-db-mac/coref_java_src.db \
  --out   reports/codefuse-db-diff-latest.md          # diff 模式, exit 1 = Mac 失败

python3 scripts/diagnose_codefuse_db_diff.py --db dataset/codefuse-db-linux/coref_java_src.db --out /tmp/g.md  # PASS
python3 scripts/diagnose_codefuse_db_diff.py --db dataset/codefuse-db-mac/coref_java_src.db   --out /tmp/g.md  # FAIL
```

**(b) 手动 SQL 关键证据**
```bash
L=dataset/codefuse-db-linux/coref_java_src.db; M=dataset/codefuse-db-mac/coref_java_src.db
for t in method_access_expression_with_type method_access_expression_without_type reference_type; do
  echo "$t  L=$(sqlite3 $L "SELECT count(*) FROM $t")  M=$(sqlite3 $M "SELECT count(*) FROM $t")"; done
# java.* 退化
for db in $L $M; do echo "$db java.*=$(sqlite3 $db "SELECT count(*) FROM reference_type WHERE qualified_name LIKE 'java.%'")  org.owasp.*=$(sqlite3 $db "SELECT count(*) FROM reference_type WHERE qualified_name LIKE 'org.owasp.%'")"; done
```

**(c) 最小复现实验（runnable，但本轮未执行——会写新 DB 且当前 JDK=17≠建库 21）**

探针文件已备好：`reports/data/repro/Mini.java`（含 servlet source + String/StringBuilder relay + Runtime sink）。
```bash
export CODEFUSE_HOME=<path-to-sparrow-cli>
export PATH="$CODEFUSE_HOME:$PATH"
# 实验1：不显式 JDK/classpath（复现当前失败路径）
sparrow database create -s reports/data/repro -lang java -o /tmp/mini-db-noclasspath
sqlite3 /tmp/mini-db-noclasspath/coref_java_src.db \
  "SELECT qualified_name FROM reference_type WHERE qualified_name LIKE 'java.%' OR qualified_name LIKE 'javax.%';"
# 实验2：显式指向 JDK21 + servlet-api（验证修复）
export JAVA_HOME=<path-to-jdk-21>          # 确认 $JAVA_HOME/bin/java -version 为 21
sparrow database create -s reports/data/repro -lang java -o /tmp/mini-db-withjdk
sqlite3 /tmp/mini-db-withjdk/coref_java_src.db \
  "SELECT count(*) FROM method_access_expression_with_type;"   # 期望明显高于实验1
```
判读：实验1 若 `java.lang.*` 缺失、`with_type` 偏低 → 复现本问题；实验2 若回升 → 证实触发点 (a) 并给出修复路径。

---

## 12. Remaining Risks

- **`Unknown`**: 6/12 建库当时的 `JAVA_HOME` / `java_home` 状态无法回溯；现网证据（java_home 失败、JDK 已换 17）只能作旁证。
- **`Unknown`**: Sparrow 内部为何未加载 JDK，缺建库 verbose 日志 / sparrow 版本号实证；触发点 (a)/(b)/(c) 未最终二选一。
- **`Possible` 偏差**: 最小复现实验在 **当前 JDK 17** 下运行，与建库时 21 不同；若实验1 未复现，仅说明"现网换 JDK 后行为变了"，不否定 6/12 的失败。建议用与建库一致的 JDK 21 复跑。
- **`Confirmed` 不受上述影响**: 无论触发点为何，"Mac 库 `java.*` 类型缺失、不可用于正式评测"已由 DB 证据确证；P0 决策稳健。

---

## 附：本轮新增 / 产出文件

- `scripts/diagnose_codefuse_db_diff.py` — 只读差分 + CI gate（新增）
- `reports/codefuse-db-mac-linux-rootcause-v2.md` — 本报告
- `reports/codefuse-db-diff-latest.md` — 自动生成的差分快照
- `reports/data/linux_only_fqn.txt` — Linux 独有 819 个 FQN
- `reports/data/fn_files_linux_receiver_types.tsv` — 67 个 FN 文件被降级调用的接收者类型分布
- `reports/data/repro/Mini.java` — 最小复现实验探针

> 本轮严格只读，未改动 rules / vep / 评测逻辑，未删除任何既有报告或数据库。
