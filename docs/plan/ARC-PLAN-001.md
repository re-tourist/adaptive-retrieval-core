# ARC-PLAN-001 · V0 Master Execution Plan（总执行计划）

- **版本**：v0.1.1（公开环境说明与执行入口澄清，阶段门槛沿用 v0.1）
- **状态**：FROZEN FOR EXECUTION（执行计划基线；不代表任何代码已完成）
- **项目**：Adaptive Retrieval Core（ARC）
- **日期**：2026-11-05
- **执行跨度**：D0 → M0 → M1 → M2 → M3（单个连续 Goal）
- **事实状态**：当前处于 Pre-Goal 文档复核阶段，D0–M3 尚未启动。

## 1. 目标与成功定义

完成 V0 版可安装、可测试、可复现的检索核心。以 **BEIR/SciFact** 与 **Wayfair/WANDS** 两个全库检索任务为固定主测；实现 E1 BM25、E2 Dense、E3 Hybrid/RRF、E4 Hybrid+Cross-Encoder 的可对比实验；提供独立评测路径、逐阶段 Trace 和轻量 API/CLI 交付。

**成功不要求指标单调提高或超越 SOTA**；要求运行真实、统计诚实、对照合理、代码质量达标、交付可复现。不得把模拟数据的模型结果写成公开基准成绩。

## 2. 权威依据、变更与冲突处理

1. `docs/rfc/RFC-001.md`：项目目标、边界与安全原则（历史冻结版本）。
2. `docs/architecture/ARC-TECH-001.md`：模块边界、依赖方向、目录与 D0 架构（冻结）。
3. `docs/evaluation/ARC-EVAL-001.md`：SciFact + WANDS 的 Benchmark 选型（冻结；明确覆盖 RFC 中 ESCI 主测的旧提议）。
4. `docs/evaluation/ARC-EXP-001.md`：E1–E4 实验协议（原文件为 PROPOSED）；本轮使用 `docs/evaluation/ARC-EXP-001-EXECUTION-DECISION.md` 解释执行批准范围和阻塞条件。
5. `docs/tasks/ARC-M0-001.md`：M0 数据/指标验收细则。
6. 本执行计划与 `AGENTS.md`：规定跨里程碑过程控制，不替代上述技术规范。

冲突处理：先识别同一主题的后续明确决策（Benchmark 选择 WANDS；V0 采用轻量 BM25 + FAISS；包管理采用 uv），记录冲突及采用理由；**不静默编辑 FROZEN 的原始文件**。重大技术偏离须新 ADR 并暂停相关部分，未授权时不得自行更改权威基线。

## 3. 开发与环境政策

- 仓库：单仓库 `src/arc` Python 包；Modular Monolith + Hexagonal Architecture + Lightweight DDD。
- 版本：Python **3.12**。使用 **uv**、`pyproject.toml`、`.python-version`、`uv.lock`。D0 实际解析并提交锁文件；后续通过 `uv sync --frozen` 或等效锁定安装复现。
- 本地 Windows/CPU 可用于 D0 与 M0。M1 开始前检测目标服务器的 GPU、显存、驱动与运行时，再确定 CUDA/PyTorch 兼容组合。需要 PyTorch 时在 M1 引入独立依赖组。
- ARC 使用独立的项目环境，优先采用 Python 3.12 + uv。既有容器、镜像、Conda 环境及 CUDA/PyTorch 版本均不继承。Docker 镜像、GPU 设备、挂载目录、网络与代理按实施阶段的实际条件决定。保留其他项目的环境、目录与系统配置。
- CI 优先 CPU 测试。GPU benchmark 不应作为强制 GitHub Actions 常规检查。
- 初始依赖最少化：D0 不预装模型或大型 ML 依赖；M0 不需要 GPU。
- 网络依赖和模型下载允许在用户提供的网络/权限条件内执行；禁止从不明来源替换官方数据或伪造下载成功。

## 4. 自动执行状态机

- 获得 D0–M3 的执行授权后，以 `PROGRESS.md` 为本地可恢复执行台账；每个阶段有 `NOT_STARTED / IN_PROGRESS / PASS / BLOCKED` 状态。
- 从第一个非 `PASS` 阶段开始：读取规范 → 制定阶段内子任务 → 实施 → 执行验收 → 修复重试 → 产出证据 → Git 提交 → 更新状态 → **自动进入下一阶段**。
- 每阶段创建 `artifacts/acceptance/{phase}/report.md`（可提交**精简报告**）、`artifacts/acceptance/{phase}/checks.json`（命令、退出码、时间、环境摘要），大体积中间文件在 `.gitignore`；如尚未创建验收程序，用现有真实命令记录证据。不要在未经运行的情况下标 PASS。
- 将 Git commit/branch、未解决项和下一步写入 `PROGRESS.md`。进度和关键测试报告纳入 Git；原始数据、权重、索引和敏感路径不得提交。
- 连续 Goal 不因完成一个阶段而停止；**在真正需要外部权限、访问真实数据失败、不可逆的危险操作、冻结规范冲突、无法核验的 GPU 运行或可重复的技术阻塞时暂停并报告**。
- 即使单次 Codex 会话因预算、上下文或平台原因中断，后续也以仓库状态和证据恢复；**不假设能不受限地后台运行**。
- 遵守 `AGENTS.md` 的 Git 与安全边界：允许在工作分支提交、更新经授权的 Issue；不强推、不自动合并保护分支、不泄露凭据。

