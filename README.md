# Adaptive Retrieval Core (ARC)

**Benchmark-driven, modular information retrieval core for enterprise AI harnesses.**

当前工程阶段和验收证据见 [PROGRESS.md](PROGRESS.md)。项目目标是用可插拔的 BM25、Dense、Hybrid 和 Rerank 管线，验证文本（BEIR/SciFact）与商品（Wayfair/WANDS）两个场景的质量、成本和系统可复用性，并为未来多模态检索预留可演进边界。

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

实验协议原文仍为 **PROPOSED**。[执行审定附录](docs/evaluation/ARC-EXP-001-EXECUTION-DECISION.md) 有条件允许 D0/M0 启动。M1/M2 正式实验须通过 M0 数据审计并满足协议准入要求。历史决策见 [决策日志](docs/DECISION_LOG.md)，RFC、TECH、EVAL 冻结原件按版本保留。

Pre-Goal 人工复核并明确授权后，从 [执行入口](PLAN.md) 启动 D0，按 [进度台账](PROGRESS.md) 恢复，遵循 [Git 工作流](docs/engineering/GIT_WORKFLOW.md)。

## 运行环境

ARC 采用独立的 Python 3.12 + uv 项目环境，D0/M0 优先使用 CPU。M1 前实测目标服务器环境，再确定 GPU 运行配置。环境边界见 [ADR-002](docs/adr/ADR-002-uv-and-lightweight-backends.md)。

原始文档和执行包的校验清单分别见 [MANIFEST.json](MANIFEST.json) 与 [PRE_GOAL_PACKAGE_MANIFEST.json](PRE_GOAL_PACKAGE_MANIFEST.json)。

### 本地 CPU 检查（Windows / Linux）

安装 uv 后，在仓库根目录执行。D0 只依赖 Python 3.12 和开发测试工具。

```sh
uv python install 3.12
uv sync --locked
uv run --no-sync python -c "import arc"
uv run --no-sync pytest
uv run --no-sync ruff check .
uv run --no-sync ruff format --check .
```

### M0 数据审计与指标校验

1. 从 [BEIR 官方目录](https://github.com/beir-cellar/beir/wiki/Datasets-available) 下载 SciFact ZIP，核对发布方 MD5 `5f7d1de60b170fc8027bb7898e2efca1`，解压到 `data/official/scifact`。
2. 从 [Wayfair/WANDS](https://github.com/wayfair/WANDS/tree/3b74dcf4ba29ab8ff3e6a50b5b09fc627cb882b5/dataset) 获取固定提交的三个 TSV 文件，保留原始字节并置于 `data/official/wands-raw`。
3. 运行以下命令。审计校验原件指纹，写出拆分、数据清单和失败明细。按 [ADR-003](docs/adr/ADR-003-wands-disputed-labels.md) 排除已批准的 DISPUTED 对。若发现新冲突、清单失配或孤立引用，审计以退出码 1 拒绝正式评分。合成算例用于检验指标公式。

```sh
uv run --no-sync python -m arc.evaluation.audit --scifact data/official/scifact --wands data/official/wands-raw --output artifacts/m0/audit
uv run --no-sync python -m arc.evaluation.smoke --output artifacts/m0/smoke
```
