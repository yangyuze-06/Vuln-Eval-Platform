# CodeFuse DB Mac vs Linux — 根因确认报告

**生成时间**: 2026-06-17
**对比对象**: `dataset/codefuse-db-linux/coref_java_src.db` (259MB) vs `dataset/codefuse-db-mac/coref_java_src.db` (258MB)
**结论**: 差异根因是 **Mac 端 Sparrow 类型解析失败（外部类型未解析为全限定名）**，而非旧报告假设的「AST 节点缺失 / 调用图不完整 / Java 21 字节码差异」。

---

## 1. 结构对比：130 张表完全相同，仅 5 张行数不同

| 表 | Linux | Mac | Δ | 含义 |
|----|------:|----:|---:|------|
| `method_access_expression_with_type` | 32371 | 4500 | **−27871** | 解析出接收者类型的方法调用 |
| `method_access_expression_without_type` | 39455 | 67326 | **+27871** | 未解析类型的方法调用 |
| `constructor_invocation` | 3683 | 5172 | +1489 | 已解析构造调用 |
| `new_expression` | 6026 | 4537 | −1489 | 未解析 `new` 表达式 |
| `reference_type` | 1840 | 1111 | −729 | 引用类型表 |

**关键点**：前两行 Δ 完全配对（±27871），method-access 总数两端都是 71826；构造同理（±1489，总数 9709）。
→ 节点没丢，只是 **从 `with_type` 掉到了 `without_type`**：类型解析失败。旧报告「Mac 缺 AST 节点」假设被证伪。

## 2. 直接证据：reference_type 全限定名 vs 简单名

Linux 独有 830 个引用类型、Mac 独有 101 个。逐条对比发现是 **同一批类型的全限定 vs 简单名** 退化：

| Linux（已解析 FQN） | Mac（退化为简单名） |
|---|---|
| `java.lang.Runtime` | `Runtime` |
| `java.lang.ProcessBuilder` | `ProcessBuilder` |
| `java.sql.Statement` / `Connection` / `ResultSet` | `Statement` / `Connection` / `ResultSet` |
| `javax.servlet.ServletRequest` / `ServletResponse` | `ServletRequest` / `ServletResponse` |
| `javax.xml.xpath.XPathExpression` | （未解析） |
| `javax.naming.directory.BasicAttributes` | `BasicAttributes` |
| `java.util.List<String>` | `List<String>` / `LinkedHashMap<>`（泛型参数也丢） |

Mac 端 Sparrow **无法把 JDK / 库类型解析到全限定名**，连核心 `java.lang.*` 都失败，回退成裸简单名。

## 3. 为什么导致漏报（FN）

污点规则的 source/sink 按 **全限定名 + 方法名** 匹配，例如：
- sink: `java.lang.Runtime.exec` / `java.lang.ProcessBuilder.<init>`
- source: `javax.servlet.http.HttpServletRequest.getParameter`

当接收者类型只剩 `Runtime`（无包名），签名匹配失败 → 该调用进入 `method_access_expression_without_type`（无 `type_hash_id`）→ source/sink 识别不到 → 整条数据流断裂 → FN。

### 逐用例验证（缺失测试用例）

| 测试用例 | Linux `with_type` | Mac `with_type` |
|---|---:|---:|
| BenchmarkTest00077 (CWE-078) | 12 | **0** |
| BenchmarkTest00060 (CWE-022) | 5 | **0** |
| BenchmarkTest00207 (CWE-643) | 12 | **1** |

Mac 端这些文件的「已解析类型方法调用」几乎归零。全局看，Mac 只保住 4500/32371 ≈ **14%** 的类型解析。

### 为什么 CWE-327/328/330/614 不受影响

这几类（弱加密 / 弱哈希 / 不安全随机 / Cookie 无 Secure）靠**本地模式**检测（算法字符串字面量、`getInstance("DES")`、`new Random()`、单表达式配置），不依赖 servlet source→sink 的跨过程污点链，故类型解析退化时仍能命中。受影响的 022/078/079/089/501/643 全部是污点追踪类，必须连通 source 与 sink。

## 4. 根因定位（DB 层已确定 / Sparrow 层待查）

DB 证据已确定 **发生了什么**：Mac 端外部类型解析退化为简单名。

`command.txt` 的建库命令未显式传 classpath/依赖 jar：
```
sparrow database create -s <src> -lang java -o <out>
```
故 Sparrow 需自行定位 JDK + 库 jar 来解析类型。**Linux 找到了（FQN 完整），Mac 没找到**。可能原因（需在 Sparrow 侧确认）：
1. Mac 上 `JAVA_HOME` / bootclasspath 未被 Sparrow 正确发现；
2. Mac 与 Linux 的 Sparrow 版本 / 类型解析后端行为不同；
3. 建库时 benchmark 依赖 jar 未在解析路径上（servlet-api 等）。

## 5. 建议

1. **最终评测用 Linux 库**（Recall=100%，FQN 完整）。Mac 库不可作正式数据。
2. Mac 复现：建库时显式提供 classpath（JDK + benchmark 依赖 jar），重建后复查
   `SELECT count(*) FROM method_access_expression_with_type;` 是否回升到 ~32k。
3. 向 CodeFuse/Sparrow 反馈跨平台类型解析不一致：附本报告第 2、3 节证据。

## 复现命令

```bash
L=dataset/codefuse-db-linux/coref_java_src.db
M=dataset/codefuse-db-mac/coref_java_src.db
# 行数差异
for t in method_access_expression_with_type method_access_expression_without_type reference_type; do
  echo "$t L=$(sqlite3 $L "SELECT count(*) FROM $t") M=$(sqlite3 $M "SELECT count(*) FROM $t")"
done
# FQN 退化证据
sqlite3 $L "SELECT qualified_name FROM reference_type ORDER BY 1" > /tmp/lr.txt
sqlite3 $M "SELECT qualified_name FROM reference_type ORDER BY 1" > /tmp/mr.txt
comm -23 /tmp/lr.txt /tmp/mr.txt | grep -E '^java' | head   # Linux 独有的 FQN
```
