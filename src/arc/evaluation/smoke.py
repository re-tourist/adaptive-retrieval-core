"""Emit deterministic metric checks on hand-verifiable, synthetic rankings."""

import argparse
from pathlib import Path

from arc.evaluation.audit import write_json
from arc.evaluation.metrics import evaluate
from arc.evaluation.runfile import rank_scores, read_run, render_run


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    cases = (
        ("scifact", {"positive": 1}, [("unjudged", 2), ("positive", 1)]),
        (
            "wands",
            {"exact": 2, "partial": 1, "negative": 0},
            [("partial", 4), ("unjudged", 3), ("exact", 2), ("negative", 1)],
        ),
    )
    results = {"synthetic": True, "cases": {}}
    for name, judgments, scores in cases:
        qrels = {"query": judgments, "empty": {}}
        entities = {entity for entity, _ in scores}
        rows = rank_scores("query", scores, "synthetic")
        text = render_run(rows, set(qrels), entities)
        (args.output / f"{name}.trec").write_text(text, encoding="utf-8", newline="\n")
        parsed = read_run(text.splitlines(), set(qrels), entities)
        macro, by_query = evaluate(parsed, qrels, entities, wands=name == "wands")
        results["cases"][name] = {"macro": macro, "by_query": by_query}
    write_json(args.output / "m0_smoke_metrics.json", results)


if __name__ == "__main__":
    main()
