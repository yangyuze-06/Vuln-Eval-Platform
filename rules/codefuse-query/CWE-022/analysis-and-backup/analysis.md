 # 1. 当前checker结构分析

  checker_taint_no_fallback_debug.gdl 可以拆成 6 个模块：

  1. 基础与入口

  - default_java_db()：固定加载 coref_java_src.db
  - main()：输出 cwe022_taint_no_fallback_debug() 结果

  2. Source 建模模块

  - is_http_source_call
  - is_source_expr
  - is_source_stmt
  - header 枚举链相关：
      - is_header_name_enumeration_call
      - is_header_value_enumeration_call
      - is_enumeration_next_element_call
      - is_header_name_enumeration_source_expr
      - is_header_enumeration_next_element_expr
      - is_header_value_enumeration_expr

  职责：定义“什么是用户输入”以及 header enumeration 的特殊传播入口。

  3. Sink 建模模块

  - is_path_sink_new
  - is_path_sink_call

  职责：识别文件路径相关危险点（构造器和静态方法两类）。

  4. Helper 模块

  - call_has_tainted_argument
  - call_has_tainted_receiver
  - new_has_tainted_argument
  - call_targets_callable

  职责：被 taint 与 findings 模块复用的通用判定逻辑。

  5. Taint 传播模块（核心）

  - is_tainted_var
  - is_tainted_expr

  职责：定义变量和表达式的污染传播闭包，包括局部赋值、参数传递、返回值传播、AST
  向上传播等。

  6. Debug Findings 模块

  - new_has_receiver_taint_return_arg
  - call_has_receiver_taint_return_arg
  - cwe022_taint_no_fallback_debug

  职责：只在 sink 处输出，并附带 reason（污染触发原因），用于解释命中路径而不是
  做最小告警集。

  ———

  # 2. source/sink/propagation详细机制

  ## 2.1 Source 建模

  当前 HTTP 输入识别主要靠字符串匹配 getPrintableText().contains(...)：

  - .getParameter(
  - .getParameterMap(
  - .getParameterValues(
  - .getParameterNames(
  - .getHeader(
  - .getHeaders(
  - .getQueryString(
  - .getCookies(
  - .getPathInfo(
  - .getRequestURI(
  - .getTheParameter(

  分两层：

  1. is_source_expr(e)：扫描全库 MethodAccessExpression，若 e.key_eq(c) 且命中上
     述字符串则 tainted。
  2. is_source_stmt(s)：语句级同样字符串匹配，主要给其他逻辑（早期/兼容）复用。

  Header enumeration 的结构化“半建模”：

  - getHeaderNames() 作为 source expr；
  - nextElement() 需要 receiver tainted；
  - getHeaders(x) 需要参数 tainted；
    这部分不是纯字符串单点，而是带了 receiver/argument taint 条件，算半结构化。

  结论：主干仍是字符串匹配，结构化只在少数路径上出现。

  ## 2.2 Sink 建模

  两类 sink，仍是 contains 匹配：

  1. is_path_sink_new(n)（构造器）

  - new java.io.File(
  - new java.io.FileInputStream(
  - new java.io.FileOutputStream(
  - new java.io.FileReader(
  - new java.io.FileWriter(
  - new java.io.RandomAccessFile(
  - new java.util.zip.ZipFile(

  2. is_path_sink_call(c)（方法调用）

  - java.nio.file.Files.newInputStream(
  - java.nio.file.Files.newOutputStream(
  - java.nio.file.Files.readAllBytes(
  - java.nio.file.Files.readAllLines(
  - java.nio.file.Files.readString(
  - java.nio.file.Files.write(

  命中判定不是直接“source->sink path”，而是在 sink 侧检查 tainted 参数/表达式来
  源并打 reason。

  ## 2.3 Taint propagation 机制

  ### Expression taint（is_tainted_expr）

  传播规则包括：

  1. 直接源：

  - is_source_expr(e) 或 header 枚举链相关三个谓词命中即 tainted。

  2. 变量引用传播：

  - 若某变量 v tainted，则其 v.getDirectUsage() 的引用表达式 tainted。

  3. AST 向上传播（upward）：

  - 若 child tainted 且 e == child.getParent()，则 e tainted。
  - 这会把污染从子表达式持续抬升到更大表达式节点。

  4. 调用返回污染：

  - e 是某 MethodAccessExpression 时，只要参数 tainted 或 receiver tainted，就把
    调用结果视为 tainted。

  5. 构造器结果污染：

  - e 是 NewExpression 且构造参数 tainted -> tainted。

  6. 跨过程 return 传播：

  - 调用点 call 绑定到 method m；
  - 若 m 内任意 return 的 result tainted，则 call tainted。

  ### Variable taint（is_tainted_var）

  传播规则包括：

  1. 局部变量初始化：

  - LocalVariable 初值 tainted -> 变量 tainted。

  2. 赋值：

  - ae.getSource() tainted 且目标定义对应变量 -> 变量 tainted。

  3. 跨过程参数传播：

  - tainted 实参 -> 被调函数对应 index 的 Parameter tainted（通过
    call_targets_callable + getArgument(idx)）。

  4. foreach 传播：

  - iteratedValue tainted -> iterationParameter tainted。

  5. receiver 污染：

  - 若某方法调用存在 tainted 参数，则其 callSite 对应接收者变量直接 tainted。

  ### 是否有 upward AST propagation？

  - 有，且是显式规则（child tainted -> parent tainted）。

  ### 是否有 inter-procedural 传播？

  - 有两类：

  1. 实参 -> 形参（参数传播）
  2. 被调函数 return tainted -> 调用表达式 tainted（返回传播）

  ## 2.4 Debug 机制

  cwe022_taint_no_fallback_debug(ruleId, sinkFile, line, reason) 在 sink 处输出
  理由：

  - 对 NewExpression sink：
      - reason = "tainted_constructor_arg" 且 new_has_tainted_argument(n)
      - reason = "receiver_taint_to_return_taint" 且
        new_has_receiver_taint_return_arg(n)
  - 对 MethodAccessExpression sink：
      - reason = "tainted_call_arg" 且 call_has_tainted_argument(c)
      - reason = "receiver_taint_to_return_taint" 且
        call_has_receiver_taint_return_arg(c)

  触发条件都是：

  - ruleId = "CWE-022"
  - sinkFile、line 绑定到 sink 位置
  - 对应 reason 条件成立

  ———

  # 3. 关键问题列表（逐条）

  1. 大量 getPrintableText().contains()，语义不稳

  - Source 与 sink 大量依赖文本片段匹配，而不是 API 符号解析。
  - 问题：
      - 容易误匹配（变量名/注释/字符串片段形似）。
      - 对 import、全限定名、格式变化敏感。
      - 难区分同名方法不同类型（多态/重载场景）。

  2. 过度传播（over-taint）点一：AST 向上传播过宽

  - 规则：if is_tainted_expr(child) && e == child.getParent() -> tainted
  - 问题：
      - 任何包含 tainted 子节点的父表达式都会被污染。
      - 很容易把局部污染扩展到大表达式树，召回高但精度下降明显。

  3. 过度传播点二：receiver taint 规则激进

  - 规则：调用有 tainted 参数 -> receiver 变量 tainted（is_tainted_var 最后一
    段）。
  - 后果：
      - 将“对象被调用时接收 tainted 参数”解释为“对象状态污染”，非常激进。
      - 配合“调用结果 tainted if receiver tainted”会放大链式污染。

  4. 过度传播点三：调用结果保守传播过宽

  - 规则：call_has_tainted_argument(call) || call_has_tainted_receiver(call) ->
    调用表达式 tainted。
  - 问题：
      - 几乎把所有“带 tainted 参数的函数调用返回值”都当 tainted。
      - 缺乏白名单/语义模型（如 sanitize、normalization、constant-return）。

  5. 性能风险：存在多层全库嵌套扫描

  - 典型模式：
      - 在 is_tainted_expr 中 for (child in Expression(...)) 递归调用
        is_tainted_expr(child)。
      - 在 is_tainted_var 里多层 for（Assignment -> Reference -> Variable；
        Parameter -> Callable -> MethodAccessExpression）。
      - call_targets_callable 每次调用遍历全库 Method/Constructor。
  - 问题：
      - 递归 + 全库循环相互嵌套，复杂度高，规模稍大就可能慢。
      - 缺少缓存/分层中间关系谓词。

  6. Debug reason 可解释性有限

  - reason 只覆盖 4 类触发条件。
  - 对“具体 source 入口”“跨过程路径节点”没有直接输出，调试仍需二次分析。

  7. Sink 粒度偏粗

  - 比如 new java.io.File( 被直接视为 sink，容易把“仅构造路径对象、未访问文件系
    统”的代码也计入风险前置节点。

  ———

  # 4. 重构设计方案（重点）

  ## 模块A：Source 重构（字符串匹配 -> 语义建模）

  设计：

  1. 引入“方法符号级”source 谓词：

  - 基于 receiver 类型 + 方法名 + 参数签名识别 HttpServletRequest 等真实入口。

  2. 把 header enumeration 建模成显式数据流边：

  - getHeaderNames -> nextElement -> getHeaders(name) -> nextElement(value) 用专
    门谓词链表达。

  3. 分级 source：

  - strong source（request 参数/header/query/path）
  - weak source（cookies、自定义 wrapper）

  原因：

  - 显著降低文本误匹配。
  - 便于调参与评估不同 source 强度。

  trade-off：

  - Precision 大幅提升；Recall 可能略降（需要补充框架适配）。

  ## 模块B：Sink 重构（API 语义分层）

  设计：

  1. 分离“路径对象构造”与“真实文件访问”：

  - File/Path 构造归为中间节点，不直接告警。
  - FileInputStream/Files.read*/write* 等 I/O 操作作为真正 sink。

  2. 按 CWE-022 场景分组 sink：

  - 读文件、写文件、归档处理（ZipFile）分开建模，输出附带 sink kind。

  原因：

  - 减少“仅创建对象”导致的误报。
  - 后续能按风险级别处理。

  trade-off：

  - Precision 提升，Recall 对早期路径构建场景可能下降，但更可控。

  ## 模块C：Propagation 收紧（核心）

  设计：

  1. 去掉全局 AST 向上传播“无限上抬”：

  - 改为有限传播规则（赋值、参数传递、返回值、特定表达式构造）。

  2. 收缩 receiver taint：

  - 默认关闭“tainted arg -> tainted receiver”；
  - 仅对已知可变容器/构建器白名单开启。

  3. 调用返回污染改为“模型驱动”：

  - 仅对 identity/concat/path-join 等可证明传递污染的方法传播；
  - 对 sanitizer 建立去污规则（canonicalize + base-path check 等可留接口）。

  4. 跨过程传播增加边界：

  - 限制调用深度/递归层；
  - 优先同包/同项目方法，降低全库扩散。

  原因：

  - 当前误报与性能瓶颈主要来自传播过宽。

  trade-off：

  - Precision 明显提升、性能改善；Recall 可能下降，需要通过评测集迭代补回。

  ## 模块D：Debug 输出重构

  设计：

  1. 输出结构化原因：

  - reason_code + source_kind + sink_kind + propagation_kind。

  2. 增加“关键路径摘要”：

  - 至少输出 source 行、sink 行、1~2 个关键中间节点。

  3. 区分“strict mode / exploratory mode”：

  - strict 只输出高置信规则；
  - exploratory 保留更宽规则但打低置信标签。

  原因：

  - 便于你做规则调参与误报归因。

  trade-off：

  - 实现复杂度增加，但维护效率提升。

  ## 模块E：规则保留/删除建议

  保留：

  - tainted_argument -> sink 主线（高价值）
  - 参数/返回值跨过程传播（但要加约束）
  - header enumeration 专项链路（可保留，需类型约束）

  收缩：

  - receiver_taint_to_return_taint（改为白名单）
  - new java.io.File( 直接作为最终 sink（改为中间节点）

  删除或默认关闭：

  - 全局 child->parent AST upward 规则
  - 无类型约束的 contains 大范围匹配逻辑（迁移后废弃）

  ———

  如果你下一步要我继续，我可以基于这个设计直接产出一份“重构任务拆分清单（按优先
  级+风险）”，仍然先不改代码。