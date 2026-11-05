# ARC · Continuous Goal Progress

- **Updated**: 2026-11-05
- **Execution**: IN PROGRESS
- **Next stage**: M1 real BM25 and Dense baselines
- **Provenance**: Planning artifacts generated in ChatGPT. No repository code, CI, datasets, Docker or GPU runtime was executed/verified as part of this file.

| Stage | State | Verified acceptance evidence | Git commit |
|---|---|---|---|
| D0 | PASS | [Report](artifacts/acceptance/d0/report.md) · [Checks](artifacts/acceptance/d0/checks.json) | `ccb402f2d892b0dc87809dfaebdb2355e8bee194` |
| M0 | PASS | [Report](artifacts/acceptance/m0/report.md) · [Checks](artifacts/acceptance/m0/checks.json) | `7845e78180d7f1cbee486ec01d3e694af8fdc0d4` |
| M1 | IN_PROGRESS | [E1 full-corpus checkpoint](artifacts/acceptance/m1/report.md). E2 runtime pending. | `07478dc87e1749dd9b88497e97ba0af57de418e0` |
| M2 | NOT_STARTED | — | — |
| M3 | NOT_STARTED | — | — |

## Next action

M0 passed both official data audits after [ADR-003](docs/adr/ADR-003-wands-disputed-labels.md) approved the 14 DISPUTED exclusions. M1 uses the admitted, fingerprinted Qrels and keeps the sensitivity assessment separate from tuning. The Pre-Goal PR remains Draft after the platform rejected the merge. The development branch is based on the reviewed Pre-Goal revision.

### M1 checkpoint

- Local preflight used Python 3.12.8 and the hash-verified bm25s 0.2.14 wheel with the host numerical libraries. Command `python -B -m arc.evaluation.baselines --dataset <dataset> --method e1 --data <official-input> --admission artifacts/m0/admission --output artifacts/m1/preflight --split dev --smoke 10` exited 0 for both corpora. This was a dev-only runtime check.
- `uv lock --no-python-downloads` resolved 66 packages and exited 0. `uv sync --locked --no-python-downloads --group sparse --group dense` exited 1 after a network timeout. Verify remaining downloads and wheel hashes before retrying the locked install. Partial and verified downloads are under the ignored `.cache/m1-wheelhouse` and `models/bge-small-en-v1.5` paths.
- Local hardware detection reported a GeForce RTX 4060 Laptop GPU, 8,188 MiB and driver 566.24. Actual PyTorch CUDA execution is pending. BGE safetensors matched the pinned SHA-256 after downloading from BAAI on ModelScope. E1 full-corpus dev/test runs passed twice in both the host and locked sparse environments. Within each environment, Runfiles were byte-identical. Cross-version scores varied slightly and two WANDS test rank rows changed, with identical per-query metrics. Next verify dense runtime, run E2, and compute paired comparison and ADR-003 sensitivity.

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
