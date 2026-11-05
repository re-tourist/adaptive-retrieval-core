# Run ARC locally

ARC serves a browser Playground, JSON API and CLI. The optional field-notes corpus contains 12 original ARC articles and runs with real CPU BM25. You can also load a local SciFact or WANDS snapshot.

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

| Shell | Select the field-notes corpus |
| --- | --- |
| PowerShell | `$env:ARC_DATASET = "playground"` |
| Bash | `export ARC_DATASET=playground` |

```sh
uv run --no-sync arc serve
```

Open [Search Playground](http://127.0.0.1:8000/playground/) while the local service is running. Try **reciprocal rank fusion** or **dense vector search** and inspect the ranked hits and stage trace. With no `ARC_DATASET` set, ARC uses its original three-document CPU sample. [CPU Playground screenshot](assets/playground-cpu.png)

## Start with Docker

```sh
docker build --tag arc:v0 .
docker run --rm -e ARC_DATASET=playground -p 127.0.0.1:8000:8000 arc:v0
```

Open the same local Playground URL. The image installs CPU BM25 and serves the bundled assets. To run the original container smoke check, start the image without `-e ARC_DATASET=playground` and run `python scripts/container-smoke.py http://127.0.0.1:8000` in another terminal.

## CLI and API

```sh
uv run --no-sync arc search "BM25" --top-k 3 --trace
```

Use [interactive OpenAPI](http://127.0.0.1:8000/docs), or send this JSON to `POST /search`:

```json
{"query":"BM25","domain":"technical","strategy_id":"bm25","top_k":3,"return_level":"unit","trace_level":"summary"}
```

- `GET /healthz` lists the active domain and strategy snapshot IDs. Use a `snapshot_id` in the request to require that exact snapshot. A mismatch returns HTTP 409.
- `filters.entity_ids` is an allowlist applied before ranking. An empty list returns no hits. Unknown filter fields return HTTP 422.
- Search returns ranked entities by default. `return_level: "unit"` adds retrieval-unit ID and position. `trace_level: "summary"` includes stage timings and item counts.

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

The Playground only offers strategies from the current snapshot configuration. To compare two, select a primary and a comparison strategy, then submit one query. ARC runs both in sequence. Use ranks and source IDs to compare results. Timing shown in each card comes from the harness for that request, in milliseconds. It excludes the browser and network.

Use local, public or authorized corpora. See [Engineering](ENGINEERING.md) for boundaries and [V0 acceptance](ARC-V0-ACCEPTANCE.md) for measured results.
