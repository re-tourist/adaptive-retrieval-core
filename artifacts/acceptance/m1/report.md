# M1 acceptance — PASS

E1 and E2 ran through the same SearchService on both official full corpora, with the admitted splits and Qrels. E1 rebuilt each CPU index in a clean locked sparse environment. E2 built FAISS IndexFlatIP snapshots with GPU BGE encoding and replayed every dev/test query against the checksum-verified saved indexes. Both strategies reproduced Runfiles and per-query metrics byte for byte within their locked environments. BM25 index serialization varied across independent builds; the artifact hashes identify the canonical snapshot.

| Dataset | Strategy | Test queries | NDCG@10 | Recall@100 | Judged@10 |
|---|---|---:|---:|---:|---:|
| scifact | E1 | 300 | 0.641400 | 0.869222 | — |
| scifact | E2 | 300 | 0.712707 | 0.941667 | — |
| wands | E1 | 400 | 0.648530 | 0.343283 | 0.789500 |
| wands | E2 | 400 | 0.705657 | 0.360762 | 0.835500 |

WANDS uses the ARC-WANDS-400 custom split and observed recall. Unjudged and disputed items are distinct from confirmed negatives. E2−E1 paired NDCG@10 is +0.071307 on SciFact (2,000-resample 95% interval +0.034427 to +0.107701) and +0.057127 on WANDS (+0.036599 to +0.078607). On the 13 disputed WANDS test pairs, the mixed-endpoint delta bounds are [+0.057206, +0.057376]. Both preserve the E2 advantage.

| Dataset | Strategy | Build + save (s) | Index bytes | Test retrieval p50 / p95 (ms) | Truncated docs |
|---|---|---:|---:|---:|---:|
| scifact | E1 | 2.29 | 6,130,550 | 2.60 / 4.94 | 0 |
| scifact | E2 | 101.00 | 7,961,133 | 41.67 / 77.89 | 455 |
| wands | E1 | 10.07 | 54,411,720 | 20.62 / 31.23 | 0 |
| wands | E2 | 663.69 | 66,038,829 | 15.18 / 19.86 | 27,650 |

Windows 11, Python 3.12.8, RTX 4060 Laptop 8,188 MiB, NVIDIA driver 566.24. E2 used PyTorch 2.8.0+cu126, Sentence Transformers 5.7.0, float32, batch 32 and CPU exact FAISS. BGE inputs were capped at 512 tokens. Query encoding is included in E2 retrieval latency; offline corpus encoding is included only in build. These are single-query observations on a shared laptop, and do not establish server or load-test performance. The host CPU E2 SciFact cross-check matched the CUDA quality metrics but is separate from the canonical measurements.

See [checks.json](checks.json) for commands, results, Qrels/Runfile bindings, model and index fingerprints, per-query file hashes, and ADR-003 sensitivities. Raw evidence stays local under `artifacts/m1/e1-locked`, `artifacts/m1/e2-locked-cuda` and their separate repeat/replay roots.
