from collections.abc import Iterable
from math import log2
from statistics import fmean

from arc.evaluation.runfile import RunRow, validate_run


def _dcg(grades: Iterable[int]) -> float:
    return sum((2**grade - 1) / log2(rank + 1) for rank, grade in enumerate(grades, 1))


def evaluate(
    rows: Iterable[RunRow],
    qrels: dict[str, dict[str, int]],
    entity_ids: set[str],
    *,
    wands: bool,
) -> tuple[dict[str, float], dict[str, dict[str, float]]]:
    if not qrels:
        raise ValueError("Provide the full query split, including queries without judgments")
    ranking = validate_run(rows, set(qrels), entity_ids)
    per_query = {}
    recall_key = "Observed-Recall@100" if wands else "Recall@100"
    for qid, judgments in sorted(qrels.items()):
        hits = ranking.get(qid, ())
        ideal = _dcg(sorted(judgments.values(), reverse=True)[:10])
        positive = sum(grade > 0 for grade in judgments.values())
        metrics = {
            "NDCG@10": _dcg(judgments.get(eid, 0) for eid in hits[:10]) / ideal if ideal else 0.0,
            recall_key: sum(judgments.get(eid, 0) > 0 for eid in hits[:100]) / positive
            if positive
            else 0.0,
        }
        if wands:
            metrics["Judged@10"] = sum(eid in judgments for eid in hits[:10]) / 10
        per_query[qid] = metrics
    return (
        {key: fmean(metrics[key] for metrics in per_query.values()) for key in metrics},
        per_query,
    )
