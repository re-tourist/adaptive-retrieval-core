# M1 checkpoint — E1 and SciFact CUDA E2 verified

E1 completed two full-corpus runs for each official dataset using bm25s 0.2.14, Python 3.12.8, NumPy 1.26.4 and SciPy 1.15.2 on Windows CPU. The BM25 wheel was verified against the public lock hash. NumPy and SciPy came from the existing host runtime. A clean uv environment installed the three locked sparse wheels with hash enforcement (NumPy 2.5.4 and SciPy 1.18.1). Two locked runs reproduced each other byte for byte. Against the host stack, per-query metrics were identical, but float scores varied by at most 5.73e-6 and two WANDS test rank rows differed. Use the locked run as E1 for subsequent comparisons.

| E1 test | Queries | NDCG@10 | Recall@100 | Judged@10 |
|---|---:|---:|---:|---:|
| SciFact | 300 | 0.641400 | 0.869222 | — |
| WANDS ARC-WANDS-400 custom | 400 | 0.648530 | 0.343283 (observed) | 0.789500 |

Dev and test Runfiles and per-query metrics were byte-identical across independent runs. See [checks.json](checks.json) for index manifests, measurements, file hashes and WANDS single-model disputed-grade sensitivity. Raw Runfiles and indexes remain local under `artifacts/m1/e1-host-verification` and `artifacts/m1/e1-host-repeat`. The locked artifacts are in `artifacts/m1/e1-locked` and `artifacts/m1/e1-locked-repeat`.

The BAAI safetensors are available locally and match the pinned upstream SHA-256. An E2 CPU cross-check on all 300 SciFact test queries yielded NDCG@10 0.712707 and Recall@100 0.941667. Its paired NDCG@10 difference versus locked E1 is +0.071307 (bootstrap 95% interval +0.034427 to +0.107701). This cross-check used the host CPU PyTorch runtime. The locked Windows CUDA 12.6 environment installed 48 verified wheels, and a 32×384 BGE smoke test passed on the RTX 4060. Canonical SciFact E2 matched the CPU cross-check quality exactly. Test retrieval p50/p95 was 41.67/77.89 ms on this local machine; the index build and save took 101.00 s. WANDS CUDA E2 and verified snapshot replay remain in progress. M1 still requires the WANDS paired sensitivity comparison. These E1 CPU measurements are local, so server performance remains unverified.
