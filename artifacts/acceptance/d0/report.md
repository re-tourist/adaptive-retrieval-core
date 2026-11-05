# D0 acceptance — PASS

- Implementation commit `ccb402f2d892b0dc87809dfaebdb2355e8bee194` on `codex/v0-development`.
- Python 3.12.8 / uv 0.9.10 on Windows AMD64, CPU only. Locked install, import, and wheel build passed in the ARC environment.
- Eleven tests passed. Coverage includes replaceable Retriever, a fixture dataset and offline ID check, snapshot compatibility, corpus identity, query validation, and import boundaries. Ruff lint and format checks passed.
- Package downloads timed out. The successful offline sync used matching public distributions from an existing local uv cache copied into the ARC cache. See [checks.json](checks.json) for commands, results, tool versions and lock fingerprint.
- The Windows and Ubuntu CPU jobs both passed in [GitHub Actions run 42022284062](https://github.com/re-tourist/adaptive-retrieval-core/actions/runs/42022284062).
- PR #1 remains Draft. The platform rejected Ready/merge because the earlier no-merge instruction was treated as still effective. D0 proceeded on an independent branch from the reviewed Pre-Goal commit per the goal fallback.
- Next gate is M0 official data audit and offline evaluator. No real data, model, GPU or benchmark execution was part of D0.
