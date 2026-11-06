# ARC · V0 execution plan archive

The [original V0 execution specification](docs/plan/ARC-PLAN-001.md) defined the five gates below. All five passed for [v0.1.0](https://github.com/re-tourist/adaptive-retrieval-core/releases/tag/v0.1.0). [PROGRESS.md](PROGRESS.md) links to the accepted checks and implementation commits. The [original goal prompt](GOAL_PROMPT.md) is retained for provenance.

| Stage | Acceptance scope |
|---|---|
| D0 | Python 3.12 and uv lock, contracts, fake adapters, architecture tests and CPU CI |
| M0 | Official SciFact/WANDS audit, deterministic WANDS split, Qrels metrics and Runfile |
| M1 | Full-corpus BM25 and Dense baselines, snapshot identity and replay |
| M2 | RRF and fixed-pool cross-encoder reranking, quality and cost |
| M3 | API, tracing, Docker, HTTP and reproducibility |

The [execution decision](docs/evaluation/ARC-EXP-001-EXECUTION-DECISION.md) records the conditions for admitting formal V0 experiments. The [acceptance report](docs/ARC-V0-ACCEPTANCE.md) records what was measured and the remaining limits. [v0.2.0](https://github.com/re-tourist/adaptive-retrieval-core/releases/tag/v0.2.0) followed as a Showcase release.

Track current work in [GitHub Issues](https://github.com/re-tourist/adaptive-retrieval-core/issues) and [Milestones](https://github.com/re-tourist/adaptive-retrieval-core/milestones). New stages need their own authorized scope and acceptance criteria.
