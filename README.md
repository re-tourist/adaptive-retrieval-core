# Adaptive Retrieval Core (ARC)

**Benchmark-driven, modular information retrieval core for enterprise AI harnesses.**

**V0.1.0 · D0–M3 已验收。** ARC 提供 BM25、BGE + FAISS、RRF 和 MiniLM 重排，以及 Python、CLI、FastAPI、Trace 和 CPU Docker 演示。详见 [V0 总验收报告](docs/ARC-V0-ACCEPTANCE.md) 和 [进度台账](PROGRESS.md)。

| 正式测试 NDCG@10 | E1 BM25 | E2 Dense | E3 RRF | E4 MiniLM |
|---|---:|---:|---:|---:|
| SciFact（300 条） | 0.641400 | 0.712707 | 0.689995 | 0.700141 |
| WANDS（自定义 400 条） | 0.648530 | 0.705657 | 0.726482 | 0.744195 |

正式实验在 Windows 11 / RTX 4060 Laptop 上完成。WANDS 标注不完整，指标基于现有 Qrels；目标服务器性能尚未验收。Windows、Ubuntu 和 CPU Docker 的工程验收见 [GitHub Actions](https://github.com/re-tourist/adaptive-retrieval-core/actions/runs/42035615364)。

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

历史执行计划见 [PLAN.md](PLAN.md)，协作规范见 [Git 工作流](docs/engineering/GIT_WORKFLOW.md)。

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

### M1 全库检索

审计通过后，用已校验的原始数据目录和 `artifacts/m0/admission` 运行。默认 uv 检索依赖组使用 CUDA 12.6 的 PyTorch，需要先验证本机驱动和 `torch.cuda.is_available()`。

```sh
uv sync --locked --group sparse --group dense
uv run --no-sync python -m arc.evaluation.baselines --dataset scifact --method e1 --data data/official/scifact --admission artifacts/m0/admission --output artifacts/m1/run --split both
uv run --no-sync python -m arc.evaluation.baselines --dataset scifact --method e2 --data data/official/scifact --admission artifacts/m0/admission --output artifacts/m1/run --model models/bge-small-en-v1.5/5c38ec7c405ec4b44b94cc5a9bb96e735b38267a --device cuda:0 --batch-size 32 --split both
```

WANDS 使用 `--dataset wands --data data/official/wands-raw`。输出根目录下的每个数据集和策略目录须是新目录。E2 使用 [BAAI 官方 BGE 快照](https://huggingface.co/BAAI/bge-small-en-v1.5/tree/5c38ec7c405ec4b44b94cc5a9bb96e735b38267a)，模型文件名和 SHA-256 由适配器校验。使用 CPU PyTorch 的独立环境时，将 `--device` 设为 `cpu` 并记录实际依赖。CPU 结果的时延只代表所测机器。

按数据集比较已固定的两份 test Runfile。以下例子同时生成 WANDS 的配对 Bootstrap 和 ADR-003 敏感性分析。

```sh
uv run --no-sync python -m arc.evaluation.comparison --dataset wands --admission artifacts/m0/admission --entity-ids artifacts/m1/run/wands/e1/entity_ids.json --run artifacts/m1/run/wands/e1/test/run.trec --run artifacts/m1/run/wands/e2/test/run.trec --output artifacts/m1/run/wands/comparison.json
```

### M2 固定候选集重排

M1 验收后，从同一数据集的 E1/E2 已冻结 Runfile 生成 E3/E4。下载 [固定 MiniLM-L6-v2 快照](https://huggingface.co/cross-encoder/ms-marco-MiniLM-L6-v2/tree/233902d25c440f23af6f7d6e94d2946bac0bee0a) 到 `models/ms-marco-MiniLM-L6-v2/233902d25c440f23af6f7d6e94d2946bac0bee0a`。适配器校验权重与 tokenizer 文件。示例先运行 10 条 dev 查询，再运行全部 SciFact test 查询。

```sh
uv run --no-sync python -m arc.evaluation.hybrid --dataset scifact --data data/official/scifact --admission artifacts/m0/admission --e1 artifacts/m1/run/scifact/e1 --e2 artifacts/m1/run/scifact/e2 --model models/ms-marco-MiniLM-L6-v2/233902d25c440f23af6f7d6e94d2946bac0bee0a --output artifacts/m2/run --device cuda:0 --batch-size 32 --dev-smoke 10 --split both
```

WANDS 使用自己的数据目录与 E1/E2 快照。E3 固定使用 RRF k=60，E4 仅重排 E3 前 50 项并保留原尾部。E4 Runfile 中的分数按名次编码，以保持标准 TREC 排序语义。MiniLM logits 只用于决定前 50 项的顺序。用 M1 的 `arc.evaluation.comparison` 追加两份 E3/E4 test Runfile 即可生成四策略配对 Bootstrap 和 WANDS 争议标签敏感性分析。

### M3 检索服务与演示

```sh
uv sync --locked --group sparse --group harness --group harness-test
uv run --no-sync arc search "BM25" --top-k 1 --trace
uv run --no-sync arc serve --host 127.0.0.1 --port 8000
```

默认使用三个内置演示实体和真实 BM25。浏览 `/docs` 可试用 OpenAPI，`GET /healthz` 返回可用策略与快照。向 `POST /search` 发送 JSON，例如：

```json
{"query":"BM25","domain":"technical","strategy_id":"bm25","top_k":1,"return_level":"unit","trace_level":"summary"}
```

`filters.entity_ids` 是硬过滤白名单，在确定候选时生效。空白名单返回空结果，未知过滤字段返回 422。可通过 `snapshot_id` 锁定快照，失配返回 409。请求只接受 `technical` / `product`，并在配置域内检索。默认返回实体级结果，`return_level: "unit"` 附加 Unit ID 和位置。Trace 摘要给出阶段时延和候选数，不包含查询正文、标签或内部 logits。E4 的公开分数为排名编码。

加载正式语料时，设置以下环境变量后运行同一命令：

| 变量 | 作用 |
|---|---|
| `ARC_DATASET` | `scifact` 或 `wands`。省略时为 `demo`。 |
| `ARC_DATA` | 对应官方数据目录。在线只读取 corpus JSONL 或 product TSV。 |
| `ARC_BGE_MODEL` | 已校验 BGE 快照路径。与 Dense 索引同时设置后启用 Dense、Hybrid。 |
| `ARC_DENSE_INDEX` | M1 产生的 E2 目录，含 `index.faiss`、`index_manifest.json` 和 `entity_ids.json`。只加载可信的本地快照。 |
| `ARC_MINILM_MODEL` | 固定版本的 MiniLM 快照路径。与 Dense 一起配置后启用 Hybrid Rerank。 |
| `ARC_DEVICE` | `cpu` 或 `cuda:0`。用 Dense 或 MiniLM 时安装 `--group dense` 并确认运行时。 |

服务串行执行同一进程内的检索请求。只使用公开或获授权的语料，按本地评测和演示部署，无生产 ACL 和多租户隔离。性能脚本 `scripts/measure-harness.py --help` 使用固定 dev 查询、已冻结的 Runfile 和真实 HTTP 请求验证在线排名与硬过滤。

Docker 演示镜像只包含 CPU BM25、Web 入口和内置演示语料：

```sh
docker build --tag arc:v0 .
docker run --rm -p 127.0.0.1:8000:8000 arc:v0
python scripts/container-smoke.py http://127.0.0.1:8000
```

数据、索引、模型、缓存和凭据都排除在镜像构建上下文之外。
