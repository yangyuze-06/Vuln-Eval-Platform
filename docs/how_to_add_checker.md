# 如何新增 Checker

## 基本规则

- 不复制 taint propagation 逻辑。
- 注入类和 source-to-sink 漏洞优先复用 `TaintTracking.gdl`。
- API 误用 checker 如果直接 API 建模足够，不要强行使用 taint tracking。
- 新 checker 应保持 thin：`checkerXXX.gdl` 主要连接 source、sink、sanitizer 和 reporting。
- CWE-specific sink 放在 `rules/codefuse-query/lib/security/java/sinks/*.gdl`。
- CWE-specific sanitizer、barrier 和 scope suppression 放在 `rules/codefuse-query/lib/security/java/sanitizers/*.gdl`。
- benchmark-specific suppression 必须明确标记为 benchmark-only，不应直接当作 upstream-ready 逻辑。

## 模板 A：污点型 Checker

适用于 SQL 注入、LDAP 注入、XPath 注入、命令注入、路径遍历、XSS、信任边界写入等 source-to-sink 漏洞。

```rust
// script
use coref::java::*
use security::java::JavaServletSources::*
use security::java::TaintTracking::*
use security::java::sanitizers::MyCweSanitizers::*
use security::java::sinks::MyCweSinks::*

fn default_java_db() -> JavaDB {
    return JavaDB::load("coref_java_src.db")
}

fn has_tainted_sink_argument(c: MethodAccessExpression) -> bool {
    return callHasTaintedArgument(c)
}

fn my_cwe_findings(ruleId: string, sinkFile: string, line: int) -> bool {
    for (c in MethodAccessExpression(default_java_db())) {
        if (
            isMyCweSinkCall(c) &&
            has_tainted_sink_argument(c) &&
            !isMyCweSanitizerCall(c)
        ) {
            let (loc = c.getLocation()) {
                let (f = loc.getFile().getRelativePath()) {
                    let (l = loc.getStartLineNumber()) {
                        if (
                            ruleId = "CWE-XXX" &&
                            sinkFile = f &&
                            line = l
                        ) {
                            return true
                        }
                    }
                }
            }
        }
    }
}

fn main() {
    output(my_cwe_findings())
}
```

建议：

- 注入类通常应复用 `JavaServletSources.gdl` 和 `TaintTracking.gdl`。
- 如果风险参数位置明确，优先做 sink-specific argument gate。
- 不要复制 `isTaintedExpr`、`isTaintedVar` 或其传播实现。
- 如果 precision filter 只对某个 CWE 有意义，应放在对应 CWE sanitizer/scope 模块。

## 模板 B：API 误用 Checker

适用于漏洞语义本身就是 API 选择或配置错误的规则，例如弱加密、弱哈希、弱随机、Cookie 安全标志。

```rust
// script
use coref::java::*
use security::java::sinks::MyApiMisuseSinks::*

fn default_java_db() -> JavaDB {
    return JavaDB::load("coref_java_src.db")
}

fn my_api_misuse_findings(ruleId: string, sinkFile: string, line: int) -> bool {
    for (c in MethodAccessExpression(default_java_db())) {
        if (isUnsafeApiCall(c)) {
            let (loc = c.getLocation()) {
                let (f = loc.getFile().getRelativePath()) {
                    let (l = loc.getStartLineNumber()) {
                        if (
                            ruleId = "CWE-XXX" &&
                            sinkFile = f &&
                            line = l
                        ) {
                            return true
                        }
                    }
                }
            }
        }
    }
}

fn main() {
    output(my_api_misuse_findings())
}
```

建议：

- Crypto、hash、random、cookie 配置类规则不应使用 taint tracking，除非 benchmark 或 CWE 语义明确需要动态不可信输入。
- 优先做常量/API 匹配，例如 `MessageDigest.getInstance("MD5")` 或 `Math.random()`。
- 不要报告一个 API family 的所有调用，只报告明确不安全的算法、模式、构造函数或配置状态。
- 对象状态推理应保留在 checker 或 CWE-specific 模块内部。

## 开发清单

1. 阅读一个相似 checker 和 sink 模块。
2. 新增一个 CWE-specific sink 或 misuse 模块。
3. 新增 sanitizer 模块，即使第一版只是 default false。
4. `checkerXXX.gdl` 尽量控制在 150 行以内。
5. 添加最小 positive / negative Java 示例。
6. 运行 `./scripts/evaluation/eval_checker.sh XXX`。
7. 在 experiment report 中记录 TP / FP / FN / Precision / Recall / F1。
8. 如果需要 precision patch，suppression 应保持 CWE-specific，并说明是否 benchmark-only。
