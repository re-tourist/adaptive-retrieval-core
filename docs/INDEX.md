# ARC 文档总索引

下表列出五份基线文档，后续执行决策和入口见下文。冻结规范按原版本保留。

| 优先读序 | ID | 规范原件 | 文件形式 | 状态 | 用途 |
|---|---|---|---|---|---|
| 1 | RFC-001 | [需求与架构基线](rfc/RFC-001.md) | MD + DOCX | FROZEN | 目标、范围、基本概念 |
| 2 | ARC-EVAL-001 | [Benchmark 选型](evaluation/ARC-EVAL-001.md) | MD + DOCX | FROZEN | SciFact + WANDS |
| 3 | ARC-TECH-001 | [技术架构](architecture/ARC-TECH-001.md) | MD + DOCX | FROZEN | 模块、目录、依赖、扩展 |
| 4 | ARC-EXP-001 | [实验协议](evaluation/ARC-EXP-001.md) | MD | PROPOSED | E1–E4、指标和复现 |
| 5 | ARC-M0-001 | [M0 任务单](tasks/ARC-M0-001.md) | MD | READY / NOT RUN | 数据与评测器实现 |

### 权威性与文档差异

- **先读各文档状态**：FROZEN 是设计基线；PROPOSED 尚需审定；READY 只表示可讨论或开始执行，不代表已完成。
- RFC-001 最初写的是 Amazon ESCI 的候选商品精排；随后的正式决策 **ARC-EVAL-001 改为 Wayfair WANDS 商品全库检索**，以降低启动成本并统一任务类型。旧 RFC 原文保留，以后在 RFC v0.2 同步。
- RFC-001 曾倾向单一主搜索后端（OpenSearch 等候选）；随后 **ARC-TECH-001 倾向 V0 的 `bm25s + FAISS Flat Exact`**，这是当前实施方向；尚未进行后端验证，不代表生产级单引擎。
- ARC-EXP-001 原文保持 PROPOSED。[执行审定附录](evaluation/ARC-EXP-001-EXECUTION-DECISION.md) 有条件允许 D0/M0 启动。M1/M2 正式实验须通过 M0 数据审计与协议准入检查。

详见 [决策历史](DECISION_LOG.md)。

### 执行与协作

- [执行入口](../PLAN.md)、[执行总计划](plan/ARC-PLAN-001.md)、[进度台账](../PROGRESS.md)、[持续 Goal 提示词](../GOAL_PROMPT.md)。
- [仓库指令](../AGENTS.md)、[Git 工作流](engineering/GIT_WORKFLOW.md)、[ADR-002](adr/ADR-002-uv-and-lightweight-backends.md)。
- [执行包版本与校验](../PRE_GOAL_PACKAGE_MANIFEST.json)。

### 附属文件

- `readable/`：三份旧 DOCX 阅读副本（与五份 Markdown 正文的文件数不应混淆）。
- `../MANIFEST.json`：各文档文件原名、大小、SHA-256 与完整性核验记录。
- `_local/`：私人服务器笔记，不纳入 Git 仓库版本管理。
