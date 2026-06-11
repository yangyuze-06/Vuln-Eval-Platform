# CWE-330 Godel Checker Analysis

## 1. Metrics Summary

指标来自 `experiments/cwe-330/eval/codefuse_eval/metrics.json`。

| Metric | Value |
|---|--:|
| Raw alerts | 218 |
| Dedup alerts | 218 |
| TP | 218 |
| FP | 0 |
| FN | 0 |
| Precision | 1.0000 |
| Recall | 1.0000 |
| FNR | 0.0000 |
| FPR | 0.0000 |
| FDR | 0.0000 |
| F1 | 1.0000 |
| Outside-scope FP | 0 |

## 2. Checker Type

- [x] API-misuse (直接匹配不安全的随机数 API)

## 3. Source / Sink / Sanitizer Summary

### Sources
不适用（API-misuse 类型）。

### Sinks
不安全的随机数生成器调用，包括：
- `java.util.Random` 构造和使用
- `Math.random()` 调用
- 其他 `WeakRandomSinks.gdl` 中定义的非密码学安全的随机数 API

### Sanitizers / Barriers
无需 taint sanitizer；通过 API 匹配直接判定。

## 4. FP / FN Analysis

- **Precision = 1.0, Recall = 1.0**: 完美指标。
- 当前 checker 在该 Benchmark 上达到了工程最优。所有使用不安全随机数 API 的 test case 均被正确检测，无 FP、无 FN。

## 5. Known Limitations

- 弱随机数检测规则较为直接（`java.util.Random` / `Math.random()` 使用即告警），在 Benchmark 上的简单代码模式覆盖完美
- 真实项目中可能存在：
  - 通过工厂/反射间接创建 `Random` 实例
  - 自定义 `Random` 子类
  - 第三方库封装的随机数 API
- 未检测 `ThreadLocalRandom`（非密码学安全但比 `Random` 略好）的使用场景

## 6. Next Steps

- 当前 Benchmark 版本可作为 baseline，无需修改
- 在真实项目验证中补充反射/工厂/第三方库的检测覆盖
- 考虑增加 `SecureRandom` 使用的 positive encouragement（鼓励迁移到安全 API）
