# ARC-TECH-001 · 技术架构与仓库规范

**项目：** Adaptive Retrieval Core（ARC）  
**副标题：** Technical Architecture & Repository Specification  
**版本：** v0.1  
**状态：** **FROZEN — 设计基线**（架构已审定；具体代码与运行结果尚未验证）  
**日期：** 2026-11-05  
**规范原件：** 本 Markdown；DOCX 是阅读副本  
**关联：** RFC-001 v0.1（需求基线）、ARC-EVAL-001 v0.1（Benchmark 选型）、ARC-EXP-001 v0.1（实验草案）、ARC-M0-001 v0.1（数据与评价任务）

> **决策摘要**：ARC 采用 **模块化单体（Modular Monolith）+ 轻量六边形架构（Ports & Adapters）+ 适度 DDD**。统一检索语义和应用编排；通过实现接口扩展检索算法，通过垂直业务模块扩展业务规则，通过独立离线评价扩展 Benchmark。V0 坚持有限抽象、可信实验和可移植交付，不以微服务数量或算法种类衡量工程质量。

---

## 1. 本文档的职责与优先级

本规范用于 **D0 项目初始化与后续 M0–M3 开发**，固定模块职责、依赖方向、数据归属、目录边界、扩展规则和最低验收要求；不固定所有 Python 方法签名、模型超参数、部署容量或未来多模态模型。

**文档生效顺序：**

1. `RFC-001` 保留项目目标、总体范围和安全约束。
2. `ARC-EVAL-001` 明确取代 RFC 原有的 ESCI 商品候选重排主测：V0 正式采用 **BEIR / SciFact + Wayfair / WANDS** 两套**全库检索** Benchmark。RFC 原件不静默覆盖，待 v0.2 同步。
3. `ARC-EXP-001` 仍为 **PROPOSED**：四组算法基线、Top-100、Rerank 前 50 等属于待实施的实验协议，不因本架构冻结而自动冻结。
4. 本 `ARC-TECH-001` 专门决定**代码组织和内部模块边界**。若与 RFC 的「单一搜索后端」候选方案不同，依第 8 节的 ADR 显式记录并在 RFC v0.2 统一。
5. `ARC-M0-001` 在 **D0 完成并验收后**开始实施；D0 不能替代 M0，也不能提前声称评测已通过。

## 2. 推荐架构与术语

### 2.1 设计风格

采用**一个仓库、一个可安装 Python 核心包、进程内模块协作**的模块化单体。使用 **Ports** 规定应用需要的检索能力，**Adapters** 实现具体 BM25、FAISS、Cross-Encoder 等技术。Domain 表达检索系统的业务语义，Application 编排检索用例；Entrypoints 只是入口，Evaluation 作为离线调用方。

**运行与依赖关系（概念图）：**

```text
外部业务 / SDK / CLI / 后续 REST API
                  |
                  v
       Entrypoints (输入校验 / 传输)
                  |
                  v
       Application (SearchService / Pipeline)
           |           |             ^
           v           v             |
        Domain       Ports <----- 实现 ---- Adapters
     (Entity/Unit)  (Retriever/          (BM25/Dense/
                     Reranker/Store)      Index/模型)
           ^              ^
           |              |
  Verticals (Technical / Ecommerce) 由 Bootstrap 注入策略或实现

Evaluation Runner --通过应用公开用例--> Application
Observability   <------ 应用阶段事件 / Trace
Bootstrap 负责组装各个具体实现（唯一允许知道大部分实现的地方）
```

**依赖方向规则：**

- `domain` 不依赖 `application`、`adapters`、`entrypoints`、`evaluation` 和具体 ML 框架。
- `application` 依赖 `domain` 及其 Ports，不直接 import `bm25s`、`faiss`、Sentence Transformers 等具体实现。
- `adapters` 可以依赖 Ports / Domain 并实现接口；不可反向要求 Domain import Adapter。
- `verticals` 依赖稳定的 Domain / 应用策略接口，向 Bootstrap 提供业务策略；Application 不直接引用 `WANDS` 或某个电商品牌。
- `evaluation` 通过真实检索用例和 Runfile 评价；**Qrels 不进入线上检索或策略决策路径**。
- `entrypoints` 只转换请求、处理传输错误与呈现输出；不写 BM25、融合或排序逻辑。
- `bootstrap` 可以依赖所有组件，但不能成为隐藏业务逻辑中心。

