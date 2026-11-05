import argparse
import json
from pathlib import Path
from statistics import median
from time import perf_counter

from arc.adapters.datasets.scifact import load_scifact
from arc.adapters.datasets.wands import load_wands
from arc.application.ports import Candidate
from arc.application.ranking import reciprocal_rank_fusion, rerank_prefix
from arc.evaluation.audit import write_json
from arc.evaluation.baselines import _checked_json, _digest, _p95
from arc.evaluation.metrics import evaluate
from arc.evaluation.runfile import RunRow, read_run, render_run, validate_run


def _ranked_parent(root: Path, split: str, query_ids: set[str], entities: set[str]) -> tuple:
    folder = root / split
    path = folder / "run.trec"
    digest = _digest(path)
    if digest != json.loads((folder / "metrics.json").read_bytes())["run_sha256"]:
        raise ValueError(f"Parent Runfile hash mismatch: {path}")
    rows = read_run(path.read_text(encoding="utf-8").splitlines(), query_ids, entities)
    ranking = validate_run(rows, query_ids, entities)
    if set(ranking) != query_ids or any(len(hits) != 100 for hits in ranking.values()):
        raise ValueError(f"Parent Runfile does not cover the entire split at Top-100: {path}")
    return ranking, digest


def _timings(values: list[float]) -> dict[str, float]:
    return {"p50": median(values), "p95": _p95(values)}


