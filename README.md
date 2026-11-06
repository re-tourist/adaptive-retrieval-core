# Adaptive Retrieval Core

**One search API for keyword, dense, hybrid, and reranked retrieval.** See how each strategy ranks the same query.

[Run locally with uv](docs/QUICKSTART.md#start-with-uv) · [Run locally with Docker](docs/QUICKSTART.md#start-with-docker) · [Documentation](docs/INDEX.md) · [中文](README.zh-CN.md)

![Live ARC search for a small brass reading lamp, with four ranked product cards](docs/assets/showcase-v2/hero.png)

*Live BM25 results from the bundled 22-product fictional catalog. Product photos are generated. The CPU demo runs with the included assets.* [Screenshot: strategy comparison](docs/assets/showcase-v2/compare.png)

## What you can inspect

- Query the same corpus from the Playground, CLI, or FastAPI. Results retain source IDs and rank.
- Load BGE and a compatible FAISS index for Dense and Hybrid. Add MiniLM for reranking. Compare two available strategies on one query and expand the retrieval details when needed.

## V0 benchmark

**SciFact:** Dense had the highest observed NDCG@10 (0.712707). **WANDS:** Hybrid + Rerank led at 0.744195 versus 0.726482 for Hybrid. On WANDS, adding reranking increased serial loopback HTTP p95 from 68.89 to 416.11 ms.

WANDS uses ARC’s custom 80/400 split and incomplete relevance judgments. Latencies come from a Windows 11 laptop with an RTX 4060 GPU. V0 is scoped to local use and evaluation. Production access control, tenant isolation, and concurrent capacity are outside its acceptance scope. [Full benchmark and conditions](docs/ARC-V0-ACCEPTANCE.md)

[Architecture](docs/ENGINEERING.md) · [Reproduce V0](docs/REPRODUCING.md) · [Demo catalog and image provenance](docs/SHOWCASE.md) · [Releases](https://github.com/re-tourist/adaptive-retrieval-core/releases)
