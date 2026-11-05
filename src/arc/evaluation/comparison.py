import argparse
import json
from itertools import combinations
from pathlib import Path
from random import Random
from statistics import fmean

from arc.evaluation.audit import WANDS_DISPUTED, write_json
from arc.evaluation.baselines import _checked_json, _digest
from arc.evaluation.metrics import evaluate
from arc.evaluation.runfile import read_run
from arc.evaluation.sensitivity import disputed_sensitivity


def paired_bootstrap(deltas: list[float], *, seed: int = 20261105) -> dict[str, float]:
    if not deltas:
        raise ValueError("Paired query deltas are required")
    generator = Random(seed)
    samples = sorted(fmean(generator.choices(deltas, k=len(deltas))) for _ in range(2000))
    return {"mean": fmean(deltas), "p025": samples[49], "p975": samples[1949]}


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare frozen full-corpus ARC Runfiles")
    parser.add_argument("--dataset", required=True, choices=("scifact", "wands"))
    parser.add_argument("--admission", required=True, type=Path)
    parser.add_argument("--entity-ids", required=True, type=Path)
    parser.add_argument("--run", required=True, type=Path, action="append")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if len(args.run) < 2:
        parser.error("Provide at least two frozen test Runfiles")
    wands = args.dataset == "wands"
    audit = json.loads((args.admission / "audit_report.json").read_bytes())[args.dataset]
    if audit["failures"]:
        raise ValueError("Dataset has not passed admission")
    source = json.loads((args.admission / "dataset_manifest.json").read_bytes())[args.dataset]
    qrels = _checked_json(
        args.admission / args.dataset / "test_qrels.json", source["qrels_sha256"]["test_qrels.json"]
    )
    entities = set(json.loads(args.entity_ids.read_bytes()))
    if len(entities) != audit["entities"]:
        raise ValueError("Entity inventory does not cover the admitted corpus")
    runs = {}
    metrics = {}
    run_fingerprints = {}
    for path in args.run:
        meta = json.loads((path.parent / "metrics.json").read_bytes())
        run_sha = _digest(path)
        if run_sha != meta["run_sha256"]:
            raise ValueError(f"Runfile hash mismatch: {path}")
        rows = read_run(path.read_text(encoding="utf-8").splitlines(), set(qrels), entities)
        if len(rows) != len(qrels) * 100 or {row.query_id for row in rows} != set(qrels):
            raise ValueError(f"Runfile lacks full top-100 coverage: {path}")
        tag = rows[0].tag
        if tag in runs:
            raise ValueError(f"Duplicate strategy {tag}")
        runs[tag] = rows
        run_fingerprints[tag] = run_sha
        metrics[tag] = evaluate(rows, qrels, entities, wands=wands)[1]
    results = {
        "dataset": args.dataset,
        "query_count": len(qrels),
        "entity_ids_sha256": _digest(args.entity_ids),
        "qrels_sha256": source["qrels_sha256"]["test_qrels.json"],
        "run_sha256": run_fingerprints,
        "ndcg@10_paired_bootstrap": {
            f"{right}-{left}": paired_bootstrap(
                [
                    metrics[right][qid]["NDCG@10"] - metrics[left][qid]["NDCG@10"]
                    for qid in sorted(qrels)
                ]
            )
            for left, right in combinations(sorted(runs), 2)
        },
    }
    if wands:
        ledger = _checked_json(WANDS_DISPUTED, source["disputed_ledger_sha256"])
        results["disputed_sensitivity"] = disputed_sensitivity(runs, qrels, entities, ledger)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    write_json(args.output, results)


if __name__ == "__main__":
    main()