## 5. D0 · Foundation / Pre-M0

**输入**：当前仓库文档，未必存在源码。**不下载数据与模型。**

交付：
- `src/arc` 可安装包、`pyproject.toml`、`.python-version`、`uv.lock`、`.gitignore`、基础 README/运行说明。
- 最小 `domain`（Entity、RetrievalUnit 的身份/关系规则）、`application` 与必要 Ports；Fake Retriever/Fake Adapter；`bootstrap` 可用最小装配。不创建无意义空包。
- Ruff、Pytest、CPU CI 及契约/架构测试；Windows/Linux 兼容策略。
- 按 [ADR-002](../adr/ADR-002-uv-and-lightweight-backends.md) 落实 uv 和轻量检索后端的决策，保留冻结原件。

**PASS 门槛**：干净隔离环境能安装并导入 `arc`；CPU `pytest`/Ruff 真实通过；Fake Retriever 可在不改 SearchService 时替换；模拟 Dataset Adapter 可接入；不兼容索引/编码版本能被拒绝；禁止 Domain 直接依赖检索 Adapter。CI 如未实际跑过只能写“配置生成，远端未验证”。

## 6. M0 · Data & Evaluation Foundation

**依据**：`docs/tasks/ARC-M0-001.md`；实施前审阅实验执行裁决。

交付：官方 SciFact/WANDS Adapter、字段及 ID 审计、WANDS 确定性 80/400 查询划分、Qrels 规范化、标准 TREC Runfile 读写、NDCG@10/Recall@100/Observed-Recall@100/Judged@10 及手算单测。

**PASS 门槛**：真实官方文件规模及引用关系、标签重复/冲突情况有报告；分割 manifest 哈希可复现；小型合成 Runfile 的分数与手算结果一致；正式测试集不用于调参；无 GPU。若官方文件与预期不一致或出现未决冲突标签，**BLOCKED** 并报告，不可静默改规则。

## 7. M1 · Sparse/Dense Baselines

**输入**：M0 PASS，正式数据协议已审定，推理环境可验证。

交付：E1 BM25、E2 BGE-small-en-v1.5 Dense + FAISS IndexFlatIP；两套**全库** Top-100；数据/编码器/索引 manifests，规范 Runfile 与逐 Query 指标。先 smoke 再 canonical test；模型及 tokenizer revision、截断统计写入结果。

**PASS 门槛**：同一 Core 通过 SciFact/WANDS Adapter 运行且不修改 Core；输出合法、可重复的正式文件；明确 CPU/GPU 环境和成本；不能将未运行的服务器测量推断为真实值。

## 8. M2 · Hybrid/Rerank/Analysis

**输入**：M1 PASS。

交付：E3 每路 Top100 → RRF k=60 → Top100；E4 对 E3 前50 使用 MS MARCO MiniLM-L6-v2 Cross-Encoder，重排后拼接 E3 后50；完成两数据集的 NDCG@10、辅助指标、逐 Query 差异、失败案例、配对 Bootstrap（固定 seed、2000 次）。

**PASS 门槛**：每个 Query 断言 `set(E3 Top100) == set(E4 Top100)`；若以一致 Qrels 算 Recall@100，数值相等；E4 只影响排序，不引入文档；报告成功、负收益和不确定性，不以分数提升为必要条件。

## 9. M3 · Harness Delivery

**输入**：M2 PASS。

交付：公共 Search API/CLI、薄 FastAPI 入口、基础 Trace、索引版本与部署说明、Docker 构建、轻量演示、完整重现实验入口、最终技术报告与简历可验证证据；补充端到端性能 P50/P95 与离线成本，区分生产和 Demo 级能力。

**PASS 门槛**：从干净环境能运行 CPU smoke；有服务端点与真实集成测试；Docker 如实际验证必须附构建/启动证据；官方数据和权重不进入镜像/仓库；正式 Benchmark 具备环境指纹、Runfile、逐 Query 和实验配置；完整成本/限制说明。对无法访问的服务器性能标 BLOCKED，不能标为 PASS。

## 10. GitHub 协作策略

建议五个 GitHub Milestones 与 D0/M0/M1/M2/M3 一一对应；Issues/PR 作为协作视图，**以仓库 PLAN + PROGRESS + 真实测试证据为执行事实依据**。若 GitHub 权限不足，继续本地已授权工作并说明无法同步远端，不能假装已创建 Milestone。

每阶段在独立工作分支提交或在授权工作分支连续提交；不 force-push、不覆盖用户未提交改动、不无许可合并到默认分支。阻塞时提供最小可复现报告。单阶段完成后无需等待新的 Prompt，可继续下一阶段。

## 11. 最终完成判定与交付报告

**只有 D0/M0/M1/M2/M3 全部 `PASS`，且所需正式实验确实执行完成，才可声明 V0 完成。**

最终交付至少包括：
- 阶段 PASS/FAIL/BLOCKED 矩阵及可追溯命令/退出码；
- 两套数据各四种策略的分开报告，未标注和非官方划分的局限；
- 每 Query Runfiles、完整配置、环境、模型及索引版本；
- 包安装、API、测试、Docker 和基线复现命令；
- Git 分支/提交/未提交修改，CI 状态；
- 性能 P50/P95、硬件/批次/并发条件和使用限制；
- 剩余风险、未验证项、推荐的 V1/V2 扩展。

**明确排除 V0**：多模态、Agentic Search、自研 ANN、分布式生产集群、企业级真实 ACL、针对 test 的连续试错调参。