### 2.2 英文名称选择与边界

| 名称 | 中文 | 定义与使用原因 |
|---|---|---|
| `entrypoints` | 外部入口 | CLI、未来 REST 或 SDK 的接入点；与核心用例解耦。 |
| `application` | 应用服务 | Search / Indexing / Pipeline 的用例与编排；解决「谁组织各阶段」。 |
| `domain` | 检索领域 | 检索对象、身份、内容关系和不变量；不是所有数据类的收容所。 |
| `ports` | 能力端口 | `Retriever`、`Reranker`、必要的 Store 等抽象契约。 |
| `adapters` | 技术适配器 | 具体模型、索引、外部数据集的接入实现。 |
| `verticals` | 垂直业务 | `technical`、`ecommerce` 的字段规则、查询/结果策略；区别于 DDD 的 `domain`。 |
| `evaluation` | 离线评测 | Qrels、实验、指标、Runfile，不属于线上主链路。 |
| `observability` | 可观测性 | 阶段耗时、错误、Trace 和后续运行指标。 |
| `bootstrap` | 依赖装配 | 创建/连接 Port 实现，不包含业务判断。 |

`profiles` 改名为 `verticals`，是为了强调垂直业务，而非普通配置档案。**「领域模型」与「业务垂直域」不是同一层概念。**

## 3. 模块职责与数据模型归属

### 3.1 Domain（核心语义）

**应包含：** `Entity`（最终返回对象）、`RetrievalUnit`（参加匹配的单元）及 ID / 修订 / 来源位置等规则。一个 Entity 可对应多个 Unit；一个 Unit 可以拥有多种检索表示。Domain 中不保存 FAISS Index 对象、模型 Tensor 或 API 序列化字段。

V0 的 `RetrievalUnit` 可主要使用文本内容；但其 **身份、来源和内容引用**不应假定所有未来 Unit 都只能有 `str`。若 V2 加入图片，可通过显式类型化内容引用和接口版本演进扩展，**不要求 V0 立即实现通用多模态 Payload**。

### 3.2 Application（用例）与 Ports（能力契约）

`SearchService` 接受应用级查询契约，通过 Retriever 获取候选、应用过滤/融合、调用 Reranker、聚合 Unit 与 Entity、生成输出与 Trace。`IndexingService` 协调数据修订、索引构建及版本切换。

初版真正需要的抽象建议为：`Retriever`、`Reranker`、必要的 `EntityStore`；`FusionPolicy` 作为独立策略实现，不必一开始建立复杂插件体系。索引能力可以有明确的 **Index Manifest 与内部生命周期接口**，但只有出现第二种实际索引实现和替换需求时，才拆出更细的 `IndexBackend` Port。检索能力与索引身份必须**概念解耦**。

### 3.3 Adapters 与 Verticals 的区别

- **Retriever / Reranker / Index Adapter**：解决「怎样计算和查找」（BM25、Dense + FAISS、Cross-Encoder；未来 ColBERT）。
- **Dataset Adapter**：解决「某个公开数据文件怎样变成标准 Entity、Unit、Query、Qrels」（SciFact、WANDS；未来 FiQA）。
- **Vertical**：解决「某类企业业务如何理解字段、硬约束和返回结果」（技术文档、电商）。

**新数据集 ≠ 新业务领域。** 新增 FiQA 不必新建金融 Vertical；新增一个真实商品业务规则，也不需要修改 WANDS 的原始数据适配器。

### 3.4 数据模型所属位置

