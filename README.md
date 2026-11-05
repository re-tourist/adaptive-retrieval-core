# Adaptive Retrieval Core (ARC)

**Benchmark-driven, modular information retrieval core for enterprise AI harnesses.**

当前仓库处于 **文档基线 / D0 开始前**：尚无已验收代码、已运行的 Benchmark 成绩或生产服务。项目目标是用可插拔的 BM25、Dense、Hybrid 和 Rerank 管线，验证文本（BEIR/SciFact）与商品（Wayfair/WANDS）两个场景的质量、成本和系统可复用性，并为未来多模态检索预留可演进边界。

> **开始开发前请阅读**：[`docs/INDEX.md`](docs/INDEX.md)。请保留文档原有版本和状态，不要把 PROPOSED 文档擅自当成冻结规范。

## 当前文档（所有规范原件为 Markdown）

| 文档 | 路径 | 状态 |
|---|---|---|
| RFC-001 · 需求与架构基线 | [`docs/rfc/RFC-001.md`](docs/rfc/RFC-001.md) | FROZEN |
| ARC-EVAL-001 · Benchmark 选型 | [`docs/evaluation/ARC-EVAL-001.md`](docs/evaluation/ARC-EVAL-001.md) | FROZEN |
| ARC-EXP-001 · 实验协议 | [`docs/evaluation/ARC-EXP-001.md`](docs/evaluation/ARC-EXP-001.md) | PROPOSED |
| ARC-M0-001 · Codex 数据/评测任务 | [`docs/tasks/ARC-M0-001.md`](docs/tasks/ARC-M0-001.md) | READY / NOT RUN |
| ARC-TECH-001 · 技术架构 | [`docs/architecture/ARC-TECH-001.md`](docs/architecture/ARC-TECH-001.md) | FROZEN |

DOCX 阅读副本放在 `docs/readable/`；规范更改应首先在 Markdown 中完成并正式升级版本。

## 项目技术原则

- 模块化单体、轻量六边形架构、有限 DDD：Domain / Application / Ports / Adapters / Verticals / Evaluation。
- 源数据实体和检索单元分离；基准测试与在线检索隔离；Qrels 不进入检索执行路径。
- V0 优先准确、低成本、可复现；不要因扩展性过度设计。
- 不把人工相关性标签不完整的公开 Benchmark 当作真实全量相关性真值。

## 开发阶段

`D0（仓库与环境） → M0（数据与评测器） → M1（BM25/Dense） → M2（Hybrid/Rerank） → M3（API/Trace/Docker）`

正式开始 D0 前，先按 `docs/DECISION_LOG.md` 解决历史版本间的两处已记录变更，并将实验协议审定。

## 运行环境

开发目标：Python 3.12，`uv`，CPU-first D0/M0；GPU 计算延后至 M1/M2。服务器私有路径、代理和容器名字不应提交到公开仓库。

此 ZIP 包的版本与来源核验见 `MANIFEST.json`。
