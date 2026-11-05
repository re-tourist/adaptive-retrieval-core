# ARC Showcase acceptance

Local evidence for branch `codex/arc-showcase`. Playground implementation commit `2942a25`. The PR’s Checks tab records Windows, Ubuntu and the CPU container against the proposed head.

## Scope

- The same-origin Playground serves from `arc serve` and uses the existing search contract. It pins the active snapshot in each request and runs comparisons in sequence.
- `ARC_DATASET=playground` adds 12 original ARC notes as an opt-in CPU corpus. The original default corpus, ranking logic and evaluation inputs stay as released.
- The [README](../../../README.md) leads with a live example. The [Quickstart](../../../docs/QUICKSTART.md), [engineering guide](../../../docs/ENGINEERING.md), and [reproduction guide](../../../docs/REPRODUCING.md) carry setup and technical details.

## Local engineering checks

| Check | Exit | Observed result |
| --- | ---: | --- |
| `uv lock --check --offline` | 0 | 76 packages resolved with the existing lock |
| `uv export --locked --offline` followed by `uv pip sync --offline --no-index --require-hashes` | 0 | Clean Python 3.12.8 environment provisioned with 26 locked Windows CPU and test dependencies from a local wheel cache |
| `uv sync --locked --offline --group sparse --group harness --group harness-test --no-editable` | 0 | ARC wheel built and installed in the clean environment |
| `uv run --no-sync pytest` | 0 | 24 passed, 1 Dense-dependent test skipped in the CPU environment, 1 upstream TestClient deprecation warning |
| `uv run --no-sync ruff check .` and `uv run --no-sync ruff format --check .` | 0 each | Lint passed, 35 Python files already formatted |
| `node --check src/arc/entrypoints/playground/playground.js` | 0 | JavaScript syntax passed |
| `arc search "reciprocal rank fusion" --top-k 3 --trace` with the field notes | 0 | First hit `playground://rrf`, three positive BM25 scores, BM25 and assembly stages |
| `python scripts/container-smoke.py` against the default local wheel service | 0 | Original BM25 first hit and stage trace, Playground assets and config all served |
| `python -m arc.evaluation.audit` and `python -m arc.evaluation.smoke` | 0 each | Official SciFact and WANDS inputs passed with 0 audit failures, hand-verifiable metric smoke passed |
| Markdown relative-link and benchmark cross-check | 0 | Both README tables and the SVG’s eight NDCG@10 and p95 pairs match the V0 acceptance tables |

The initial uncached dependency downloads timed out on Windows. The successful clean install used cached wheels checked against exported lockfile hashes. Docker was unavailable on the local host, so the container build and run are assigned to the existing CI job.

## Browser checks and provenance

- Headless Microsoft Edge ran the installed CPU Playground at desktop and 390 px widths. Verified the disabled comparison selector, ranked results, trace, blank-query feedback and recovery messaging for an intercepted HTTP 409. The API contract suite separately verifies a real snapshot mismatch.
- On the existing local SciFact corpus and CUDA snapshots, the browser ran all four strategies across two comparisons for the same query. For each strategy, the displayed Top-3 source IDs and order matched the live API response. Checked that the comparison stacked without horizontal overflow at 390 px.
- On the local WANDS corpus, all three product examples returned positive-scoring BM25 results from the actual product snapshot.
- The [README capture](../../../docs/assets/playground.png) uses a local FAISS index built from the 12 original ARC notes with the pinned BGE encoder. Dense and Hybrid + Rerank ran live with the pinned MiniLM model. The [CPU capture](../../../docs/assets/playground-cpu.png) uses the installed wheel and its BM25-only mode. Screenshot timings are single-request harness readings. Benchmark timing comes from the separate V0 HTTP measurements.
- GitHub’s Markdown renderer recognized both README variants. The benchmark values come from the [V0 acceptance report](../../../docs/ARC-V0-ACCEPTANCE.md). Formal ranking and latency experiments were reused as published.
