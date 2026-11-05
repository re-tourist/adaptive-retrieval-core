# ADR-002 · uv 工具链与 V0 轻量检索后端

- **状态**：ACCEPTED FOR V0 IMPLEMENTATION
- **日期**：2026-11-05
- **背景**：早期讨论在 uv 与 Conda + pip 之间切换；ARC 目标是跨 Windows/Linux 的可复现 Python 包。原架构 RFC 曾讨论统一搜索引擎（如 OpenSearch），后续实验协议倾向降低初期依赖。

## 决定

1. **uv + Python 3.12** 是 ARC 专属环境管理和项目依赖锁定的默认方案，生成 `pyproject.toml`、`.python-version`、`uv.lock`。ARC 独立配置项目环境，既有容器、镜像、Conda 环境及 CUDA/PyTorch 版本均不继承。
2. **V0：bm25s + FAISS Exact** 为优先实现路径，应用通过 Ports 调用检索器，允许 V1 适配 OpenSearch/Vespa 等成熟搜索后端。
3. M1 前检测目标服务器的 GPU、驱动和运行时，再确定 CUDA/PyTorch 兼容组合。Docker 镜像、GPU 设备、挂载目录、网络与代理在实施阶段决定。

## 理由 / 代价

uv 提供统一的项目环境同步与锁定机制；避免在个人与服务器之间维护两套互相冲突的版本清单。轻量后端可快速获得两套小中型数据的可信基线，但不代表生产级大规模索引服务。未来确需系统级二进制环境约束时可以新增显式例外，而非混用未经记录的包管理方案。

## 影响

该 ADR 仅更新工具链和 V0 后端的实施选项，不改变核心架构、Benchmark 或目标。历史冻结文档原件保持不变。
