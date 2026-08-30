# 评测结果

以下是当前 CodeFuse-Query 规则在 OWASP Benchmark 上的结果。`Findings` 表示 evaluator 去重后的 finding 数量。

数据来源：`reports/data/metrics_v2_codefuse_all.json`（2026-08-31 mac-fixed DB 全量回归，v2 评估口径，
见 `docs/audits/PARITY_M34_CODEFUSE_PIPELINE.md`）。

## 总览

- 已完成 checker：11 个。
- 所有已完成 checker 当前在 benchmark 上 Recall 都为 1.0000，FN = 0。
- CWE-330、CWE-614、CWE-328 已达到 Precision / Recall / F1 全部 1.0000。
- Overall：TP=1415，FP=552，FN=0，TN=773，Precision=0.7194，Recall=1.0000，F1=0.8368。
- CWE-501 Precision Patch 1 将 outside-scope findings 从 493 降到 0，同时保持 FN = 0。
- CWE-328 的历史"1 个 FP"（`328S` 样本）在 v2 评估口径下确认为 TP：ground truth 官方标注
  `BenchmarkTest00003,hash,true,328S` 为漏洞样本，旧 evaluator 将 `328S` 排除出 CWE-328 scope 属于口径偏差。

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
| CWE-328 | 弱哈希算法 | 129 | 129 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 |
| CWE-330 | 随机数不足 | 218 | 218 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 |

## Web 配置 / 对象状态检查器

| CWE | 类别 | Findings | TP | FP | FN | Precision | Recall | F1 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| CWE-614 | 敏感 Cookie 缺少 Secure 标志 | 36 | 36 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 |
| CWE-501 | 信任边界违规 | 117 | 83 | 34 | 0 | 0.7094 | 1.0000 | 0.8300 |

## 备注

- CWE-501 Patch 1 新增了局部 scope filter，用于过滤 remember-me cookie session cache 写入。Patch 前 outside-scope findings 为 493，Patch 后为 0。
- CWE-328：ground truth 中唯一 `328S` 行（`BenchmarkTest00003`）被 v2 evaluator 归一化计入 CWE-328。旧口径（`eval_codefuse_results.py`）将其排除在 scope 外并计为 FP；本轮全量回归中 `TaintTracking.gdl` 与规则未做任何修改，findings 逐字节一致（见 parity 审计）。历史上"移除 `SHA512` 会引入 39 个 FN"的结论仍有效。
- 精度优化应优先保持在 CWE-specific sink/sanitizer 模块内；任何公共 `TaintTracking.gdl` 修改都必须对所有已完成 checker 做回归。
