from itertools import combinations
from statistics import fmean

from arc.evaluation.metrics import evaluate
from arc.evaluation.runfile import RunRow


def disputed_sensitivity(
    runs: dict[str, tuple[RunRow, ...]],
    qrels: dict[str, dict[str, int]],
    entity_ids: set[str],
    ledger: list[dict],
) -> dict:
    affected = [row for row in ledger if row["query_id"] in qrels]
    if len({row["query_id"] for row in affected}) != len(affected):
        raise ValueError("Sensitivity bounds require at most one disputed pair per query")
    scenarios = {"main": qrels}
    for name, endpoint in (("observed_low", 0), ("observed_high", -1)):
        amended = qrels.copy()
        for row in affected:
            qid, eid = row["query_id"], row["entity_id"]
            if eid not in entity_ids or eid in qrels[qid]:
                raise ValueError("Disputed pair must be valid and absent from main Qrels")
            amended[qid] = {**qrels[qid], eid: row["grades"][endpoint]}
        scenarios[name] = amended

    outcomes = {}
    by_scenario = {}
    for scenario, judgments in scenarios.items():
        outcomes[scenario] = {}
        by_scenario[scenario] = {}
        for strategy, rows in runs.items():
            macro, per_query = evaluate(rows, judgments, entity_ids, wands=True)
            outcomes[scenario][strategy] = macro["NDCG@10"]
            by_scenario[scenario][strategy] = per_query

    pairs = {}
    for left, right in combinations(sorted(runs), 2):
        by_query = {}
        for qid in sorted(qrels):
            by_query[qid] = {
                name: scores[right][qid]["NDCG@10"] - scores[left][qid]["NDCG@10"]
                for name, scores in by_scenario.items()
            }
        bounds = [
            sorted((deltas["observed_low"], deltas["observed_high"]))
            for deltas in by_query.values()
        ]
        low, high = (fmean(column) for column in zip(*bounds, strict=True))
        main = fmean(delta["main"] for delta in by_query.values())
        pairs[f"{right}-{left}"] = {
            "mean_paired_delta": {
                name: fmean(delta[name] for delta in by_query.values()) for name in scenarios
            },
            "mixed_endpoint_delta_bounds": [low, high],
            "direction_strictly_stable": (main > 0 and low > 0) or (main < 0 and high < 0),
            "affected_queries": {row["query_id"]: by_query[row["query_id"]] for row in affected},
        }
    return {"disputed_pairs": len(affected), "ndcg@10": outcomes, "pairs": pairs}
