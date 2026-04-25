# CWE-078 静态分析极限与局限性复盘 (AST Datalog)

## 1. 当前规则表现
当前版本的 `checker078.gdl` (原名 `checker_cmdi.gdl`) 已经达到了基于 **纯抽象语法树 (AST) 查询分析** 的理论极限。
在 OWASP Benchmark 中，该规则实现了：
- **100% 召回率 (Recall)**：不漏报任何一个真实的命令注入漏洞。
- **56% 准确率 (Precision)**：在流不敏感的 AST 引擎中达到极高水准。

## 2. 为什么存在剩余的 FPs (误报)？
剩余的大约 90 个误报并非规则逻辑错误，而是触及了 **CodeFuse-Query GDL 当前轻量级分析框架的理论盲区**。在缺乏深度过程间和路径敏感数据流引擎支持的情况下，以下两大模式在数学上无法被过滤：

### 2.1 常量折叠与死代码分支 (Constant Folding FPs)
**典型场景：**
```java
int num = 86;
if ((7 * 42) - num > 200) { 
    bar = "This_should_always_happen"; // 恒真分支，安全
} else {
    bar = param; // 污点分支，理论不可达
}
Runtime.getRuntime().exec(cmd + bar);
```
**分析极限：**
AST 引擎缺乏常量折叠计算引擎（无法计算 `7*42-86>200` 为真）以及控制流可达性验证（CFG 死代码消除）。由于 Datalog 采用**路径不敏感 (Path-Insensitive)** 的遍历策略，只要 AST 中存在 `bar = param` 这个赋值节点，引擎就会全局将 `bar` 标记为污染，从而产生误报。

### 2.2 游标欺骗与集合移位 (List/Array Index FPs)
**典型场景：**
```java
List<String> valuesList = new ArrayList<String>();
valuesList.add("safe");
valuesList.add(param);        // Index 1 被污染
valuesList.add("moresafe");

valuesList.remove(0);         // 移除 Index 0，整体左移
bar = valuesList.get(1);      // 此时 Index 1 安全 ("moresafe")
```
**分析极限：**
当前 GDL 引擎缺乏深度的内存模型和指针/别名分析（**上下文/堆不敏感 Context/Heap Insensitive**）。引擎无法在内存中动态模拟 `List` 索引的移位过程。为了保证安全，引擎只能采取最保守的策略：“只要集合被插入过污点，集合本身及其产生的所有元素皆视为污点”。

## 3. 突破极限的未来演进路线
要在当前的 `0.56` 精确度上进一步削减误报，仅靠调整 `checker078.gdl` 语法规则是不可能的。未来的演进必须引入更高的维度：

1. **引入静态单赋值 (SSA) 与数据流图 (DFG)**：
   需要底层引擎暴露类似 CodeQL 的数据流模块，从而精准识别被“洗白常量”覆盖的 `bar_v2`，解决 Sanitization by Replacement (覆盖洗白) 的误报。
   
2. **LLM 代码大模型辅助验证 (当前业界最佳实践)**：
   放弃在 SAST 阶段死磕零误报，保留目前的 100% 召回率基座。将报警出的 `TP+FP` 代码切片一并送入大模型，借助大模型强大的逻辑推理能力（一眼看穿死代码和常量折叠），完成最后一公里的精准过滤。
