# ARC GitHub 开发工作流

1. 从最新的远程默认分支创建独立 feature 或 milestone 分支，例如 `codex/m0-data-audit`。同步前先检查工作区和远程分支，保留现有本地修改。
2. 使用 Conventional Commits，按可独立审查的变更提交，例如 `docs: add milestone acceptance report` 或 `feat(retrieval): add sparse retrieval adapter`。
3. 重大变更必须通过 Pull Request 审查。可先开 Draft PR 汇集证据。禁止强推、破坏性 reset 或未经授权直接修改受保护分支。
4. 每个里程碑必须提交精简验收报告，记录实际测试和 lint 命令、退出码、结果、证据路径、提交和未解决事项。在项目进度表登记验收结论。
5. 提交前检查 staged diff 和新增文件。禁止提交密钥、个人服务器配置、私有路径、模型权重、大型数据、原始实验产物或未经授权的数据。需要复现数据时，核验许可并记录官方来源和校验值。
6. 重大架构变更通过新增 ADR 记录背景、决策、影响及所替代的条款，再随 PR 审查。冻结规范原件按版本保留。
