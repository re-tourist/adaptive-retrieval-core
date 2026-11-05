# ARC · Continuous Goal Progress

- **Updated**: 2026-11-05
- **Execution**: IN PROGRESS
- **Next stage**: M1 real BM25 and Dense baselines
- **Provenance**: Planning artifacts generated in ChatGPT. No repository code, CI, datasets, Docker or GPU runtime was executed/verified as part of this file.

| Stage | State | Verified acceptance evidence | Git commit |
|---|---|---|---|
| D0 | PASS | [Report](artifacts/acceptance/d0/report.md) · [Checks](artifacts/acceptance/d0/checks.json) | `ccb402f2d892b0dc87809dfaebdb2355e8bee194` |
| M0 | PASS | [Report](artifacts/acceptance/m0/report.md) · [Checks](artifacts/acceptance/m0/checks.json) | `7845e78180d7f1cbee486ec01d3e694af8fdc0d4` |
| M1 | IN_PROGRESS | BM25/BGE and FAISS adapters, frozen-run evaluator and sensitivity checks under development | — |
| M2 | NOT_STARTED | — | — |
| M3 | NOT_STARTED | — | — |

## Next action

M0 passed both official data audits after [ADR-003](docs/adr/ADR-003-wands-disputed-labels.md) approved the 14 DISPUTED exclusions. M1 uses the admitted, fingerprinted Qrels and keeps the sensitivity assessment separate from tuning. The Pre-Goal PR remains Draft after the platform rejected the merge. The development branch is based on the reviewed Pre-Goal revision.

## Progress entry format (append per stage)

```text
### [timestamp] [stage] [PASS/BLOCKED]
- Branch/commit:
- Files changed:
- Executed commands + exit codes:
- Test counts and outputs:
- Evidence artifacts (paths):
- Environment / dataset / model / index fingerprints:
- Unverified items / risks:
- Next stage or exact blocker:
```

If execution is interrupted, treat the repository, actual test outputs and Git history as source of truth; do not trust a status line without its evidence.
