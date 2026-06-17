# CodeFuse/Sparrow macOS JDK 发现机制调查

> 这是对 `codefuse-db-mac-linux-rootcause-v2.md` 中诊断的第 3 阶段跟进
> （commit `9c3ce48`）。目标：通过一个最小复现实验，把根因从
> **可能：JDK 发现失败** 推进到已验证分类。
> 日期：2026-06-18。未重建完整 DB，未修改规则、vep 或 evaluator。

## 1. 目标

通过单文件探针确认：macOS 上缺失 `java.*` JDK 类型模型，是否由 JDK
发现机制 / `JAVA_HOME` 配置触发；以及修正配置后，完全限定名（FQN）解析
是否恢复。

待验证命题：

- **A.** *当前* Mac 环境是否无法在 `Mini.java` 中解析 JDK FQN
  （`java.lang.String`、`StringBuilder`、`Runtime`、`java.util.List`）？
- **B.** 将构建指向正确的 JDK home 后，FQN 是否恢复？
- **C.** 如果 B 成立，是否可将根因从 *Possible* 升级为 *Confirmed*？

## 2. 基线诊断（来自 v2 报告）

完整 DB，Linux vs Mac（6/11-6/12 构建）：

| metric | Linux | Mac | delta |
|---|---:|---:|---|
| `reference_type` `java.*`（JDK） | 842 | 38 | -804 (-95%) |
| `method_access_expression_with_type` | 32371 | 4500 | -27871 |
| internal `org.owasp.*` | 891 | 891 | 0（不变） |
| third-party `javax.*` | 32 | 25 | 大多保留 |

延续此前解释：项目内部类型和第三方 jar 类型仍然存在；只有 **JDK 系统类型**
（`java.base` 等）缺失 -> JDK 类型模型从未进入 Sparrow 的解析路径。v2
将触发因素标记为 *Possible: JDK discovery failure* 和 *Possible: arm64
module-image parsing bug*。

## 3. 当前 Java 环境

| probe | result |
|---|---|
| OS | macOS 26.5.1 (build 25F80), Darwin 25.5.0, **arm64** |
| Sparrow | `2.1.0` at `…/codefuse/sparrow-cli/sparrow` |
| `JAVA_HOME` | `/opt/homebrew/opt/openjdk@17`（Homebrew **keg prefix**） |
| `which java` / version | `…/openjdk@17/bin/java` -> `17.0.19` |
| `/usr/libexec/java_home -V` | **FAIL**: "Unable to locate a Java Runtime" |
| `/usr/libexec/java_home -v 21` / `-v 17` | **FAIL**（相同） |
| `/Library/Java/JavaVirtualMachines` | **空**（没有向 macOS 注册的 JDK） |
| Homebrew `openjdk@21/libexec/openjdk.jdk` | 存在 |
| Homebrew `openjdk@17/libexec/openjdk.jdk` | 存在 |

**关键结构性发现**：keg prefix *不是* 完整 JDK home：

| path | `bin/` | `lib/modules` | `jmods/` |
|---|:--:|:--:|:--:|
| `/opt/homebrew/opt/openjdk@17`（prefix，即当前 `JAVA_HOME`） | yes | **缺失** | **缺失** |
| `…/openjdk@17/libexec/openjdk.jdk/Contents/Home` | yes | yes (129 MB) | yes |
| `/opt/homebrew/opt/openjdk@21`（prefix） | yes | **缺失** | **缺失** |
| `…/openjdk@21/libexec/openjdk.jdk/Contents/Home` | yes | yes (141 MB) | yes |

prefix 下的 `bin/java` 是 wrapper/symlink，仍然可以*运行*（JVM 能定位自己的
内部组件），但 `$JAVA_HOME/lib/modules` 和 `$JAVA_HOME/jmods` 不存在于该
prefix 下。而外部工具需要读取这些位置来构建 JDK 类型模型。

## 4. Mini.java 复现（当前环境，未修复）

探针文件 `reports/data/repro/Mini.java`（未修改）覆盖 `java.util.List`、
`java.lang.String`、`StringBuilder`、`Runtime`，以及一个 `javax.servlet`
来源。构建：

```bash
mkdir -p /tmp/vep-mini-db-current-logs
sparrow database create -s reports/data/repro -lang java \
  -o /tmp/vep-mini-db-current --verbose --log-dir /tmp/vep-mini-db-current-logs
# extractor log: "java home: /opt/homebrew/opt/openjdk@17"
```

查询结果（`/tmp/vep-mini-db-current/coref_java_src.db`）：

