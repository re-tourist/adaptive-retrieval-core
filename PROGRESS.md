# ARC · Release Evidence Ledger

- **Scope**: Released V0 and Showcase work. See [GitHub Issues](https://github.com/re-tourist/adaptive-retrieval-core/issues) for current work.
- **Execution**: COMPLETE (V0 engineering acceptance)
- **Acceptance**: [ARC V0 report](docs/ARC-V0-ACCEPTANCE.md)
- **Retrospective archives**: [v0.1.0 milestone](https://github.com/re-tourist/adaptive-retrieval-core/milestone/1) and [v0.2.0 milestone](https://github.com/re-tourist/adaptive-retrieval-core/milestone/2).
- **Provenance**: Stage reports link to executed checks and immutable implementation commits.

| Stage | State | Verified acceptance evidence | Git commit |
|---|---|---|---|
| D0 | PASS | [Report](artifacts/acceptance/d0/report.md) · [Checks](artifacts/acceptance/d0/checks.json) | `ccb402f2d892b0dc87809dfaebdb2355e8bee194` |
| M0 | PASS | [Report](artifacts/acceptance/m0/report.md) · [Checks](artifacts/acceptance/m0/checks.json) | `7845e78180d7f1cbee486ec01d3e694af8fdc0d4` |
| M1 | PASS | [Report](artifacts/acceptance/m1/report.md) · [Checks](artifacts/acceptance/m1/checks.json) | `141d634aa3cdf291371be95500293227f43e361d` |
| M2 | PASS | [Report](artifacts/acceptance/m2/report.md) · [Checks](artifacts/acceptance/m2/checks.json) | `4419393c346b6aa3a551e2878c06812a765ba2a7` |
| M3 | PASS | [Report](artifacts/acceptance/m3/report.md) · [Checks](artifacts/acceptance/m3/checks.json) | `f99c33161aaf5bcbcf3f70ea389e8e1ea72d7f26` |

## v0.1.0 release and remaining external checks

[Release v0.1.0](https://github.com/re-tourist/adaptive-retrieval-core/releases/tag/v0.1.0) points to the merge of [PR #2](https://github.com/re-tourist/adaptive-retrieval-core/pull/2). Target server performance remains BLOCKED because no designated server was available. Local CUDA, localhost HTTP, CPU Docker, and the complete official E1–E4 experiments have independent evidence. The development branch started from the reviewed Pre-Goal revision after the initial platform restriction. [Pre-Goal PR #1](https://github.com/re-tourist/adaptive-retrieval-core/pull/1) was later merged.

## Showcase follow-up

- Implementation `2942a25` on `codex/arc-showcase`.
- Local wheel, browser, corpus audit and documentation checks passed. The [Showcase report](artifacts/acceptance/showcase/report.md) records commands, results and screenshot provenance. Final platform and container checks are recorded on [PR #3](https://github.com/re-tourist/adaptive-retrieval-core/pull/3), whose commits entered main through PR #5.

## Showcase V2

- Runtime `703d8e2` on `codex/arc-showcase-v2` integrates the reviewed design with the live 22-item catalog.
- Clean CPU wheel, full Dense-dependent suite, catalog and legacy HTTP smoke, browser parity and visual checks passed locally. The [V2 acceptance report](artifacts/acceptance/showcase-v2/report.md) records commands, results, scope and captures. [Design PR #4](https://github.com/re-tourist/adaptive-retrieval-core/pull/4) preserves the prototype and was closed without merging. [Implementation PR #5](https://github.com/re-tourist/adaptive-retrieval-core/pull/5) records the final Windows, Ubuntu and Docker checks. [Release v0.2.0](https://github.com/re-tourist/adaptive-retrieval-core/releases/tag/v0.2.0) points to its merge.
