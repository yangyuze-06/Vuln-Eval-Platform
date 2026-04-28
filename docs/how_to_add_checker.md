# 如何添加新的检查器 (Checker)

## 规则
- **严禁重复污点逻辑**：所有数据流传播必须由中央引擎处理。
- **必须复用 TaintTracking.gdl**：始终导入并使用共享的 `TaintTracking` 模块。
- **聚焦于特定性**：新检查器只需定义其独特的 **汇点 (Sink)**、**清洗器 (Sanitizer)** 和 **ruleId**。

## 最小模板
```rust
use coref::java::*
use security::java::JavaServletSources::*
use security::java::TaintTracking::*
use security::java::sinks::MyNewSinks::*

fn myNewFinding(ruleId: string, sinkFile: string, line: int) -> bool {
    for (sink in MethodAccessExpression(default_java_db())) {
        if (isMyNewSink(sink) && callHasTaintedArgument(sink) && ruleId = "CWE-XXX") {
            return true
        }
    }
}

fn main() {
    output(myNewFinding())
}
```
