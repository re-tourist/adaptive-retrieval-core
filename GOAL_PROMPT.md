# ARC · Original V0 Codex Goal Prompt

> Historical record of the original V0 execution request. D0–M3 passed and shipped in v0.1.0. See [the evidence ledger](PROGRESS.md) and [current contribution rules](AGENTS.md).

---

**Goal: Complete Adaptive Retrieval Core V0 end-to-end through D0, M0, M1, M2, and M3 in one continuous workstream, without asking me to send a new prompt after each milestone.**

First inspect the existing repository and read `AGENTS.md`, `PLAN.md`, `PROGRESS.md`, `docs/plan/ARC-PLAN-001.md` and the referenced frozen specifications. Preserve the existing committed documentation and user edits.

Follow the stage gates in the master plan. Implement each stage, run the actual checks, repair failures, produce acceptance evidence, update progress and make safe, traceable commits. **On PASS, continue to the next stage automatically**; do not stop solely for milestone confirmation. For each stage save the exact commands/exit codes, artifact paths, relevant environment versions, Git commit, tests and remaining risks. Follow `docs/engineering/GIT_WORKFLOW.md` and keep GitHub Issues/Milestones synchronized when authorized and permitted, but do not let missing GitHub management permissions block local code work.

Use Python 3.12 + uv. Respect the modular monolith/hexagonal dependency boundaries. Keep the two frozen benchmark choices (SciFact and WANDS), and execute E1–E4 under the EXP-001 adjudication. Do not train new models, add multimodal/Agentic Search, replace official labels, adjust test data to improve scores, or claim unmeasured results. Do not edit frozen documents in place, modify unrelated environments, force push, merge protected branches or publish credentials.

If you encounter genuine external blockers, potentially destructive operations, missing permissions, materially contradictory specifications, corrupted official data or an irrecoverable failed gate, stop the affected activity, mark BLOCKED in `PROGRESS.md`, and ask only for the specific decision or permission needed. If the session ends for budget/context/platform reasons, preserve resumable evidence and a clear next step. Never claim V0 complete unless all D0–M3 are genuinely PASS.

At the end, produce a consolidated, evidence-based V0 acceptance report with both benchmarks' real per-strategy metrics, stage-level pass/fail matrix, performance conditions, reproducibility instructions, Git history, limitations and unverified items.
