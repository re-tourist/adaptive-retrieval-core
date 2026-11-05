# ARC V0 验收报告

2026-11-05 · 分支 `codex/v0-development` · 已验收实现 `f99c33161aaf5bcbcf3f70ea389e8e1ea72d7f26`

## 阶段验收

| 阶段 | 状态 | 实际验证 | 证据 |
|---|---|---|---|
| D0 | PASS | Python 3.12 安装与构建、11 项测试、Windows/Ubuntu CI | [报告](../artifacts/acceptance/d0/report.md) |
| M0 | PASS | 官方数据规模、ID、Qrels 和拆分双次审计，18 项测试 | [报告](../artifacts/acceptance/m0/report.md) |
| M1 | PASS | E1、E2 两套全库正式检索及锁定重放 | [报告](../artifacts/acceptance/m1/report.md) |
| M2 | PASS | E3/E4 全部正式查询，固定池、尾部和逐查询 Recall 独立校验 | [报告](../artifacts/acceptance/m2/report.md) |
| M3 | PASS | 独立环境 wheel、CLI、四策略 HTTP 对照、Trace、实测 Docker | [报告](../artifacts/acceptance/m3/report.md) |

## 正式质量结果

| 数据集 | 策略 | 查询数 | NDCG@10 | Recall@100 | Judged@10 |
|---|---|---:|---:|---:|---:|
| SciFact | E1 BM25 | 300 | 0.641400 | 0.869222 | — |
| SciFact | E2 BGE + FAISS | 300 | 0.712707 | 0.941667 | — |
| SciFact | E3 RRF | 300 | 0.689995 | 0.965000 | — |
| SciFact | E4 MiniLM | 300 | 0.700141 | 0.965000 | — |
| WANDS | E1 BM25 | 400 | 0.648530 | 0.343283 | 0.789500 |
| WANDS | E2 BGE + FAISS | 400 | 0.705657 | 0.360762 | 0.835500 |
| WANDS | E3 RRF | 400 | 0.726482 | 0.373135 | 0.870000 |
| WANDS | E4 MiniLM | 400 | 0.744195 | 0.373135 | 0.876250 |

SciFact 全库 5,183 条，使用 809 dev 和 300 test。WANDS 全库 42,994 件，使用 ARC 自定义 80/400 拆分，表中 Recall 是已观测 Recall。根据 [ADR-003](adr/ADR-003-wands-disputed-labels.md)，14 个冲突对单列为 DISPUTED，不进入主 Qrels，也不视为真实负例。

- **SciFact**：E2 的 NDCG@10 最高。E4−E3 为 +0.010146，95% 配对区间 [−0.020469, +0.042317]。E4−E2 为 −0.012566，区间 [−0.041061, +0.015461]。本轮数据不足以证明 SciFact 的重排增益。
- **WANDS**：E4−E3 为 +0.017713，95% 区间 [+0.005398, +0.030895]。对 13 个 test 争议对采用所有已观测端点组合，E4−E3 的差值区间为 [+0.017554, +0.017664]。E4−E2 为 +0.038538，95% 区间 [+0.024001, +0.053159]。
- E3 与 E4 的 700 条正式测试查询均保持相同 Top-100 集合和相同尾部。固定池约束限制了 E4 对上游召回失败的修复能力。最差查询和全部六组配对结果见 [M2 机器证据](../artifacts/acceptance/m2/checks.json)。

## 性能与成本

| 数据集 | 策略 | HTTP 请求数 | p50（ms） | p95（ms） |
|---|---|---:|---:|---:|
| scifact | E1 | 30 | 25.90 | 35.73 |
| scifact | E2 | 30 | 29.14 | 47.05 |
| scifact | E3 | 30 | 42.52 | 65.21 |
| scifact | E4 | 30 | 291.94 | 338.70 |
| wands | E1 | 30 | 48.55 | 76.89 |
| wands | E2 | 30 | 30.61 | 41.29 |
| wands | E3 | 30 | 57.08 | 68.89 |
| wands | E4 | 30 | 373.17 | 416.11 |

本机 Windows 11，RTX 4060 Laptop 8,188 MiB，驱动 566.24，PyTorch 2.8.0+cu126。BM25 和 FAISS 在 CPU 上运行，BGE 与 MiniLM 使用 CUDA、float32、批次 32。在线测量为本机环回 HTTP，单进程串行、每策略两次预热、10 条固定 dev 查询各重复三次。建索引成本另计。E2 索引构建与保存分别耗时 101.00 s（SciFact）和 663.69 s（WANDS），FAISS 文件分别为 7,961,133 与 66,038,829 字节。E4 的主要额外时延来自 MiniLM，WANDS 正式 test 有 12,117 / 20,000 个配对文本发生截断。详见 [M1 机器证据](../artifacts/acceptance/m1/checks.json) 和 [M3 机器证据](../artifacts/acceptance/m3/checks.json)。

## 复现与边界

1. 按 [README](../README.md) 安装锁定环境并从官方来源获取数据和固定权重。运行 M0 审计生成本地准入清单。
2. 依次执行 M1 E1/E2、M2 E3/E4 与四策略配对比较。每个报告保存数据、模型、索引、Runfile 和逐查询结果的指纹，原始数据、模型和大体积运行产物保留在本地。
3. 通过 README 中的 `arc search`、`arc serve` 和容器命令复现。用 `scripts/measure-harness.py` 对两个正式快照核对在线排名与 Trace。
4. [GitHub Actions](https://github.com/re-tourist/adaptive-retrieval-core/actions/runs/42035615364) 对实现提交实际通过 Windows、Ubuntu 和 Docker。CPU Docker 演示与本机全策略 CUDA 服务分别验收。

目标服务器性能为 **BLOCKED**。当前没有可访问的指定服务器，实测数字限于本机和 CI 容器。V0 采用公开语料与单进程服务，尚无生产 ACL、多租户隔离和并发容量证据。后续可在目标硬件补齐并发与资源画像，再依据业务时延预算选择是否开启重排。WANDS 的不完整标注限制了对真实全召回的解释。

## Git 记录

- D0 `ccb402f`，M0 `7845e78`，M1 索引与重放 `141d634`，M2 `4419393`，M3 `b61a801`，最终实现验证 `f99c331`。
- [Pre-Goal PR #1](https://github.com/re-tourist/adaptive-retrieval-core/pull/1) 仍为 Draft。平台此前拒绝 Ready/合并，开发按批准的备选路径从审核后的提交继续。交付分支为 `codex/v0-development`。
