# ARC-EXP-001 · V0 实验协议与基线实施规范

- **项目**：Adaptive Retrieval Core (ARC)
- **类型**：Experimental Protocol / Reproducibility Specification（实验协议与复现规范）
- **版本**：v0.1 · **PROPOSED（待审定，未冻结）**
- **日期**：2026-11-05
- **上游约束**：RFC-001 v0.1（架构冻结）；ARC-EVAL-001 v0.1（SciFact + WANDS 选型冻结）
- **状态说明**：尚未运行任何实验；本文数值均为配置预算或公开数据规模，不是实验结果。

## 1. 实验目标与有效性边界

V0 同时证明：（1）通用检索核心在学术文本与电商商品的全库检索上可复用；（2）BM25、Dense、Hybrid/RRF、Cross-Encoder 的质量、延迟和资源开销可公平比较；（3）完整数据与运行版本可追溯。

**公开报告边界：** 两套数据均是英语；SciFact 代表科学论断检索而非代码/API 搜索；WANDS 代表家具商品相关性而非用户个性化推荐。不得将 WANDS 不完整 qrels 推断为全体商品的真实完整相关性，也不得宣称该自定义拆分为官方排行榜成绩。

## 2. 数据与划分（冻结上游约束）

| 属性 | BEIR / SciFact | Wayfair / WANDS |
|---|---|---|
| 评测方式 | Full-corpus Retrieval，Document 级 | Full-corpus Retrieval，Product 级 |
| 全库规模 | 5,183 文档 | 42,994 商品 |
| 正式测试 | BEIR 官方 test 300 Query | 自定义固定 400 Query |
| 开发/配置检查 | 官方 train Query 与 Qrels；非 test | 80 Query；按 query_id 稳定哈希确定 |
| Qrels | 官方文件，二元相关 | Exact=2、Partial=1、Irrelevant=0 |
| 评价对象 ID | 原始 document_id | 原始 product_id |

WANDS 的 Query 划分规范：取得按 **原始 query_id 去重** 的 480 个查询；以固定文本 `ARC-WANDS-v0.1|{query_id}` 做 SHA-256，按十六进制摘要字典序排列（并以原始 query_id 作平局次序）；前 80 为 dev，剩余 400 为 test。输出 `dev_query_ids.json`、`test_query_ids.json` 和各自 SHA-256，放入 Git；不得按标注标签筛选或打乱本划分。

**重大前提：** 先下载原项目文件，记录 URL、Git commit/来源版本、SHA-256、License；核对 query/product/label 的真实行数、唯一键和孤立引用。重复 `(query_id, product_id)` 且标签一致的记录可归并并计数；**发生冲突标签时禁止静默选取一条**，产出冲突清单，先审核是否需单独的清洗决策，再运行正式实验。未获核实前，不对外声称 qrels 无重复/无冲突。

## 3. Query、文档字段及索引一致性

- SciFact：单一 **document-level** Entity/Unit，索引文本为 `title + '\n' + text`；`doc_id` 保持原始键。V0 不切 Passage，不在段落级评测文档 Qrels。
- WANDS：单一 **product-level** Entity/Unit；索引文本按固定顺序组合 `product_name`、`product_class`、`category_hierarchy`、`product_features`、`product_description`；空字段用空字符串，不创建虚假文本；保留字段名/分隔符以明确含义。`product_id` 保持原始键。`rating_count`、`average_rating`、`review_count` **不进入 V0 检索文本与排序特征**。
- WANDS 的 `query_class` 仅用于事后切片诊断（如启用），不得作为模型在线输入，以免把预先给出的类别当作系统推断能力。
- 对 BM25、Dense、Cross-Encoder，固定**同一份原始内容字段和 Entity ID**；允许不同算法不同表示和模型长度限制，但需明确截断/词元化策略。
- Embedding 基线：`BAAI/bge-small-en-v1.5`，短 Query 固定添加模型卡的英文检索 instruction；文档不添加；L2 归一化后用 `FAISS IndexFlatIP`，因此为精确余弦近邻排序。记录模型 revision、tokenizer、最大长度、精度、批次大小与截断比例。
- Cross-Encoder 基线：`cross-encoder/ms-marco-MiniLM-L6-v2`；记录模型 revision、最大 Token、Query/Document 拼接顺序、裁剪策略、推理精度与 batch size。特别记录 WANDS 商品长描述的截断率。
- BM25：固定实现、tokenizer（大小写、Unicode、标点、数字与连字符规则）、参数、语料统计与索引版本。不预设 BM25 与 Dense 得分可直接比较。

## 4. 四个正式策略（基线，不进行模型训练）

| ID | 策略 | 输出与控制变量 |
|---|---|---|
| E1 | BM25 | 全库稀疏搜索，Top-100 |
| E2 | Dense | 编码 Query，FAISS IndexFlatIP 精确搜索，Top-100 |
| E3 | Hybrid | BM25@100 + Dense@100，合并去重，RRF `k=60`，保留 Top-100 |
| E4 | Hybrid + Rerank | **复用 E3 的同一个 Top-100 候选集合**；Cross-Encoder 对 E3 的前 50 精排；保留这 50 个经重排结果，再附上原 E3 第 51–100 项；评测整个 Top-100 |

RRF：每一路候选按从 1 开始的 rank 计分；未出现在一路的文档没有该路贡献。输入每路最多 100 项；排序平局按稳定 ID 解决。记录总候选并集数、融合前后去重数。

**不可变性质：** 每一 Query 的 `set(E3 Top100) == set(E4 Top100)` 必须自动断言；所以 E3/E4 **Recall@100 应严格相等**（以相同 qrels 与定义计算）。两者 NDCG@10 的差异归因于前 50 的重排序，但可能存在截断和域迁移造成的负收益。WANDS 已标注商品的同候选重排作为辅助诊断，**不得混作全库检索成绩**。

