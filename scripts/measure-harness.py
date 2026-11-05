import argparse
import json
from pathlib import Path
from statistics import median
from time import perf_counter
from urllib.request import Request, urlopen

from arc.adapters.datasets.wands import load_wands_queries
from arc.evaluation.audit import write_json

STRATEGIES = ("bm25", "dense", "hybrid", "hybrid_rerank")
STAGES = (
    ("bm25", "assemble"),
    ("query_encode", "faiss_search", "assemble"),
    ("bm25", "query_encode", "faiss_search", "rrf", "assemble"),
    ("bm25", "query_encode", "faiss_search", "rrf", "minilm", "assemble"),
)


def read_ranks(path: Path) -> dict[str, list[str]]:
    ranks = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        qid, _, eid, rank, *_ = line.split()
        hits = ranks.setdefault(qid, [])
        if int(rank) != len(hits) + 1:
            raise ValueError("Expected a rank-ordered ARC Runfile")
        hits.append(eid)
    return ranks


def measure(args: argparse.Namespace) -> dict:
    wands = args.dataset == "wands"
    domain = "product" if wands else "technical"
    dev = json.loads((args.admission / args.dataset / "dev_query_ids.json").read_bytes())[:10]
    if wands:
        queries = load_wands_queries(args.data)
    else:
        with (args.data / "queries.jsonl").open(encoding="utf-8") as stream:
            queries = {row["_id"]: row["text"] for row in map(json.loads, stream)}
    roots = [args.e1, args.e2, args.m2 / "e3", args.m2 / "e4"]
    references = [read_ranks(root / "dev" / "run.trec") for root in roots]
    base = args.base.rstrip("/")
    with urlopen(base + "/healthz", timeout=20) as stream:
        health = json.load(stream)
    assert health["domain"] == domain and set(health["snapshots"]) == set(STRATEGIES)

    def post(qid: str, strategy: str, **extra) -> tuple[dict, float]:
        payload = {
            "query": queries[qid],
            "domain": domain,
            "strategy_id": strategy,
            "top_k": 10,
            "trace_level": "summary",
            "snapshot_id": health["snapshots"][strategy],
            **extra,
        }
        request = Request(
            base + "/search",
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
        )
        before = perf_counter()
        with urlopen(request, timeout=60) as stream:
            result = json.load(stream)
        return result, (perf_counter() - before) * 1000

    stats = {}
    for strategy, reference, names in zip(STRATEGIES, references, STAGES, strict=True):
        for qid in dev[:2]:
            post(qid, strategy)
        scoped_id = reference[dev[0]][-1]
        filtered, _ = post(dev[0], strategy, top_k=1, filters={"entity_ids": [scoped_id]})
        assert [hit["entity_key"]["entity_id"] for hit in filtered["hits"]] == [scoped_id]
        times = []
        stage_times = {name: [] for name in names}
        for _ in range(args.repeat):
            for qid in dev:
                result, elapsed = post(qid, strategy)
                assert result["snapshot_id"] == health["snapshots"][strategy]
                ids = [hit["entity_key"]["entity_id"] for hit in result["hits"]]
                assert ids == reference[qid][:10], (strategy, qid, ids)
                assert tuple(stage["name"] for stage in result["trace"]) == names
                for stage in result["trace"]:
                    stage_times[stage["name"]].append(stage["elapsed_ms"])
                times.append(elapsed)
        ordered = sorted(times)
        stats[strategy] = {
            "queries": len(dev),
            "requests": len(times),
            "rank_parity": True,
            "hard_filter": True,
            "http_p50_ms": median(times),
            "http_p95_ms": ordered[(95 * len(times) + 99) // 100 - 1],
            "stage_p50_ms": {stage: median(values) for stage, values in stage_times.items()},
        }
    return {
        "dataset": args.dataset,
        "query_ids": dev,
        "warmup_per_strategy": 2,
        "sequential": True,
        "transport": "loopback HTTP, fresh connection per request",
        "snapshots": health["snapshots"],
        "strategies": stats,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True)
    parser.add_argument("--dataset", choices=("scifact", "wands"), required=True)
    for name in ("data", "admission", "e1", "e2", "m2", "output"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    parser.add_argument("--repeat", type=int, default=3)
    args = parser.parse_args()
    if args.repeat < 1:
        parser.error("--repeat must be positive")
    result = measure(args)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    write_json(args.output, result)
    print(json.dumps(result["strategies"], indent=2))


if __name__ == "__main__":
    main()
