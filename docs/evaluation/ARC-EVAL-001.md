# ARC-EVAL-001 · V0 Benchmark 选型基线

**项目：** Adaptive Retrieval Core（ARC）  
**文档类型：** Benchmark Selection Decision / Evaluation ADR（评测选型决策记录）  
**版本与状态：** v0.1 · FROZEN（选型冻结，实验数值尚未产生）  
**日期：** 2026-11-05  
**关联：** RFC-001 v0.1《需求与架构基线》  
**权威版本：** 本 Markdown 文档；DOCX 为阅读副本

> **决定：V0 只引入两套公开主 Benchmark：BEIR / SciFact（学术文本全库检索）和 Wayfair / WANDS（商品全库检索）。** 首轮目标是利用真实、可复现、相对轻量的数据尽快跑通基线，再逐步完成 Hybrid 与 Reranker 的消融比较。现阶段不使用 Amazon ESCI 作为主评测。

## 1. 为什么要冻结两个 Benchmark

ARC 的目标不是凭一套大数据刷榜，而是证明两个能力：**检索质量可测量**，以及**同一 Retrieval Core 能在不同业务下复用**。V0 优先保证公开来源可信、任务清晰、标签可用、数据规模可控、无需从头训练且能在单机环境取得首轮结果。

决定权重按如下次序考虑：

1. **任务正确性与可信性：** 官方/原发布方数据，有明确查询、候选对象和相关性标注。
2. **成本与速度：** 小型或中型公开语料，优先支持直接运行 BM25 和预训练 Dense 的首次对照。
3. **求职辨识度：** 学术界或工业界熟悉、能说明为何选择、可提供公开引用。
4. **业务差异：** 一套学术文本检索、一套商品内容搜索，验证通用内核而非重复相似任务。

**不追求** V0 覆盖全部文本领域、千万商品规模或多模态检索。

## 2. 两个正式数据集

| 维度 | Benchmark A：BEIR / SciFact | Benchmark B：Wayfair / WANDS |
|---|---|---|
| 来源与认可度 | BEIR 检索评测体系中的公开子集；SciFact 源于科学事实核验研究 | Wayfair 发布；配套 ECIR 2022 论文和人工标注说明 |
| 任务 | **全库文档检索**：科学论断 → 相关论文摘要 | **全库商品检索**：用户查询 → 商品列表 |
| 语料 | **5,183** 篇文档 | **42,994** 个商品 |
| 查询 | **300** 条标准测试查询 | **480** 条查询，无官方固定训练/测试分割 |
| 标注 | BEIR 标准 Qrels（文档级） | **233,448** 条 Query–Product 人工相关性标注 |
| 相关性 | 文档与科学论断是否相关 | Exact / Partial / Irrelevant（三级） |
| 首要指标 | **NDCG@10** | **NDCG@10** |
| 辅助指标 | Recall@100、MRR@10、P95 延迟 | Judged Recall@100（须注明标签不完全）、MRR@10、P95 延迟 |
| 数据接口 | corpus / queries / qrels | product.csv / query.csv / label.csv |
| 开发优先级 | **第一优先**：快速打通基线 | **第二优先**：验证业务迁移 |

官方来源：
- BEIR 数据集目录与 SciFact 下载指引：https://github.com/beir-cellar/beir/wiki/Datasets-available
- SciFact 原论文与源数据：https://github.com/allenai/scifact
- WANDS 原始仓库：https://github.com/wayfair/WANDS
- Wayfair 的数据集背景与标注说明：https://www.aboutwayfair.com/careers/tech-blog/wayfair-releases-wands-the-largest-and-richest-publicly-available-dataset-for-e-commerce-product-search-relevance

**适用性边界：** SciFact 是科学论断—论文摘要检索，不能直接证明 API/代码版本搜索能力；WANDS 是家具等商品文本检索，不能直接证明商品个性化推荐或多模态能力。两项都以**英语**为主要语言，不据此声称中文检索质量。