| 对象 | 归属 | 原因 |
|---|---|---|
| `Entity`、`RetrievalUnit` | `domain/` | 稳定语义与身份。 |
| `SearchQuery`、`SearchResult`（应用级） | `application/` 或其契约模块 | 用例参数与输出，不等于 HTTP DTO。 |
| HTTP Request / Response | `entrypoints/` | 传输格式与外部校验。 |
| `Qrel`、`ExperimentConfig`、`Runfile` | `evaluation/` | 仅离线评价；避免数据泄漏。 |
| `IndexManifest` / Snapshot | 索引生命周期契约 | 记录构建依赖、版本、兼容性。 |
| Embedding、Token 多向量、FAISS 句柄 | 具体 `adapters/` | 技术实现细节，不是业务对象。 |

## 4. 建议仓库结构与演进规则

```text
adaptive-retrieval-core/
├── pyproject.toml
├── uv.lock
├── .python-version
├── README.md
├── src/arc/
│   ├── __init__.py
│   ├── domain/
│   │   └── models.py           # Entity, RetrievalUnit, invariants
│   ├── application/
│   │   ├── search.py           # SearchService
│   │   ├── indexing.py         # IndexingService (按阶段实现)
│   │   └── ports.py            # Retriever, Reranker, Store contracts
│   ├── adapters/
│   │   ├── retrievers/         # M1: bm25.py, dense.py
│   │   ├── rerankers/          # M2: cross_encoder.py
│   │   ├── indexes/            # M1: FAISS + manifest utilities
│   │   └── datasets/           # M0: scifact.py, wands.py
│   ├── verticals/              # Technical / Ecommerce policy, 按需创建
│   ├── entrypoints/            # M0/M1 CLI；M3 才考虑 REST API
│   ├── evaluation/             # M0: qrels, runfile, metrics, runner
│   ├── observability/          # 轻量阶段 Trace
│   └── bootstrap.py            # 组装具体组件
├── configs/
│   ├── datasets/
│   └── experiments/
├── tests/
│   ├── unit/
│   ├── contracts/
│   └── integration/
├── docs/
│   ├── rfc/
│   ├── architecture/
│   ├── evaluation/
│   └── tasks/
├── data/                      # 本地数据，默认 Git 忽略
└── artifacts/                 # 索引/Runfile/报告，默认 Git 忽略
```

**目录树是目标结构，不是 D0 要生成的所有空包。** 只按真实任务增加文件。`src` Layout 防止测试直接依赖仓库根路径；公开 API 从 `arc` 或专用入口导出即可，V0 不需要独立的 SDK 服务。

## 5. 执行路径、评测隔离与接口契约

### 5.1 线上检索路径

```text
SearchRequest / Query
    ↓ 解析、Schema 校验与允许的过滤
SearchService
    ↓ Retriever(s) -> 候选集合
    ↓ Fusion Policy (如 RRF)
    ↓ Reranker (如 Cross-Encoder)
    ↓ Entity/Unit 聚合与结果组装
SearchResult + Trace（根据权限与入口策略暴露）
```

`SearchService` 不应知道具体数据集名称；可由 Bootstrap 注入 `VerticalPolicy`、已校验过滤及 Adapter 实例。不同算法分数不天然可比较；响应中的 Score 必须附上下文或只作内部诊断，不承诺跨策略统一语义。

### 5.2 离线评价路径

```text
官方数据 -> Dataset Adapter -> Corpus / Queries / Qrels
                  |               |          |
                  +-----> 索引与真实 SearchService <-+
                                        |             |
                                 Runfile / Trace       |
                                        |             |
                                        +----> Evaluation Runner
                                                  ↓
                                      Metrics / Per-query / Report
```

**关键隔离：** Qrels 仅进入评价器，不进入 Retriever、Reranker、Vertical 查询策略、Query Router 或模型输入。若需要官方标签做 dev 调参，只能在明确开发划分内使用，不能访问保留 test 标签。

V0 主要支持 `BEIR / SciFact` 和 `Wayfair / WANDS` 全库检索，保持原始 Entity ID 与评测对象对齐。SciFact 为文档级 Qrels，WANDS 为商品级人工标签；WANDS 的未标注结果不应解释为真实负例。具体标签映射、Query 划分与 E1–E4 预算沿用现有 EVAL / EXP 文档。

### 5.3 数据/索引一致性