## 5. 指标：主结论、辅助诊断与局限

### 5.1 主结果（测试集、按 Query Macro Average）
- SciFact：`NDCG@10` 主指标；`Recall@100` 辅助（基于官方 Qrels）。
- WANDS：`NDCG@10` 主指标，固定 `Exact=2 / Partial=1 / Irrelevant=0`，`DCG` 使用 `2^rel-1` gain；**必须标注为 ARC-WANDS-400 Custom Split + Qrels-based NDCG@10**。未标注的返回项仅在计分实现上按 0 gain 处理，**不能解释为真实无关**。
- WANDS 辅助：`Observed-Recall@100`（已标注 Exact/Partial 正例中的覆盖率；与真实全量 Recall 区分）；`Judged@10`（Top10 中有判断标签的比例）；按 Exact / Partial 的检索命中分布。可选增加“已标注候选集合内的重排”诊断，单独命名并与全库评测隔离。
- 各指标的空查询、无正例、平分处理、ID 类型、输出顺序必须在评测器中显式规定，且通过最小手算单测；禁止默默删除难题/零结果 Query。

### 5.2 统计方法
- 所有运行共享相同正式 Query ID 列表；提供每 Query 原始指标、Runfile 与逐 Query 差值。
- E3 vs E1/E2、E4 vs E3 采用 **Query 级配对 Bootstrap（预设随机种子及 2,000 次重采样）** 报告 95% 区间；区间仅描述有限 Query 样本波动，不解决 qrels 缺失带来的系统偏差。
- 不因测试集结果反复调参。模型和主要参数根据官方默认或 dev 配置决定，正式 test 是最后一次确认；如果之后重新优化，应新建实验版本并公开记录。

## 6. 运行成本协议

- 离线：数据载入、Embedding 编码、稀疏/稠密索引构建、索引磁盘占用分别计量。
- 在线：Query 编码、两路检索、RRF、Cross-Encoder、结果组装分阶段计时；请求整体 P50/P95 单独报告。单请求稳态性能测量前执行 warm-up；严禁将全量文档离线编码时间加入单次检索时延。
- 服务器作为**正式性能基准**：记录 GPU 型号/显存、驱动、CUDA、CPU、内存、软件版本、并发数、batch size、量化和峰值显存。其他共享 GPU 负载存在时**暂停或标记结果无效**，不假装结果可比。
- 质量运行和性能运行可分开执行，但必须锁定相同检索逻辑、模型权重与配置，并在报告中说明具体环境。
- V0 不测试生产级百万索引性能；FAISS Flat Exact 是故意排除 ANN 误差的可信基线，HNSW/IVF 后续作为独立系统性能消融。

## 7. 工程验收门槛与实验工件

每次运行必须记录/输出：
- `dataset_manifest.json`：来源、SHA-256、规模、字段、许可证、拆分与标注统计；
- `index_manifest.json`：数据、索引、tokenizer 与 encoder revision、配置哈希；
- `experiment_config.yaml`：模型与策略、候选预算、后端、随机种子；
- `runs/{dataset}/{strategy}.trec`：标准 6 列排名文件、无重复 ID、稳定排序；
- `metrics/{dataset}/{strategy}.json` 与 `per_query.csv`；
- `traces/`：每一阶段的候选、得分/排名、耗时及状态（面向本地测试数据）；
- `report.md`：两个数据集独立的质量表、延迟表、失败案例、未知项及公平性说明。

## 8. 里程碑与 Stop/Go 门槛

- **M0 数据与评测器**：完成数据加载审计、固定 split、对象 ID 映射、qrels 规范化与小型合成排名的指标单测。不需要 GPU；**未通过前不得运行并发布正式模型评测**。
- **M1 BM25 + Dense**：同一 Core 完成 SciFact 和 WANDS 的完整 Top100，生成上述工件，验证 Test Query 隔离。
- **M2 Hybrid + Rerank**：按 E3/E4 不变量运行消融；完成截断报告与逐 Query 错误分析。
- **M3 Harness 交付**：薄 HTTP 适配层、复现脚本、Docker、正式报告、轻量本地演示；不声称完整企业级 ACL 或生产就绪。

## 9. 上游文档关系与未决项

- 继承 RFC-001 的 `Entity / RetrievalUnit / IndexSnapshot`、在线 `search()` 与离线 Benchmark Runner 边界。
- 继承 ARC-EVAL-001 的两套 Benchmark 与 WANDS 自定义 `80 dev / 400 test`；不覆盖已冻结 Markdown。
- 与 RFC-001 早期候选商品重排路径不同的变更已在 ARC-EVAL-001 记录；未来 RFC-001 v0.2 合并。
- **未决且需 M0 实测确认：** WANDS 真实数据中 `(query_id, product_id)` 重复、标签冲突、空字段分布及每 Query 的已标注正例分布；这些数据质量问题如影响标准指标，应先记录并审定修复，不得悄悄修改 Qrels。

## 官方参考

1. BEIR / SciFact 官方索引：https://github.com/beir-cellar/beir/wiki/Datasets-available
2. Wayfair WANDS 原始仓库与格式：https://github.com/wayfair/WANDS
3. BGE-small-en-v1.5 模型卡：https://huggingface.co/BAAI/bge-small-en-v1.5
4. Sentence Transformers Cross-Encoder 官方模型说明：https://sbert.net/docs/cross_encoder/pretrained_models.html

**本文件为审定草案，不代表已运行或通过验收。**