## 3. 为什么 WANDS 替代先前讨论的 Amazon ESCI

上一轮讨论拟采用 Amazon ESCI Task 1 作为商品 Benchmark；重新审查快速落地约束后，本决策将其移出 V0。

| 比较 | Amazon ESCI Task 1 | Wayfair WANDS |
|---|---|---|
| 主要任务 | 给定候选商品的 **Reranking** | 既有商品全集，又有 Query–Product 标签，可建立 **Full-corpus Retrieval** 流程 |
| 原生数据规模 | 多语言，小版本 **48,300** 查询、**1,118,011** 条标注；US 部分也较大 | **480** 查询、**42,994** 商品、**233,448** 条标注 |
| 获取成本 | 原仓库的商品元数据 Parquet 文件约 **1.03 GB** | 三份 CSV，语料和查询规模更可控 |
| ARC V0 适配性 | 适合日后验证商品候选重排 | 更适合当前统一内核的 **端到端召回 + 排序** 验证 |
| 决定 | **暂缓至 V1 / 选修** | **V0 冻结采用** |

> **重要：这是一项对 RFC-001 v0.1 的有记录的变更。** 原 RFC 将商品验证定义为「ESCI 给定候选重排」；本 ADR 将 V0 商品主测改为「WANDS 商品全库检索」，并保留同一个算法与 Harness 双目标。原 RFC-001 v0.1 文件不作静默覆盖；后续统一文档时应发布 RFC-001 v0.2，将该变更合并。除商品 Benchmark 与对应评价协议外，其余 RFC 原则不变。

此变化也带来一个更强的论证：两个不同业务均通过统一的全库检索接口运行，但各自有不同数据字段和相关性等级。

## 4. 快速跑通与最终报告分层

### 4.1 Smoke（仅验证运行正确性）

- SciFact：完整 5,183 篇文档，选 10–20 条查询；检查 IDs、Qrels、输出、指标公式。
- WANDS：先加载全体商品元数据，抽取 10–20 条查询；如有必要可用小型商品子集调试，但**商品子集成绩不得用于简历或官方对比**。
- 最先完成 **BM25 baseline**，其次执行预训练 Dense baseline；无需在第一轮引入 Reranker、微调或 Agent。

### 4.2 Canonical V0（正式可比较结果）

- **SciFact：** 使用 BEIR 的**完整 test 查询集合（300 条）与完整 5,183 篇语料**；可使用其 train 划分做开发/校准，不用 test 选择参数。
- **WANDS：** 使用全部 **42,994 商品**；由于数据不提供统一官方训练/测试划分，预先根据稳定 `query_id` 哈希固定 **80 条 dev + 400 条 test**，以查询为分组单位划分，所有策略使用完全相同的拆分。固定的 Query ID 清单保存至仓库。
- **防泄漏：** test 用于最终验证；不得根据 test 上的指标反复选择策略或参数。如需改实验方案，记录为新版本，而非覆盖首轮结果。
- **报告标签：** WANDS 的 400 条测试查询结果必须标明 `ARC-WANDS-400 (custom query split)`；**不得称为 WANDS 官方排行榜成绩**，也不可无条件与外部论文数字直接比较。

固定拆分的种子/哈希算法、数据文件哈希和实际 ID 列表由数据适配器在首次构建后输出并纳入版本控制。`80/400` 是预先决定的协议，不依赖相关性标注筛选查询。

## 5. 初版指标与公平性规则

