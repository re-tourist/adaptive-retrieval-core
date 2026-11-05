# M3 acceptance — PASS

The Python harness, installed CLI and FastAPI endpoints share the same retrieval adapters and ranking rules. The online path reads only the corpus and verified model/index snapshots. In a fresh locked Windows CPU environment, the installed wheel passed CLI and loopback HTTP smoke, with 23 tests passing and the optional dense snapshot test skipped. The locked CUDA environment passed all 24 tests. Ruff lint and formatting passed. Starlette reported a test-client deprecation warning for httpx; the runtime HTTP smoke uses standard-library HTTP.

Both official corpora passed online Top-10 parity against frozen dev Runfiles for all four strategies. Each strategy also passed a hard filter targeting an entity deep in its reference candidate list. Requests selected the expected snapshot and produced stage-level Trace data. The test used 10 fixed dev queries × 3 repetitions per strategy, two warmups per strategy, sequential fresh connections over localhost, and no quality tuning.

| Dataset | Strategy | Measured requests | HTTP p50 (ms) | HTTP p95 (ms) |
|---|---|---:|---:|---:|
| scifact | E1 | 30 | 25.90 | 35.73 |
| scifact | E2 | 30 | 29.14 | 47.05 |
| scifact | E3 | 30 | 42.52 | 65.21 |
| scifact | E4 | 30 | 291.94 | 338.70 |
| wands | E1 | 30 | 48.55 | 76.89 |
| wands | E2 | 30 | 30.61 | 41.29 |
| wands | E3 | 30 | 57.08 | 68.89 |
| wands | E4 | 30 | 373.17 | 416.11 |

Measured on Windows 11 and the RTX 4060 Laptop, CUDA 12.6, with CPU BM25 and exact CPU FAISS. Startup was 21.89 s for SciFact and 30.14 s for WANDS. Full stage medians, snapshots, commands and hashes are in [checks.json](checks.json). These figures exclude server load/concurrency experiments. Target server performance is **BLOCKED** because no target server was available.

[GitHub Actions run 42035615364](https://github.com/re-tourist/adaptive-retrieval-core/actions/runs/42035615364) passed on Windows and Ubuntu and actually built and started the CPU Docker image. The smoke test queried the running container over HTTP. The first image built successfully but a startup connection reset escaped the readiness loop. The fixed probe passed on rerun. The image includes the CPU demo and Web harness. The official corpora, models and index artifacts stay outside the build context.
