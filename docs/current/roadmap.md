# 路线图

## 当前状态：V3.0.0

M1～M5 均已完成：11 个 Java checker、共享规则架构、统一 pipeline、v2 评估与报告、golden regression 和 CI 已形成稳定发布基线。

已支持：CWE-022、078、079、089、090、327、328、330、501、614、643。

## V3.x：规则精度研究

Recall 已达到 1.0000，后续重点是降低 FP，同时保持 FN=0：

1. 按 FP 数量和人工审计成本处理 CWE-089、022、078、090、643。
2. 优先修改 CWE-specific sink、sanitizer、barrier 和 scope filter。
3. 每个 patch 保存 TP/FP/FN/P/R/F1 delta，并运行 11 CWE 全量回归。
4. benchmark-only suppression 必须显式标记，不与 upstream-ready 规则混合。

## 中期扩展

- CWE-601 Open Redirect。
- CWE-094 Code Injection。
- CWE-502 Deserialization。
- Spring MVC source 建模。
- 标准化 taint-based 与 API-misuse checker 模板。

## 长期研究

- 局部 strong update。
- collection/key sensitivity。
- path-sensitive branch reasoning。
- field/context-sensitive taint。
- helper return precision。
- 可解释 taint path。

共享 `TaintTracking.gdl` 属高风险边界。任何修改都必须通过 pytest、golden fixtures、CodeFuse 全量回归及 CodeQL 对照。

## 稳定性约束

- 机器可读 schema 保持向后兼容。
- 旧 wrapper 至少保留一个 V3 兼容周期。
- 新工具通过 adapter 接入，不在 pipeline 中写工具专属分支。
- 当前发布基线见 `reports/data/metrics_v2_*_all.json`。
