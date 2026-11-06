# ARC · Repository Instructions for Codex

Use the [Git workflow](docs/engineering/GIT_WORKFLOW.md) for contributions, the [documentation index](docs/INDEX.md) for design and protocol, and [GitHub Issues](https://github.com/re-tourist/adaptive-retrieval-core/issues) for current work. [PLAN.md](PLAN.md) and [PROGRESS.md](PROGRESS.md) record the delivered V0 program. Start new stages only within the user's authorized scope. Continue through authorized stages until the acceptance gates pass or a concrete blocker stops the affected work.

## Authority and review

- Within the authorized task, Codex may maintain Issues, Milestones and labels, create branches and commits, open PRs, run tests, fix CI within scope, update acceptance evidence, and maintain task links and completion states.
- Codex may merge low-risk documentation and governance PRs through GitHub when all CI checks for the current PR head pass, required reviews are satisfied, and the platform permits a normal merge.
- Core algorithms, major architecture, formal experiment protocols and security-related changes require human review before merge. Formal releases require separate authorization. Document changes to frozen specifications in new ADRs and raise material conflicts for human decision.
- Respect branch protection, review rules and access controls. Do not force-push, reset user changes, delete remote resources, change security-sensitive permissions or administrator settings, or modify Secrets. Record access blockers and the specific next step. Keep working on unaffected tasks.
- Mark every Codex-led PR **AI-assisted implementation** and record its Issue, actual verification and review state. Use the configured Git author and authenticated GitHub identity. Never attribute authorship or approval to someone who did not provide it.

## Architecture and evaluation

- Use Python 3.12 and uv with the committed lockfile. Read the [engineering design](docs/ENGINEERING.md) and [frozen architecture](docs/architecture/ARC-TECH-001.md) before changing code. Keep the domain independent of application, adapters, evaluation and ML frameworks. Application code uses domain and Ports. Connect concrete adapters at bootstrap.
- Keep dataset adapters, vertical rules and offline evaluation separate. Preserve source IDs. Never leak Qrels or test labels into requests, routing, document text or model selection. Use dev for decisions and test for final reporting.
- Read the [evaluation baseline](docs/evaluation/ARC-EVAL-001.md), [experiment protocol](docs/evaluation/ARC-EXP-001.md) and [execution decision](docs/evaluation/ARC-EXP-001-EXECUTION-DECISION.md) together before touching benchmark work. Preserve the WANDS split and explicit disputed-label policy. Under the V0 protocol, E3 and E4 share the same Top-100 entity set per query. Report NDCG@10, observed recall, judged coverage and dataset caveats.
- Keep private configuration, credentials, server paths, models, raw data and indexes out of Git. Verify dataset licensing before redistribution. Keep GPU drivers and unrelated Docker/Conda environments outside the task.

## Acceptance

Run relevant tests and lint. Record commands, exit codes, evidence, commit and unresolved limits in the PR and, for milestone acceptance, in a durable report. Report failed and unverified checks and negative experiment findings. Resume from recorded evidence and verify the relevant artifacts against Git history. If a gate is blocked, report the observed cause and exact next step.
