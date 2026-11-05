# ARC · Repository Instructions for Codex

This is a long-running, multi-milestone research-engineering project. **Do not stop after one milestone solely to ask for the next prompt.** Follow `PLAN.md` and `PROGRESS.md`; continue until all authorized stages pass, or a real blocking condition occurs. Starting D0 requires explicit authorization after Pre-Goal review.

## Read before modifying code

1. `PLAN.md` — executable stage gates and resumption.
2. `docs/plan/ARC-PLAN-001.md` — authoritative execution specification.
3. `docs/architecture/ARC-TECH-001.md` — frozen module and dependency rules.
4. `docs/evaluation/ARC-EVAL-001.md` and `docs/evaluation/ARC-EXP-001-EXECUTION-DECISION.md` — dataset and experiment boundaries.
5. `docs/evaluation/ARC-EXP-001.md`, `docs/tasks/ARC-M0-001.md`, `docs/rfc/RFC-001.md` — existing detail; preserve frozen originals.
6. `PROGRESS.md` — recorded evidence and next unfinished stage.

## Architecture and implementation

- Python 3.12, **uv** with `pyproject.toml` and a committed `uv.lock` once D0 creates it. Do not introduce competing package managers in ARC.
- Modular monolith / Ports & Adapters. `domain` MUST NOT import application, adapters, evaluation or concrete ML frameworks. `application` depends on domain and Ports, not concrete FAISS/bm25s/SentenceTransformers. Build adapters behind Ports and connect at bootstrap.
- Keep dataset adapters, vertical business rules and offline evaluation separate. **Never allow Qrels/test labels into retrieval requests, query routing, document text or model selection.**
- Preserve real source IDs; prefer precise, small vertical slices and tests over speculative abstractions. No microservices or multimodal/Agentic features during V0.

## Evidence, evaluation and phase gates

- Always run relevant tests and lint. Never invent a pass, model quality result, dataset, command execution or GPU benchmark.
- M0 validates official input sizes, deterministic WANDS 80/400 split, repeated/conflicting labels and hand-verifiable metrics. Refuse to silently resolve label conflicts.
- For M2, per-query E3/E4 must contain exactly the same Top-100 entity set. Report NDCG@10, observed recall and judged coverage with their dataset caveats.
- Treat test data as final reporting only; use dev for choices. Report negative findings, costs, incomplete labels and all relevant failures.
- After a stage genuinely passes, update `PROGRESS.md` with executed commands, evidence paths and commit, then proceed to the next stage. Store concise acceptance reports; keep large/raw data, model weights, sensitive env files and indexes out of Git.

## Safety, Git and external systems

- Do not edit frozen RFC/EVAL/TECH documents in place; document changes in new ADRs, then flag significant conflicts for user approval.
- Follow [Git Workflow](docs/engineering/GIT_WORKFLOW.md) and commit milestone-sized changes on a safe work branch. Do not force-push, reset user changes, delete remote resources, merge protected branches, rotate credentials, change GPU drivers or modify other Docker/Conda environments.
- Do not publish private server paths, proxy credentials or tokens to GitHub. Verify dataset licenses before redistribution; default to download scripts rather than committing data.
- A missing permission, incompatible environment, unavailable official dataset, material specification conflict or irreducible failing acceptance check is `BLOCKED`, not a success. Explain the blocker and exact next authorized step.

## Completion report

At each stage output an evidence-backed PASS/BLOCKED report (files changed, commands, exit codes, results, Git commit, unresolved risks). Final V0 report requires all D0–M3 gates passing. If interrupted, resume from PROGRESS and verify existing artifacts instead of starting over.
