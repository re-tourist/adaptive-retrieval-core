# M2 acceptance — PASS

Both official corpora used frozen M1 Top-100 inputs, RRF k=60 and the pinned MiniLM-L6-v2. Each split ran after a ten-query dev smoke per dataset. Independent Runfile validation checked every test query for exactly 100 distinct IDs, equal E3/E4 entity sets, unchanged ranks 51–100, and equal per-query recall.

| Dataset | Strategy | Test queries | NDCG@10 | Recall@100 | Judged@10 |
|---|---|---:|---:|---:|---:|
| scifact | E3 | 300 | 0.689995 | 0.965000 | — |
| scifact | E4 | 300 | 0.700141 | 0.965000 | — |
| wands | E3 | 400 | 0.726482 | 0.373135 | 0.870000 |
| wands | E4 | 400 | 0.744195 | 0.373135 | 0.876250 |

WANDS recall is observed against incomplete judgments using ARC-WANDS-400 custom split.

- **scifact**. E4−E3 +0.010146, 95% paired bootstrap interval [-0.020469, +0.042317]. E4 improved 58 queries, worsened 57 and left 185 unchanged. E3 retrieved no observed positive for 10 queries; fixed-pool E4 cannot recover those misses. Worst E4 query IDs and deltas are in checks.json.
- **wands**. E4−E3 +0.017713, 95% paired bootstrap interval [+0.005398, +0.030895]. E4 improved 158 queries, worsened 111 and left 131 unchanged. E3 retrieved no observed positive for 6 queries; fixed-pool E4 cannot recover those misses. Worst E4 query IDs and deltas are in checks.json.

WANDS ADR-003 E4−E3 mixed observed endpoint bounds [+0.017554, +0.017664], direction strictly stable: True. The machine evidence contains all six paired strategy comparisons and the disputed-grade scenarios.

| Dataset | Fusion p50 / p95 (ms) | MiniLM + prefix sort p50 / p95 (ms) | Truncated / scored test pairs |
|---|---:|---:|---:|
| scifact | 1.76 / 3.10 | 440.98 / 558.77 | 2,160 / 15,000 |
| wands | 1.39 / 2.50 | 383.67 / 665.73 | 12,117 / 20,000 |

Timings are incremental offline stages on the local RTX 4060 Laptop with CUDA 12.6 and float32 MiniLM, batch size 32. Upstream E1/E2 search and model load are excluded. These figures do not establish online service or server performance. For commands see the README M2 entry. [Machine evidence](checks.json) binds model, both parents and the E3/E4 Runfiles.
