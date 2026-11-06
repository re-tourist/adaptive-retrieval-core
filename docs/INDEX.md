# ARC 文档总索引

V0 的 D0–M3 已验收。以下入口覆盖使用、设计与证据。

- [Quickstart](QUICKSTART.md) · 启动 Playground、CLI、API 和 Docker。
- [商品 Demo](SHOWCASE.md) · 语料、素材来源和实跑画面。
- [工程设计](ENGINEERING.md) · 在线检索流程、策略、索引与分数语义。
- [V0 验收报告](ARC-V0-ACCEPTANCE.md) · 正式结果、时延测量与阶段证据。
- [复现实验](REPRODUCING.md) · 官方数据、固定模型和复现命令。

## 贡献与当前任务

- [GitHub Issues](https://github.com/re-tourist/adaptive-retrieval-core/issues) 跟踪当前工作，[Milestones](https://github.com/re-tourist/adaptive-retrieval-core/milestones) 聚合阶段。
- [Git 工作流](engineering/GIT_WORKFLOW.md) 说明贡献与验收流程，[仓库指令](../AGENTS.md) 定义 Codex 权限与人工审核边界。

## 技术规范与实验协议

下表保留文档原始状态。实际交付与实验状态以 V0 验收报告为准。

| 优先读序 | ID | 规范原件 | 文件形式 | 状态 | 用途 |
|---|---|---|---|---|---|
| 1 | RFC-001 | [需求与架构基线](rfc/RFC-001.md) | MD + DOCX | FROZEN | 目标、范围、基本概念 |
| 2 | ARC-EVAL-001 | [Benchmark 选型](evaluation/ARC-EVAL-001.md) | MD + DOCX | FROZEN | SciFact + WANDS |
| 3 | ARC-TECH-001 | [技术架构](architecture/ARC-TECH-001.md) | MD + DOCX | FROZEN | 模块、目录、依赖、扩展 |
| 4 | ARC-EXP-001 | [实验协议](evaluation/ARC-EXP-001.md) | MD | PROPOSED | E1–E4、指标和复现 |
| 5 | ARC-M0-001 | [M0 任务单](tasks/ARC-M0-001.md) | MD | 历史任务单，M0 已验收 | 数据与评测器实现 |

### 权威性与文档差异

- FROZEN 文档保留设计基线。原始 PROPOSED 协议与后续执行审定须结合阅读。
- RFC-001 最初写的是 Amazon ESCI 的候选商品精排；随后的正式决策 **ARC-EVAL-001 改为 Wayfair WANDS 商品全库检索**，以降低启动成本并统一任务类型。旧 RFC 原文保留，以后在 RFC v0.2 同步。
- RFC-001 最初考虑 OpenSearch 等单一搜索后端。V0 按 ARC-TECH-001 的方向实现并验收了 `bm25s + FAISS Flat Exact`。
- ARC-EXP-001 保留 PROPOSED 原文。[执行审定附录](evaluation/ARC-EXP-001-EXECUTION-DECISION.md) 记录了准入条件，[V0 验收报告](ARC-V0-ACCEPTANCE.md) 记录了实际执行结果。

详见 [决策历史](DECISION_LOG.md)。

## 历史规划与交付

- [V0 规划归档](../PLAN.md)、[原始执行计划](plan/ARC-PLAN-001.md)、[原始 Goal 提示词](../GOAL_PROMPT.md)。
- [交付证据台账](../PROGRESS.md)、[版本发布](https://github.com/re-tourist/adaptive-retrieval-core/releases)。
- [ADR-002 · 运行时与检索后端](adr/ADR-002-uv-and-lightweight-backends.md)、[ADR-003 · WANDS 争议标注](adr/ADR-003-wands-disputed-labels.md)。
- [历史 Pre-Goal 执行包校验清单](../PRE_GOAL_PACKAGE_MANIFEST.json)。

### 附属文件

- `readable/`：三份旧 DOCX 阅读副本（与五份 Markdown 正文的文件数不应混淆）。
- `../MANIFEST.json`：各文档文件原名、大小、SHA-256 与完整性核验记录。
- `_local/`：私人服务器笔记，不纳入 Git 仓库版本管理。
