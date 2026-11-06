# Run ARC locally

ARC serves a browser Playground, JSON API and CLI. The bundled homewares catalog runs on CPU with BM25 and requires no model, index download, or dataset download. You can also load a local SciFact or WANDS snapshot.

Clone the repository and enter its root directory.

```sh
git clone https://github.com/re-tourist/adaptive-retrieval-core.git
cd adaptive-retrieval-core
```

## Start with uv

Use [uv](https://docs.astral.sh/uv/) and run these commands from the repository root. The lockfile pins the environment.

```sh
uv python install 3.12
uv sync --locked --group sparse --group harness
```

| Shell | Select the homewares catalog |
| --- | --- |
| PowerShell | `$env:ARC_DATASET = "catalog"` |
| Bash | `export ARC_DATASET=catalog` |

```sh
uv run --no-sync arc serve
```

Open [Search Playground](http://127.0.0.1:8000/playground/). Try **Reading nook**, **Blanket storage**, or your own query. The catalog runs Keyword (BM25) in the base installation. The original three-document sample remains the default when `ARC_DATASET` is omitted. Use `ARC_DATASET=playground` for the 12 ARC field notes. [Catalog contents and photo provenance](SHOWCASE.md)

## Start with Docker

```sh
docker build --tag arc:v0 .
docker run --rm -e ARC_DATASET=catalog -p 127.0.0.1:8000:8000 arc:v0
```

Open the same local Playground URL. To check the running catalog container from another terminal, run `python scripts/container-smoke.py http://127.0.0.1:8000 --catalog`.

## CLI and API

```sh
uv run --no-sync arc search "small brass reading lamp" --top-k 4 --trace
```

Use [interactive OpenAPI](http://127.0.0.1:8000/docs), or send this JSON to `POST /search`:

```json
{"query":"small brass reading lamp","domain":"product","strategy_id":"bm25","top_k":4,"return_level":"unit","trace_level":"summary"}
```

- `GET /healthz` lists the active domain and strategy snapshot IDs. Use a `snapshot_id` in the request to require that exact snapshot. A mismatch returns HTTP 409.
- `filters.entity_ids` is an allowlist applied before ranking. An empty list returns no hits. Unknown filter fields return HTTP 422.
- Search returns ranked entities by default. `return_level: "unit"` adds retrieval-unit ID and position. `trace_level: "summary"` includes stage timings and item counts.

## Enable comparison in the catalog

Install the optional model runtime with `uv sync --locked --group sparse --group harness --group dense`. Keep `ARC_DATASET=catalog`, set `ARC_BGE_MODEL` to the [pinned BGE snapshot](https://huggingface.co/BAAI/bge-small-en-v1.5/tree/5c38ec7c405ec4b44b94cc5a9bb96e735b38267a), and restart `arc serve`. With `ARC_DENSE_INDEX` unset, ARC builds the 22-document FAISS index in memory. Set `ARC_MINILM_MODEL` to the [pinned MiniLM snapshot](https://huggingface.co/cross-encoder/ms-marco-MiniLM-L6-v2/tree/233902d25c440f23af6f7d6e94d2946bac0bee0a) to add reranking. `ARC_DEVICE` defaults to `cpu`. Use `cuda:0` with a verified CUDA runtime.

Choose **Compare** to run the current query against two available strategies. ARC pins the advertised snapshots and runs both requests in sequence. “Only here” means an item is absent from the other returned list at the displayed depth. **Retrieval details** shows per-request timings, stage counts and identifiers. These timings exclude browser and network time.

## Load SciFact or WANDS

Follow the official data and pinned-model instructions in [Reproduce V0](REPRODUCING.md). Set the variables below in the same shell before running `arc serve`. Switch datasets by restarting the service with matching inputs.

| Variable | Value |
| --- | --- |
| `ARC_DATASET` | `scifact` (technical) or `wands` (product) |
| `ARC_DATA` | Local path to the official SciFact directory or WANDS TSV directory |
| `ARC_BGE_MODEL` | Pinned BGE snapshot directory |
| `ARC_DENSE_INDEX` | Matching trusted M1 E2 directory with `index.faiss`, `index_manifest.json` and `entity_ids.json` |
| `ARC_MINILM_MODEL` | Pinned MiniLM snapshot directory |
| `ARC_DEVICE` | `cpu` (default) or `cuda:0` |

For Dense, Hybrid and MiniLM, install `uv sync --locked --group sparse --group harness --group dense`. The Windows/Linux lock uses CUDA 12.6 PyTorch. Check the runtime before selecting CUDA. Set BGE and the index together to add Dense and Hybrid. Add MiniLM to enable Hybrid + Rerank.

The Playground uses text cards for SciFact and WANDS. Catalog photos are scoped to the bundled original products.

Use local, public or authorized corpora. See [Engineering](ENGINEERING.md) for boundaries and [V0 acceptance](ARC-V0-ACCEPTANCE.md) for measured results.