| metric | value |
|---|---:|
| `reference_type` total | 5 |
| `reference_type` `java.*` | **0** |
| `method_access_expression_with_type` | **0** |
| `method_access_expression_without_type` | 7 |
| `java.lang.String` / `StringBuilder` / `Runtime` / `List` | 0 / 0 / 0 / 0 |

这 5 条 `reference_type` 只是源码层面的裸名称，**没有 FQN**：
`Exception`、`HttpServletRequest`、`List<String>`、`String`、`StringBuilder`。

**解释：** 当前环境复现了失败路径：所有方法访问都降级为 `without_type`；
JDK FQN 数量为 0。与完整 DB 症状一致。

## 5. JDK Home “修复”

`/usr/libexec/java_home` 注册步骤（`sudo ln -sfn …openjdk.jdk
/Library/Java/JavaVirtualMachines/openjdk-21.jdk`）需要 `sudo`，而本会话没有
免密 `sudo`，因此**没有**修改系统注册表。实验改为直接将 `JAVA_HOME` 覆盖到
真实 JDK home；这在功能上等价，因为 `/usr/libexec/java_home` 本身也会返回同
一个 `Contents/Home` 路径：

```bash
JAVA_HOME=/opt/homebrew/opt/openjdk@21/libexec/openjdk.jdk/Contents/Home
# bin/java -version -> 21.0.11 ; lib/modules + jmods/java.base.jmod present
```

## 6. 修复后的 Mini.java

使用 `JAVA_HOME` -> JDK21 `Contents/Home` 重建
（`/tmp/vep-mini-db-jdk21`，日志：`java home: …/openjdk@21/…/Contents/Home`）：

| metric | value |
|---|---:|
| `reference_type` total | 7 |
| `reference_type` `java.*` | **6** |
| `method_access_expression_with_type` | **6** |
| `method_access_expression_without_type` | 1 |

`java.*` 行：`java.lang.Exception`、`java.lang.Process`、`java.lang.Runtime`、
`java.lang.String`、`java.lang.StringBuilder`、
`java.util.List<java.lang.String>`。（`List` 以泛型形式解析，因此精确匹配
`='java.util.List'` 为 0，但 FQN 已存在。`ProcessBuilder`=0 是因为探针使用
的是 `Runtime`，不是 `ProcessBuilder`；因此出现的是 `java.lang.Process`。）
唯一剩余的 `without_type` 是 `javax.servlet` 调用 `req.getParameter`：第三方
jar 不在 classpath 上，这是与 JDK 模型不同的独立问题。

**版本无关性检查**：再次使用 **JDK17** `Contents/Home` 重建
（`/tmp/vep-mini-db-jdk17fix`）：结果相同，`java.*`=6、`with_type`=6、
`without_type`=1。因此修复点是 **home 路径**，不是版本。

## 7. 前后对比

| metric | current (`JAVA_HOME`=keg prefix @17) | jdk17 fixed (Contents/Home) | jdk21 fixed (Contents/Home) |
|---|---:|---:|---:|
| `reference_type` total | 5 | 7 | 7 |
| `reference_type` `java.*` | **0** | **6** | **6** |
| `method_access_with_type` | **0** | 6 | 6 |
| `method_access_without_type` | 7 | 1 | 1 |
| `java.lang.String` | 0 | 1 | 1 |
| `java.lang.StringBuilder` | 0 | 1 | 1 |
| `java.lang.Runtime` | 0 | 1 | 1 |
| `java.lang.ProcessBuilder` | 0 | 0（探针中不适用） | 0（探针中不适用） |
| `java.util.List` | 0 | 1（泛型形式） | 1（泛型形式） |

这是计划中的 **Case 1**：当前环境失败，修正 home 后成功。

## 8. 结论分类

- **Confirmed**：在当前 Mac 环境中，缺失 `java.*` 的失败可复现
  （Mini `java.*`=0，`with_type`=0），并且通过将构建使用的有效 JDK home
  （`JAVA_HOME`）指向包含 JDK **module image**（`lib/modules` + `jmods`）的
  目录后完全修复。根因机制：`JAVA_HOME` 被设为 Homebrew **keg prefix**
  `/opt/homebrew/opt/openjdk@17`；该路径能运行 `java`，但没有 module image，
  因此 Sparrow 无法构建 JDK 类型模型。
- **Confirmed（排除为原因）**：**JDK 版本不是触发因素**。只要 home 正确，
  17 和 21 都能恢复 FQN。v2 中的 “arm64 module-image parsing bug” 假设也基本
  **排除**：当 home 正确时，arm64 Sparrow 能正确读取 `lib/modules`。
