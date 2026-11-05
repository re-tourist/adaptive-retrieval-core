# 复现 V0 正式实验

在仓库根目录执行。本流程按 M0 数据准入、M1 全库基线、M2 固定候选集重排和 M3 在线一致性验证推进。
只想运行 CPU Demo 时，参见 [Quickstart](QUICKSTART.md)。

协议、正式数值与历史运行环境见 [V0 验收报告](ARC-V0-ACCEPTANCE.md)。请按官方来源获取数据与固定模型，保留原始字节。数据、模型与运行产物保存在本地。参数选择使用 dev，test 用于最终报告。

## M0 数据审计与指标校验

1. 从 [BEIR 官方目录](https://github.com/beir-cellar/beir/wiki/Datasets-available) 下载 SciFact ZIP，核对发布方 MD5 `5f7d1de60b170fc8027bb7898e2efca1`，解压到 `data/official/scifact`。
2. 从 [Wayfair/WANDS](https://github.com/wayfair/WANDS/tree/3b74dcf4ba29ab8ff3e6a50b5b09fc627cb882b5/dataset) 获取固定提交的三个 TSV 文件，保留原始字节并置于 `data/official/wands-raw`。
3. 运行以下命令。审计校验原件指纹，写出拆分、数据清单和失败明细。按 [ADR-003](adr/ADR-003-wands-disputed-labels.md) 排除已批准的 DISPUTED 对。若发现新冲突、清单失配或孤立引用，审计以退出码 1 拒绝正式评分。合成算例用于检验指标公式。

```sh
uv python install 3.12
uv sync --locked
uv run --no-sync python -m arc.evaluation.audit --scifact data/official/scifact --wands data/official/wands-raw --output artifacts/m0/admission
uv run --no-sync python -m arc.evaluation.smoke --output artifacts/m0/smoke
```

## M1 全库检索

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

## M2 固定候选集重排

M1 验收后，从同一数据集的 E1/E2 已冻结 Runfile 生成 E3/E4。下载 [固定 MiniLM-L6-v2 快照](https://huggingface.co/cross-encoder/ms-marco-MiniLM-L6-v2/tree/233902d25c440f23af6f7d6e94d2946bac0bee0a) 到 `models/ms-marco-MiniLM-L6-v2/233902d25c440f23af6f7d6e94d2946bac0bee0a`。适配器校验权重与 tokenizer 文件。示例先运行 10 条 dev 查询，再运行全部 SciFact test 查询。

```sh
uv run --no-sync python -m arc.evaluation.hybrid --dataset scifact --data data/official/scifact --admission artifacts/m0/admission --e1 artifacts/m1/run/scifact/e1 --e2 artifacts/m1/run/scifact/e2 --model models/ms-marco-MiniLM-L6-v2/233902d25c440f23af6f7d6e94d2946bac0bee0a --output artifacts/m2/run --device cuda:0 --batch-size 32 --dev-smoke 10 --split both
```

WANDS 使用自己的数据目录与 E1/E2 快照。E3 固定使用 RRF k=60，E4 仅重排 E3 前 50 项并保留原尾部。E4 Runfile 中的分数按名次编码，以保持标准 TREC 排序语义。MiniLM logits 只用于决定前 50 项的顺序。用 M1 的 `arc.evaluation.comparison` 追加两份 E3/E4 test Runfile 即可生成四策略配对 Bootstrap 和 WANDS 争议标签敏感性分析。

## M3 在线一致性

按 [Quickstart 的正式语料配置](QUICKSTART.md#load-scifact-or-wands) 启动服务。运行 `uv run --no-sync python scripts/measure-harness.py --help` 查看测量参数。脚本使用固定 dev 查询、冻结的 Runfile 和真实 HTTP 请求，核对在线排名与硬过滤。正式测量样本和运行环境见 [M3 阶段报告](../artifacts/acceptance/m3/report.md)。