`IndexManifest` 至少记录 `index_id`、`dataset_revision/fingerprint`、`representation_type`、`encoder_revision`（如有）、`schema_version`、`backend/version` 和构建配置摘要；对于 Dense / Multi-vector 还应记录维度、距离定义与精度等兼容参数。模型更换后必须检查索引兼容性，不能复用不匹配向量。

V0 允许全量重建和快照切换，不要求实时增量同步；禁止同时混用互不兼容的 Entity、Unit、索引修订。认证授权不在 V0 实现范围：仅处理公开或获许可测试数据，**预留可见性字段不等于具备 ACL 防护**。

## 6. 三个扩展场景的设计压力测试

| 目标场景 | 应新增的内容 | 不应修改 | 设计边界 / 风险 | 评审 |
|---|---|---|---|---|
| **A. ColBERT** | Multi-vector 表示、专用索引、可选 Retriever / Reranker Adapter、配置和测试 | Domain Entity / Unit 语义、现有 BM25、基本评价指标 | 独立全库检索与候选重排的索引和成本不同；不得强制每个 Unit 只有一个向量 | **设计可行** |
| **B. 商品图文检索** | 图片内容引用、图文编码器及索引、跨模态 Query 契约版本、单独数据与 Qrels | Entity 稳定身份、技术文档逻辑、已有文本评价 | WANDS 不是图文检索标准基准；未来必须另选图像数据/任务，谨慎升级 Query API | **需受控扩展** |
| **C. 新 Benchmark（如 FiQA）** | Dataset Adapter、校验、评价配置 | SearchService、BM25/Dense、核心 Domain、通用 NDCG 实现 | Dataset Adapter 不等于新增金融 Vertical；Qrels 严禁泄漏给检索器 | **设计可行** |

以上是**纸面设计评审**，不等于 ColBERT、多模态或 FiQA 已经实现、运行或测试通过。未来增加一种技术的理想变更面应主要限于新实现、配置与测试，而不是持续修改核心用例和领域语义。

## 7. D0 开发前置规范

### 7.1 开发环境

- **Python 3.12**，统一包元数据为 `pyproject.toml`，使用 **uv** 管理虚拟环境与 `uv.lock`；锁定解释器主次版本，避免各环境随意漂移。
- **本地 Windows + 8GB GPU**：仓库初始化、M0 数据审计、单元与契约测试、轻量 Smoke。D0 / M0 必须能 **CPU-only** 执行。
- **Linux 服务器 + 48GB GPU**：M1/M2 批量 Embedding、Cross-Encoder、正式 Benchmark 与性能测量；记录具体 GPU 型号、CUDA、驱动、模型及运行配置。
- **按阶段引入依赖**：D0/M0 用 Pydantic / NumPy / 测试与质量工具；M1 才加入 `bm25s`、`faiss-cpu`、Sentence Transformers/PyTorch；M3 再加入 FastAPI/Uvicorn 和 Docker。
- CUDA 依赖需按目标平台单独验证；**不得为 ARC 随意修改服务器上其他项目的基础环境**。

### 7.2 D0 任务拆分

| 任务 | 内容 | 验收门槛 |
|---|---|---|
| D0.1 Bootstrap | `src` Layout、包元数据、锁文件、README、`.gitignore`、最小目录 | 干净环境可安装、导入 `arc`、运行测试；无 GPU/Benchmark 数据依赖 |
| D0.2 Contracts | Entity / Unit、不变量、搜索能力 Ports、最小假实现、IndexManifest 兼容校验 | 数据契约与依赖方向有测试；未实现真实 BM25/Dense |
| D0.3 Quality & CI | Ruff、Pytest、CPU CI、配置校验、Windows/Linux 安装说明 | 单命令本地测试通过；CI 不下载模型和大型语料 |

**D0 的 Stop/Go：** D0.1–D0.3 通过后才执行 `ARC-M0-001`；M0 重点加载并审计官方 SciFact/WANDS 数据、构建 Qrels 和评价器，不能提前混入模型评测或声称有算法提升。

### 7.3 三项扩展性契约测试（用 Fake/Stub 即可）