def run(args: argparse.Namespace) -> None:
    import torch

    from arc.adapters.retrievers.minilm import (
        MAX_LENGTH,
        MODEL_FILES,
        MODEL_REVISION,
        MiniLMReranker,
    )

    wands = args.dataset == "wands"
    dataset = (load_wands if wands else load_scifact)(args.data)
    source = json.loads((args.admission / "dataset_manifest.json").read_bytes())[args.dataset]
    audit = json.loads((args.admission / "audit_report.json").read_bytes())[args.dataset]
    if audit["failures"] or source["input_sha256"] != dataset.files:
        raise ValueError("Input does not match admitted corpus")
    queries = dataset.queries
    units = {unit.entity_key.entity_id: unit for unit in dataset.corpus.units}
    del dataset
    entities = set(units)
    for root, representation in ((args.e1, "bm25"), (args.e2, "dense")):
        meta = json.loads((root / "index_manifest.json").read_bytes())["index"]["compatibility"]
        if (
            meta["dataset_fingerprint"] != next(iter(units.values())).entity_key.revision
            or meta["representation_type"] != representation
            or json.loads((root / "entity_ids.json").read_bytes()) != sorted(entities)
        ):
            raise ValueError(f"Parent index is incompatible with admitted corpus: {root}")

    output = args.output / args.dataset
    output.mkdir(parents=True, exist_ok=False)
    model = MiniLMReranker(args.model, args.device, args.batch_size)
    write_json(
        output / "configuration.json",
        {
            "fusion": {"k": 60, "branch_depth": 100, "output_depth": 100},
            "rerank": {
                "prefix": 50,
                "revision": MODEL_REVISION,
                "sha256": MODEL_FILES,
                "max_length": MAX_LENGTH,
                "truncation": "longest_first",
                "input": "query_then_original_passage",
                "score": "float32_logits",
                "batch_size": args.batch_size,
                "seed": 20261105,
            },
            "runtime": {
                "device": args.device,
                "torch": torch.__version__,
                "cuda": torch.version.cuda,
                "gpu": torch.cuda.get_device_name(args.device)
                if args.device.startswith("cuda")
                else None,
            },
            "dev_smoke_limit": args.dev_smoke,
        },
    )

    for split in ("dev", "test") if args.split == "both" else ("dev",):
        name = f"{split}_query_ids.json"
        ids = _checked_json(args.admission / args.dataset / name, source["split_sha256"][name])
        e1, e1_hash = _ranked_parent(args.e1, split, set(ids), entities)
        e2, e2_hash = _ranked_parent(args.e2, split, set(ids), entities)
        if split == "dev":
            ids = ids[: args.dev_smoke]
        ranked = {"e3": [], "e4": []}
        diagnostic = {}
        for qid in ids:
            start = perf_counter()
            branches = [
                tuple(Candidate(units[eid], 0.0) for eid in hits) for hits in (e1[qid], e2[qid])
            ]
            e3 = reciprocal_rank_fusion(*branches)
            fusion_ms = (perf_counter() - start) * 1000
            start = perf_counter()
            scores, truncated = model.score(queries[qid], [hit.unit.text for hit in e3[:50]])
            e4 = rerank_prefix(e3, scores)
            rerank_ms = (perf_counter() - start) * 1000
            if (
                len(e3) != 100
                or {hit.unit.entity_key for hit in e3} != {hit.unit.entity_key for hit in e4}
                or e3[50:] != e4[50:]
            ):
                raise RuntimeError(f"Rerank violated fixed pool for query {qid}")
            for name, hits in (("e3", e3), ("e4", e4)):
                ranked[name].extend(
                    RunRow(
                        qid,
                        hit.unit.entity_key.entity_id,
                        rank,
                        hit.score if name == "e3" else float(101 - rank),
                        name,
                    )
                    for rank, hit in enumerate(hits, 1)
                )
            diagnostic[qid] = {
                "union_size": len(set(e1[qid]) | set(e2[qid])),
                "fusion_ms": fusion_ms,
                "rerank_ms": rerank_ms,
                "truncated_pairs": truncated,
            }

        for name, rows in ranked.items():
            directory = output / name / split
            directory.mkdir(parents=True)
            (directory / "run.trec").write_bytes(render_run(rows, set(ids), entities).encode())
        # Open Qrels only after both frozen rank files have been written.
        qrels_file = f"{split}_qrels.json"
        qrels = _checked_json(
            args.admission / args.dataset / qrels_file, source["qrels_sha256"][qrels_file]
        )
        qrels = {qid: qrels[qid] for qid in ids}
        recall_key = "Observed-Recall@100" if wands else "Recall@100"
        quality = {}
        for name, rows in ranked.items():
            directory = output / name / split
            macro, per_query = evaluate(rows, qrels, entities, wands=wands)
            quality[name] = per_query
            write_json(directory / "per_query.json", per_query)
            write_json(
                directory / "metrics.json",
                {
                    "queries": len(ids),
                    "quality": macro,
                    "run_sha256": _digest(directory / "run.trec"),
                    "parent_run_sha256": {"e1": e1_hash, "e2": e2_hash},
                },
            )
            print(f"{args.dataset}/{name}/{split}: {len(ids)} queries {macro}", flush=True)
        if any(quality["e3"][qid][recall_key] != quality["e4"][qid][recall_key] for qid in ids):
            raise RuntimeError("Fixed pool changed recall")
        write_json(
            output / f"{split}_diagnostics.json",
            {
                "checked_pools": len(ids),
                "fusion_ms": _timings([row["fusion_ms"] for row in diagnostic.values()]),
                "rerank_ms": _timings([row["rerank_ms"] for row in diagnostic.values()]),
                "truncated_pairs": sum(row["truncated_pairs"] for row in diagnostic.values()),
                "scored_pairs": 50 * len(ids),
                "per_query": diagnostic,
            },
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate RRF and fixed-prefix MiniLM reranking")
    parser.add_argument("--dataset", required=True, choices=("scifact", "wands"))
    for name in ("data", "admission", "e1", "e2", "model", "output"):
        parser.add_argument(f"--{name}", required=True, type=Path)
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument("--batch-size", default=32, type=int)
    parser.add_argument("--dev-smoke", default=10, type=int)
    parser.add_argument("--split", choices=("dev", "both"), default="dev")
    args = parser.parse_args()
    if args.dev_smoke < 1:
        parser.error("--dev-smoke must be positive")
    run(args)


if __name__ == "__main__":
    main()
