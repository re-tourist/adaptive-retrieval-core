# ARC GitHub 开发工作流

**Issue → Branch → Commit → PR → CI → Merge → Issue Close**

1. 在 [Issues](https://github.com/re-tourist/adaptive-retrieval-core/issues) 查找或创建可独立验收的任务，写明范围和验收条件。阶段用 Milestone 聚合，详细设计放在技术文档。已交付工作的补录标记 `Retrospective`，写明事后归档并链接原始证据。
2. 检查工作区并从最新远程默认分支创建独立分支，例如 `codex/docs-governance`。保留本地已有修改。用 Conventional Commits 提交便于独立审查的变更。
3. 提交前检查暂存差异、测试、lint 和敏感内容。开 PR 时关联 Issue，填写实际命令、退出码、结果、证据路径和已知限制。Codex 主导的 PR 标明 **AI-assisted implementation**，并如实填写审核状态。可用 Draft PR 收集尚未齐备的证据。
4. 合并前核对当前 PR 提交的全部 CI 检查与平台要求。低风险文档和治理 PR 可按 [AGENTS.md](../../AGENTS.md) 授权正常合并。核心算法、重大架构、正式实验协议和安全相关变更须人工审核。正式发布须单独授权。GitHub 的权限、分支保护和审批规则始终生效。
5. 合并后确认默认分支包含交付，关闭已验收的 Issue 并关联 PR 与证据。确认阶段验收条件和相关 Issues 均已完成后关闭 Milestone。阶段验收报告记录命令、退出码、结果、提交和限制。发现阻碍时在 Issue 或 PR 记录原因和下一步。

冻结规范的变更用新 ADR 记录背景、决策、影响及替代条款。涉及数据复现时核验许可、记录官方来源与校验值，避免提交密钥、私有配置、模型权重、大型数据和原始实验产物。