1. **替换 Retriever**：用 FakeRetriever 代替真实实现，`SearchService` 无需改动即可返回规范结果。
2. **新增 Dataset Adapter**：模拟第三个数据集，标准化语料/查询/Qrels，并在不修改 Core 的情况下通过评价器。
3. **索引兼容性**：针对 `representation_type`、模型修订和向量维度等不匹配情况，系统明确拒绝而非静默运行。

这三项只证明扩展点契约合理，不等于多模态能力已经实现。

## 8. 架构决策记录（ADR）

| ID | 决策 | 取舍与版本影响 |
|---|---|---|
| TECH-ADR-01 | 模块化单体、轻量 Ports & Adapters、适度 DDD | 不做微服务、CQRS、Event Bus、复杂 IoC 容器。 |
| TECH-ADR-02 | `domain` 表检索通用语义；`verticals` 表行业业务 | 代替模糊的 `profiles`，避免两套重复模型。 |
| TECH-ADR-03 | Application 通过 Ports 编排，Adapter 实现技术能力 | 不在 SearchService 中直接绑定 BM25/FAISS/模型 SDK。 |
| TECH-ADR-04 | Dataset Adapter 与 Vertical 分离；Evaluation 独立 | 方便新增 FiQA 和不同业务；Qrels 不泄漏。 |
| TECH-ADR-05 | Retriever、Reranker 与索引表示/生命周期概念分离 | 允许 ColBERT、多向量和未来跨模态索引；V0 不必预建复杂索引接口。 |
| TECH-ADR-06 | V0 倾向 **`bm25s + FAISS Flat Exact`** 作为两套轻量实现 | 与 RFC-001 v0.1「单个主搜索后端，OpenSearch 为候选」存在方案差异；**明确记录并待 RFC-001 v0.2 同步**。当前不声称拥有生产级单引擎能力。 |
| TECH-ADR-07 | Python 3.12 + uv、CPU-first D0/M0、GPU M1/M2 | 不为架构提前部署大型数据库或分布式系统。 |
| TECH-ADR-08 | 图文输入契约保留版本化扩展路径 | V0 不实现万能 Payload、多模态向量或 Agent 控制环。 |

**变更规则：** 目录内部拆分、类名、依赖补丁版本可在 D0/M0 细化；若改变模块依赖方向、主要对象身份、算法/索引责任边界、业务/评测隔离原则，应发布修订 ADR 或 `ARC-TECH-001 v0.2`，不得静默覆盖本文件。

## 9. 刻意避免的过度设计

1. 不自研 ANN、倒排索引、完整搜索引擎或 GPU Kernel。
2. 不提前实现十几个 Retriever / Reranker / IndexBackend 插件，也不需要通用插件注册市场。
3. 不建设复杂微服务、Kubernetes、Event Bus、CQRS、跨服务数据一致性平台。
4. 不把所有配置做成自定义 DSL 或任意检索 DAG；先保留有限策略组合。
5. 不让 `domain/models.py` 收容所有 HTTP、Benchmark、ML Model、数据库表结构。
6. 不在初版实现 Agentic Search、多模态检索、权限系统，却声称它们已支持生产使用。
7. 不把新增文件夹、抽象类数量或模型接入数量当作简历成效；关键看算法对照、稳定契约、质量/延迟和可复现性。

## 10. 冻结结论与下一步

**设计级结论：** 已确认合理支持（A）未来 ColBERT，（B）受控图文扩展，（C）新增公开 Benchmark；以稳定的 Domain / Application / Port 契约和可替换 Adapter 实现为中心。当前只冻结方向与规则，**没有代码与集成实测结果**。

**执行顺序：** `ARC-TECH-001 v0.1` → D0.1/D0.2/D0.3 → 核查 M0 任务单与接口一致性 → M0 数据与评测器 → M1 BM25/Dense → M2 Hybrid/Rerank → M3 交付与报告。

下一次需要集中讨论的具体接口问题，可在 D0.2 小范围细化，不必重新开放已冻结架构。对于实验参数的修改，遵守 `ARC-EXP-001` 的独立版本规则，不影响本文档。
