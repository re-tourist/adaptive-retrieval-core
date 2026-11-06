# ARC Showcase V2 acceptance

Runtime commit `703d8e2` on `codex/arc-showcase-v2`. The branch starts at PR #3's verified head `ca3b21a`. [Design PR #4](https://github.com/re-tourist/adaptive-retrieval-core/pull/4) provides the design baseline. The implementation PR's Checks tab records the final platform and Docker jobs.

## Local checks

| Command or check | Exit | Result |
| --- | ---: | --- |
| `uv export --locked --offline`, `uv pip sync --offline --no-index --require-hashes`, `uv sync --locked --offline --no-editable` with the sparse, harness and harness-test groups | 0 each | Fresh Python 3.12.8 environment, 26 hash-verified Windows dependencies and the built ARC wheel |
| `uv run --no-sync pytest` | 0 | 25 passed, one Dense-dependent skip, one upstream TestClient deprecation warning |
| `python -m pytest -q` in the existing CUDA dependency environment | 0 | 26 passed, including Dense snapshot compatibility |
| `ruff check .`, `ruff format --check .`, `uv lock --check --offline`, `node --check` | 0 each | Lint, formatting, locked dependency resolution and browser source syntax passed |
| `ARC_DATASET=catalog arc search "small brass reading lamp" --top-k 4 --trace` | 0 | Cove, Luma, Studio and Vale in that order, matching HTTP and browser ranks |
| `python scripts/container-smoke.py` against the local installed service, with and without `--catalog` for the corresponding profile | 0 each | Real BM25 requests returned Haven for the catalog and the original sparse example for the default. The catalog smoke verified the photo response's WebP signature. |

The local Windows host has no Docker CLI. The CI workflow builds the image and runs the same HTTP smoke against both container configurations.

## Live browser evidence

- [Search desktop](../../../docs/assets/showcase-v2/search.png) and [Search 390 px](../../../docs/assets/showcase-v2/search-mobile.png) came from the clean CPU wheel. The three presets and a separate free-text query matched live API IDs and ranks. The CPU UI advertised Keyword only and disabled Compare. An unmatched query returned an actual empty hit list.
- [Compare desktop](../../../docs/assets/showcase-v2/compare.png) and [Compare 390 px](../../../docs/assets/showcase-v2/compare-mobile.png) came from the 22-item catalog with CUDA BGE, in-memory FAISS and MiniLM. The browser compared BM25 against each other strategy in turn, verified each displayed ID and rank against live API responses, and checked movement markers against the returned lists. In the pictured query, Studio moved from rank 4 to rank 3. Moss and Vale each appeared in only one of the two displayed Top-4 lists.
- Switching views preserved the query. Diagnostics opened on demand and displayed actual stage names and a matching snapshot ID. The browser verified blank input, a deliberately stale snapshot that produced a real HTTP 409, a failed connection and subsequent successful retry.
- Visually inspected all four final layouts and the cropped [README hero](../../../docs/assets/showcase-v2/hero.png). Checked photo decoding, no horizontal overflow, and paired photo alignment at 390 px. Iteration shortened the homepage example, hid redundant attributes and unchanged-rank badges on narrow comparison, aligned strategy selectors, and cropped the hero to search and products.

The [Showcase guide](../../../docs/SHOWCASE.md) documents the catalog and generated image provenance. The demo is independent of [V0 formal results](../../../docs/ARC-V0-ACCEPTANCE.md), which are reused as published. The original benchmark loaders, inputs, evaluation, fusion and rerank logic are outside the V2 diff. BM25's positive-score option applies only to the new catalog and has its own snapshot identity. Demo queries and their per-request diagnostic timings support interface review, while the V0 report covers formal evaluation.
