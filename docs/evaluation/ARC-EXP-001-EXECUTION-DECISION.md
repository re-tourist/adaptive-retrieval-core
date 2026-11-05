# ARC-EXP-001 · Execution Adjudication（实验协议执行审定）

- **版本**：v0.1 · 2026-11-05
- **结果**：**CONDITIONALLY APPROVED FOR D0/M0**；原 `ARC-EXP-001.md` 仍标记 PROPOSED，待 M0 官方数据审计后才能确认 M1/M2 正式测试执行条件。
- **性质**：审定附录，不更改原始实验协议文本，也不声称实验已发生。

## 已审定可直接实施

- 固定两套主数据：BEIR/SciFact 5,183 文档，Wayfair/WANDS 42,994 商品；两者**全库检索**，不引入新数据集。
- SciFact：官方 test 300 queries；dev 取官方 train；Document 级 Qrels。
- WANDS：按 [原实验协议](ARC-EXP-001.md) 的 `SHA256("ARC-WANDS-v0.1|" + query_id)` 对唯一 query_id 稳定排序，同摘要按原始 query_id 排序，划分 80 dev / 400 test；**自定义协议**，成绩不可作为官方排行榜成绩。记录哈希与原始文件校验值。
- E1 BM25 Top-100；E2 BGE-small-en-v1.5 + FAISS IndexFlatIP Top-100；E3 两路各100、RRF k=60 后 Top-100；E4 对 E3 前50重排并接上未重排的后50，保持每个 Query 的 Top-100 集合不变。
- 文本字段、tokenization、截断、模型 revision、随机种子与硬件环境须记录；先 dev/smoke，再正式 test。不得根据 test 反复调参。
- SciFact `NDCG@10` 主指标，`Recall@100` 辅助；WANDS Qrels-based `NDCG@10` 为主，`Observed-Recall@100` 与 `Judged@10` 为辅助；明确未标注文档并不等于真实无关。
- 统计：Query 级配对差值、固定 seed 的 2,000 次 Bootstrap；正式质量与性能成本分开记录。
- 执行结果包含逐 Query Runfile、metrics、索引数据/模型版本与必要 Trace；数值不必优于基线，但不得伪造。

## M0 必须确认的 Gate（未知，不预判结果）

1. 官方数据来源、许可与 SHA-256 可确定；数据行数/唯一键/字符编码真实可靠。
2. WANDS 标签去重后，是否有 `(query_id, product_id)` 冲突；若有，必须输出冲突清单并暂停对冲突处理有依赖的正式评分，不允许自动选择标签。
3. SciFact 官方 test 与 dev 的文件和 Qrels 可分离；WANDS 的 80/400 清单确定、无交集，基于唯一 Query ID 划分。
4. 对无正例查询、缺失标签、未判结果、重复 Runfile ID、平分的处理有单测，报告中不混淆 Qrels-based Recall 与完整真实 Recall。
5. `Entity / Unit` 的 V0 1:1 对应正确；SciFact Document 级和 WANDS Product 级的 ID 可以可逆映射。

如果以上全部通过，自动在 M0 验收记录中确认协议可用于 M1/M2 **不需要额外的人类批准**；若发现重大源数据问题或需改变已冻结的 Benchmark/标签规则，则标记 BLOCKED 并提交差异和修订方案。

## 执行保护边界

- 不改变 SciFact/WANDS、相关性等级映射、正式拆分、Top-K、模型基线和指标定义；如有事实性错误，形成新 ADR，经过审批后修改，不能静默修补。
- 运行器可以用模拟数据测试指标代码，但禁止对外报告其为正式 Benchmark 结果。
- M1/M2 使用真实数据和真实模型权重；下载不到的情况下暂停，不使用随机或伪造权重代替。
- 在 M1 前检测目标服务器的 GPU、驱动与运行时，再确定 CUDA/PyTorch 配置并记录实测环境。正式性能验收以可复现的实际测量为准。

## 与上游文档的关系

`ARC-EVAL-001` 的两套 Benchmark 优先于 RFC 早期 ESCI 主测设想；`ARC-TECH-001` 的模块化单体、Port/Adapter 边界仍有效；本附录对 `ARC-EXP-001` 提供实施审批，不代表评测结果或技术收益已获得验证。