1. **主指标统一 NDCG@10，但分开报告两个数据集的数值；不跨数据集求平均分。**
2. SciFact 使用官方文档级 Qrels。V0 首次评测优先使用完整文档为检索单元；如拆分 Passage，必须聚合回文档再与 Qrels 比较。
3. WANDS 标签预注册 `Exact=2, Partial=1, Irrelevant=0`，按标准 NDCG 折扣公式计算，保存评价脚本版本。该映射是 **ARC 自定义且固定** 的本地协议，不宣称等价于所有外部 WANDS 论文的 gain 方案。
4. WANDS 标注不是对全部 `480 × 42,994` Query–Product 对的穷举判定；未标注商品**不能被逻辑上当成已验证的无关商品**。常见评测实现把未标注项按 0 计分时，应将结果说明为 **基于现有 Qrels 的分数**，同时保留已判定候选上的重排分析。
5. 对比至少覆盖：BM25、Dense、Hybrid/RRF、Hybrid + Cross-Encoder；中间候选预算、Top-K、索引快照、模型版本、硬件、批处理和延迟统计口径一致或明确披露差异。
6. 系统成本分开记录：**离线编码/索引构建** 与 **在线查询耗时**；对外优先报告 P50/P95，并记录运行环境。
7. 禁止「调完测试集后只汇报最优值」；报告应保留基线、所有主要消融及失败案例。

## 6. 首轮成功的最低验收标准

- 能从原始官方数据重建 Entity、Retrieval Unit、查询与 Qrels，数据量及 ID 映射通过校验。
- SciFact 全库 BM25 产生可复现 `NDCG@10`、`Recall@100` 和标准检索 Runfile。
- WANDS 在全体商品上完成 BM25 检索，并对固定测试查询产生 `NDCG@10` 和 Runfile；保存 `ARC-WANDS-400` 拆分清单。
- 相同的检索核心，通过不同 Adapter 完成上述两种任务，**不修改核心检索逻辑**。
- 成绩不达预期也允许完成 V0；必须能解释失败类型，不能以虚构提升或未运行结果替代真实实验。

## 7. 非目标与后续扩展

- **不纳入 V0 主 Benchmark：** Amazon ESCI、FiQA、NFCorpus、MTEB 综合排行榜、TREC、大规模商品图像检索。
- **暂不承诺：** 训练新模型、在公开榜单达到 SOTA、特定 QPS、实时业务指标或中文领域泛化。
- **V1 可选：** ESCI 候选重排、技术 API/代码专项测试，按现有错误归因决定。
- **V2 可选：** 商品图文检索及对应公开多模态 Benchmark，必须独立定义标注与评价协议。

## 8. 决策记录与引用

**结论：** V0 正式选定 `BEIR / SciFact` 与 `Wayfair / WANDS`，只保留两套主数据集。第一批运行优先获得 BM25 和 Dense 的真实基线，再比较融合与精排。文档状态 FROZEN；如需调整主数据集、任务级别或主评价指标，提交新版本 ADR。

**与 RFC-001 的关系：** 本 ADR 对 `商品主评测由 ESCI 候选重排改为 WANDS 全库检索` 作显式优先声明。RFC-001 v0.1 保持历史原件不变；后续同步为 RFC-001 v0.2。

**来源核查（2026-11-05）：**

1. BEIR 数据集列表与下载：https://github.com/beir-cellar/beir/wiki/Datasets-available
2. SciFact 原项目及许可证：https://github.com/allenai/scifact
3. WANDS 原项目与数据结构：https://github.com/wayfair/WANDS
4. Wayfair 数据集介绍：https://www.aboutwayfair.com/careers/tech-blog/wayfair-releases-wands-the-largest-and-richest-publicly-available-dataset-for-e-commerce-product-search-relevance
5. Amazon ESCI 原项目及 Task 1 定义：https://github.com/amazon-science/esci-data
6. 原仓库 ESCI 商品 Parquet 文件大小：https://github.com/amazon-science/esci-data/blob/main/shopping_queries_dataset/shopping_queries_dataset_products.parquet

**许可提醒：** WANDS 仓库提供 MIT LICENSE；SciFact 的原始 claims、摘要和代码可能适用不同许可条款（详见原项目 LICENSE）。正式向外分发数据或将其打包进仓库前，必须核对各数据部分的实际授权；建议仓库只提供下载脚本、来源链接及摘要哈希，不直接提交整份原始语料。