- **Confirmed**：空的 `/usr/libexec/java_home` 注册表（
  `/Library/Java/JavaVirtualMachines` 中没有 JDK）是从发现机制侧看到的同一个
  失败；正确注册后会把 Sparrow 指向同一个可修复构建的 `Contents/Home` 路径。
- **Likely（无法回溯验证）**：这一确切机制导致了 6/12 完整 DB 回归
  （842->38）。该机制与症状精确吻合，但无法恢复 6/12 构建时的
  `JAVA_HOME`/`java_home` 状态，所以对那次特定构建的归因仍为 *Likely*，
  不是 *Confirmed*。
- **Unknown**：修正 `JAVA_HOME` 后完整 Mac 重建是否能与 Linux 完全一致
  （842 条 `java.*`）；本次未测试（仅 Mini 探针）。

### 必答项

1. **是否复现 `java.*` 缺失？** 是。当前环境 Mini：`java.*`=0，
   `with_type`=0，`without_type`=7。
2. **修复是否恢复 `java.*`？** 是。`JAVA_HOME` -> `Contents/Home`（17 *或*
   21）：`java.*`=6，`with_type`=6，`without_type`=1。
3. **是否升级为 Confirmed？** 对触发机制而言，是（Case 1）。对 6/12 构建的
   具体归因仍为 *Likely*。
4. **是否重建完整 Mac DB？** 对本结论而言不需要。建议后续作为单独验证步骤，
   只在修复 `JAVA_HOME` 后执行，用于检查是否达到 842 parity。
5. **正式评测是否继续使用 Linux DB？** 是。直到使用修正后 `JAVA_HOME` 的完整
   Mac DB 重建完成，并通过 Linux `java.*` 计数校验。

## 9. 建议下一步

1. **为构建设置正确的 JDK home。** 二选一：
   - `export JAVA_HOME=/opt/homebrew/opt/openjdk@21/libexec/openjdk.jdk/Contents/Home`
     （或 `@17`），并确认 `$JAVA_HOME/lib/modules` 存在；**或**
   - 向 macOS 注册，让 `/usr/libexec/java_home` 可用（永久方案，需要 sudo）：
     ```bash
     sudo ln -sfn /opt/homebrew/opt/openjdk@21/libexec/openjdk.jdk \
       /Library/Java/JavaVirtualMachines/openjdk-21.jdk
     export JAVA_HOME=$(/usr/libexec/java_home -v 21)
     ```
2. 在构建脚本中添加 **pre-build guard**：断言
   `[ -e "$JAVA_HOME/lib/modules" ] || [ -d "$JAVA_HOME/jmods" ]`，否则明确失败。
   这正是本可捕获该回归的检查。
3. 可选：使用修正后的 `JAVA_HOME` 重建**完整** Mac DB，并重新运行 `java.*`
   计数，在把正式评测从 Linux 切换走之前确认 Linux parity（约 842）。
4. 在步骤 3 通过之前，**正式评测仍使用 Linux DB**。

---

### 复现命令（留档）

```bash
# current (fails)
mkdir -p /tmp/vep-mini-db-current-logs
sparrow database create -s reports/data/repro -lang java \
  -o /tmp/vep-mini-db-current --verbose --log-dir /tmp/vep-mini-db-current-logs

# fixed (JDK21 Contents/Home)
JH=/opt/homebrew/opt/openjdk@21/libexec/openjdk.jdk/Contents/Home
mkdir -p /tmp/vep-mini-db-jdk21-logs
JAVA_HOME="$JH" PATH="$JH/bin:$PATH" sparrow database create \
  -s reports/data/repro -lang java -o /tmp/vep-mini-db-jdk21 \
  --verbose --log-dir /tmp/vep-mini-db-jdk21-logs

# query template
DB=<db>/coref_java_src.db
sqlite3 "$DB" "SELECT count(*) FROM reference_type WHERE qualified_name LIKE 'java.%';"
sqlite3 "$DB" "SELECT count(*) FROM method_access_expression_with_type;"
sqlite3 "$DB" "SELECT count(*) FROM method_access_expression_without_type;"
```

注意：Sparrow **不会**创建 `--log-dir`；必须先创建该目录
（`FileNotFoundError: …/sparrow-cli-error.log`）。

### Git 备注

调查时 `HEAD` 为 `a4fa7f2`（`chore:update the .gitignore`）；诊断 commit
`9c3ce48` 是 `HEAD~1`。工作区干净。
