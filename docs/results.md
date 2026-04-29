# 评测结果

以下是当前 CodeFuse-Query 规则在 OWASP Benchmark 上的结果。`Findings` 表示 evaluator 去重后的 finding 数量。

## 总览

- 已完成 checker：11 个。
- 所有已完成 checker 当前在 benchmark 上 Recall 都为 1.0000。
- CWE-330 和 CWE-614 已达到 Precision / Recall / F1 全部 1.0000。
- CWE-501 Precision Patch 1 将 outside-scope findings 从 493 降到 0，同时保持 FN = 0。
- CWE-328 当前唯一 FP 来自 `328S` 安全样本与 benchmark 标注边界；尝试移除 `SHA512` 会导致 39 个 FN，因此不作为安全优化。

## 污点型漏洞检查器

| CWE | 类别 | Findings | TP | FP | FN | Precision | Recall | F1 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| CWE-022 | 路径遍历 | 241 | 133 | 108 | 0 | 0.5519 | 1.0000 | 0.7112 |
| CWE-078 | 命令注入 | 223 | 126 | 97 | 0 | 0.5650 | 1.0000 | 0.7221 |
| CWE-079 | XSS | 342 | 246 | 96 | 0 | 0.7193 | 1.0000 | 0.8367 |

## 注入类检查器

| CWE | 类别 | Findings | TP | FP | FN | Precision | Recall | F1 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| CWE-089 | SQL 注入 | 422 | 272 | 150 | 0 | 0.6445 | 1.0000 | 0.7839 |
| CWE-090 | LDAP 注入 | 49 | 27 | 22 | 0 | 0.5510 | 1.0000 | 0.7105 |
| CWE-643 | XPath 注入 | 33 | 15 | 18 | 0 | 0.4545 | 1.0000 | 0.6250 |

## API 误用 / 密码学检查器

| CWE | 类别 | Findings | TP | FP | FN | Precision | Recall | F1 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| CWE-327 | 危险或不安全加密算法 | 157 | 130 | 27 | 0 | 0.8280 | 1.0000 | 0.9059 |
| CWE-328 | 弱哈希算法 | 129 | 128 | 1 | 0 | 0.9922 | 1.0000 | 0.9961 |
| CWE-330 | 随机数不足 | 218 | 218 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 |

## Web 配置 / 对象状态检查器

| CWE | 类别 | Findings | TP | FP | FN | Precision | Recall | F1 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| CWE-614 | 敏感 Cookie 缺少 Secure 标志 | 36 | 36 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 |
| CWE-501 | 信任边界违规 | 117 | 83 | 34 | 0 | 0.7094 | 1.0000 | 0.8300 |

## 备注

- CWE-501 Patch 1 新增了局部 scope filter，用于过滤 remember-me cookie session cache 写入。Patch 前 outside-scope findings 为 493，Patch 后为 0。
- CWE-328 的 1 个 FP 是 outside-scope finding，来自 `BenchmarkTest00003` 的 `328S` 标注；它与 39 个真阳性共享 `hashAlg1` / `SHA512` 模式，不能用通用规则安全区分。
- 精度优化应优先保持在 CWE-specific sink/sanitizer 模块内；任何公共 `TaintTracking.gdl` 修改都必须对所有已完成 checker 做回归。
