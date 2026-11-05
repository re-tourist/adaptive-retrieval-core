from math import log2
from pathlib import Path

import pytest

from arc.adapters.datasets.wands import load_wands
from arc.evaluation.metrics import evaluate
from arc.evaluation.qrels import audit_qrels, wands_split
from arc.evaluation.runfile import RunRow, rank_scores, read_run, render_run

ENTITIES = {"exact", "partial", "negative", "unjudged"}


def test_wands_hand_calculation() -> None:
    qrels = {"q": {"exact": 2, "partial": 1, "negative": 0}, "empty": {}}
    ranked = rank_scores(
        "q", [("partial", 4), ("unjudged", 3), ("exact", 2), ("negative", 1)], "smoke"
    )
    encoded = render_run(ranked, set(qrels), ENTITIES)
    parsed = read_run(encoded.splitlines(), set(qrels), ENTITIES)
    macro, per_query = evaluate(parsed, qrels, ENTITIES, wands=True)
    # Gain 1 at rank 1 and gain 3 at rank 3. Ideal puts gain 3 first and gain 1 second.
    expected = (1 + 3 / 2) / (3 + 1 / log2(3))
    assert per_query["q"] == pytest.approx(
        {"NDCG@10": expected, "Observed-Recall@100": 1, "Judged@10": 3 / 10}
    )
    assert macro == pytest.approx(
        {"NDCG@10": expected / 2, "Observed-Recall@100": 1 / 2, "Judged@10": 3 / 20}
    )


def test_scifact_hand_calculation_and_empty_run() -> None:
    qrels = {"q": {"exact": 1}, "missing-judgments": {}}
    ranked = rank_scores("q", [("unjudged", 2), ("exact", 1)], "smoke")
    macro, per_query = evaluate(ranked, qrels, ENTITIES, wands=False)
    # One positive at rank 2 with ideal rank 1, and one zero-valued query.
    assert per_query["q"] == pytest.approx({"NDCG@10": 1 / log2(3), "Recall@100": 1})
    assert macro == pytest.approx({"NDCG@10": 1 / (2 * log2(3)), "Recall@100": 1 / 2})
    assert evaluate([], qrels, ENTITIES, wands=False)[0] == {"NDCG@10": 0, "Recall@100": 0}


def test_tie_break_and_invalid_runs() -> None:
    tied = rank_scores("dev", [("partial", 1), ("exact", 1)], "smoke")
    assert [row.entity_id for row in tied] == ["exact", "partial"]
    with pytest.raises(ValueError, match="outside its split"):
        evaluate(tied, {"test": {}}, ENTITIES, wands=False)
    with pytest.raises(ValueError, match="Duplicate"):
        render_run([*tied, RunRow("dev", "exact", 3, 0, "smoke")], {"dev"}, ENTITIES)
    with pytest.raises(ValueError, match="contiguous"):
        read_run(["dev Q0 exact 2 0 smoke"], {"dev"}, ENTITIES)
    with pytest.raises(ValueError, match="score"):
        read_run(["dev Q0 exact 1 nan smoke"], {"dev"}, ENTITIES)


def test_qrels_conflict_cannot_be_scored() -> None:
    qrels, audit = audit_qrels(
        [("q", "exact", 2), ("q", "exact", 2), ("q", "exact", 0), ("q", "orphan", 1)],
        {"q"},
        ENTITIES,
    )
    assert qrels is None
    assert audit.identical_repeats == 1
    assert audit.conflicts == {("q", "exact"): (0, 2)}
    assert audit.unknown_entities == ("orphan",)
    clean, _ = audit_qrels([("q", "exact", 2)] * 2, {"q", "empty"}, ENTITIES)
    assert clean == {"q": {"exact": 2}, "empty": {}}


def test_split_is_reproducible() -> None:
    ids = [str(i) for i in range(480)]
    dev, test = wands_split(ids)
    assert (dev, test) == wands_split(reversed(ids))
    assert (len(dev), len(test)) == (80, 400)
    assert not set(dev).intersection(test)
    assert set(dev) | set(test) == set(ids)


def test_wands_official_header_and_text_boundary(tmp_path: Path) -> None:
    (tmp_path / "product.csv").write_text(
        "product_id\tproduct_name\tproduct_class\tcategory hierarchy\tproduct_features"
        "\tproduct_description\taverage_rating\n001\tChair\tSeating\tHome\tOak\t\t99\n",
        encoding="utf-8",
    )
    (tmp_path / "query.csv").write_text(
        "query_id\tquery\tquery_class\n02\tOak chair\tIGNORE-ME\n", encoding="utf-8"
    )
    (tmp_path / "label.csv").write_text(
        "query_id\tproduct_id\tlabel\n02\t001\tExact\n", encoding="utf-8"
    )
    dataset = load_wands(tmp_path)
    assert dataset.queries == {"02": "Oak chair"}
    assert dataset.judgments == {"all": (("02", "001", 2),)}
    unit = dataset.corpus.units[0]
    assert unit.unit_id == unit.entity_key.entity_id == "001"
    assert unit.text.splitlines() == [
        "product_name: Chair",
        "product_class: Seating",
        "category_hierarchy: Home",
        "product_features: Oak",
        "product_description: ",
    ]
    assert dataset.empty_fields["product_description"] == 1


def test_disputed_policy_requires_exact_conflict_set_and_grades() -> None:
    rows = [("q", "exact", 2), ("q", "exact", 1), ("q", "partial", 1), ("q", "partial", 1)]
    policy = {("q", "exact"): (1, 2)}
    qrels, audit = audit_qrels(rows, {"q"}, ENTITIES, disputed=policy)
    assert qrels == {"q": {"partial": 1}}
    assert audit.conflicts == policy and audit.identical_repeats == 1
    assert audit_qrels(rows, {"q"}, ENTITIES, disputed={("q", "exact"): (0, 2)})[0] is None
    assert audit_qrels(rows[1:], {"q"}, ENTITIES, disputed=policy)[0] is None
    changed = [*rows, ("q", "partial", 2)]
    assert audit_qrels(changed, {"q"}, ENTITIES, disputed=policy)[0] is None
