# ARC · Continuous Goal Execution Plan

**Project**: Adaptive Retrieval Core. **Execution authority**: [ARC-PLAN-001](docs/plan/ARC-PLAN-001.md) (v0.1.1). **Status**: planning only, no milestone implemented or verified by this package.

## One Goal, five stage gates

| Order | Stage | Outcome / minimum gate |
|---|---|---|
| 1 | **D0** | uv/3.12 package & lock; minimal contracts and fake adapters; pytest/Ruff; architecture tests; CPU CI config. |
| 2 | **M0** | Official SciFact/WANDS loading and audit; 80/400 stable split; verified Qrels metrics and Runfile. |
| 3 | **M1** | BM25 / Dense + FAISS Exact; full-corpus E1/E2, manifests and Query-level outputs. |
| 4 | **M2** | RRF E3 + fixed-pool Cross-Encoder E4; invariants, quality/cost and failure analysis. |
| 5 | **M3** | API, tracing, portable Docker/demo, end-to-end tests, benchmark and reproducibility report. |

**Algorithm for Codex, after execution is authorized**: read `AGENTS.md` + `PROGRESS.md` → implement first non-PASS stage → run its gate checks → fix or declare genuine BLOCKED → save commands/results & Git commit → mark PASS → **continue immediately**. A milestone completion **is not** a stop condition. Do not claim V0 complete until five PASS states and the actual final evidence exist.

**Environment**: ARC uses an isolated Python 3.12 + uv project environment. See [ADR-002](docs/adr/ADR-002-uv-and-lightweight-backends.md) for runtime decisions and [Git Workflow](docs/engineering/GIT_WORKFLOW.md) for milestone commits and review.

**Benchmark**: SciFact + WANDS only; WANDS scores use an explicitly custom 80 dev / 400 test protocol with incomplete labels. No leaderboard claims or unexplained train/test reuse.

**Blocking issues**: lack of access, dataset license/schema/labels conflicts, major frozen design contradiction, unavailable needed GPU, destructive action, repeated failed acceptance — stop affected operations and report rather than fabricate success.

For detailed gates, expected files and proof requirements, see **Sections 5–11 of `docs/plan/ARC-PLAN-001.md`**. For the experiment's conditional approval and unresolved checks, see **`docs/evaluation/ARC-EXP-001-EXECUTION-DECISION.md`**.
