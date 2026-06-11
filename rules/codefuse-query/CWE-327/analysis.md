# CWE-327 Godel Checker Analysis

## 1. Metrics Summary

指标来自 `experiments/cwe-327/eval/codefuse_eval/metrics.json`。

| Metric | Value |
|---|--:|
| Raw alerts | 157 |
| Dedup alerts | 157 |
| TP | 130 |
| FP | 27 |
| FN | 0 |
| Precision | 0.8280 |
| Recall | 1.0000 |
| FNR | 0.0000 |
| FPR | 0.2328 |
| FDR | 0.1720 |
| F1 | 0.9059 |
| Outside-scope FP | 0 |

## 2. Checker Type

- [x] API-misuse (直接匹配不安全的加密算法 API)

## 3. Source / Sink / Sanitizer Summary

### Sources
不适用（API-misuse 类型，不依赖 taint tracking）。

### Sinks
不安全的加密算法调用，包括：
- `Cipher.getInstance("DES")` / `Cipher.getInstance("RC2")` / `Cipher.getInstance("RC4")` 等弱加密
- `SSLContext.getInstance("SSL")` / `SSLContext.getInstance("TLSv1")` 等过时 TLS 版本
- 其他 `CryptoAlgorithmSinks.gdl` 中定义的危险加密算法

### Sanitizers / Barriers
无需 taint sanitizer；算法白名单由 `CryptoAlgorithmSinks.gdl` 中的 sink 定义直接控制。

## 4. FP / FN Analysis

- **Recall = 1.0, Precision = 0.828**: API-misuse checker 表现良好。
- **FP (27)**: 主要来自：
  - 字符串常量/变量传入加密 API 时无法区分（例如 `String algo = "AES"` 时安全，但 `Cipher.getInstance(algo)` 被匹配）
  - `Cipher.getInstance(algorithm)` 中 algorithm 参数来自配置文件/环境变量时无法静态判定
  - `MaybeBrokenCryptoAlgorithm` 类的启发式规则产生部分 FP

## 5. Known Limitations

- 对加密算法字符串的常量传播/常量折叠能力有限
- 无法区分 algorithm 参数来自安全配置还是用户输入
- `KeyGenerator`, `SecretKeyFactory`, `Mac` 等其他加密 API 覆盖有限
- 对算法字符串的变体（大小写、斜杠、provider 前缀）匹配可能不完备

## 6. Next Steps

- 对算法参数为字符串常量的情况增加 constant value 检查
- 扩展 `KeyGenerator.getInstance`, `SecretKeyFactory.getInstance` 等 API 的覆盖
- 考虑 `Cipher.getInstance(algorithm, provider)` 双参数重载
