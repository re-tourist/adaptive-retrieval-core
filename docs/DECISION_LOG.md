# ARC 设计决策历史（合并包附录）

> 本附录仅梳理现有原文与新决策的对应关系，**不修改**已冻结的 RFC 和技术文档。

## D-001 · Benchmark 由 ESCI 转为 WANDS

- 初期 RFC-001 v0.1：商品方向使用 Amazon ESCI Task 1 给定候选重排。
- 后续 ARC-EVAL-001 v0.1（FROZEN）：使用 **SciFact + WANDS**，两个方向均以全库检索作为 V0 主任务；理由是 WANDS 规模、完整商品语料和项目范围更合适。
- 影响：后续的 `ARC-EXP-001`、`ARC-M0-001`、`ARC-TECH-001` 均以 WANDS 为准。RFC 原件等待 v0.2 同步修订。

## D-002 · V0 检索实现由单一主后端倾向轻量双实现

- 初期 RFC-001：优先尝试一个成熟主后端（OpenSearch 为候选），未锁定实现。
- ARC-TECH-001 v0.1：V0 倾向 `bm25s + FAISS Flat Exact`，以更少依赖更快完成 BM25/Dense/Hybrid 质量评测；后续可提供搜索引擎 Adapter。
- 影响：与 RFC 的结构性原则（统一接口、可替换技术后端）不冲突，但与单后端实施偏好有差异。需在 RFC v0.2 记录。

## D-003 · 环境与开发顺序

- 已定技术方向：模块化单体、Python 3.12、`uv`、D0 前置、M0 CPU 优先、M1/M2 用 GPU 正式评测。
- ARC 使用独立项目环境。GPU、驱动与运行时在 M1 前检测，CUDA/PyTorch 及容器配置按实施环境确定。冻结 TECH 中的硬件描述保留为规划背景，实际配置以 [ADR-002](adr/ADR-002-uv-and-lightweight-backends.md) 和现场检测记录为准。

## D-004 · 实验状态

- `ARC-EXP-001` 原文保持 PROPOSED。[执行审定附录](evaluation/ARC-EXP-001-EXECUTION-DECISION.md) 有条件允许 D0/M0 启动。M1/M2 正式实验须满足 M0 数据审计和协议准入要求。E1–E4 尚无正式结果。
- `ARC-M0-001`：READY FOR IMPLEMENTATION；任务尚未执行。
- WANDS 标注重复、冲突、覆盖及指标适用性需 M0 实测审计，不能凭说明文档假定已检验。
