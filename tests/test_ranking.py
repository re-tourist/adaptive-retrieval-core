import pytest

from arc.application.ports import Candidate
from arc.application.ranking import reciprocal_rank_fusion, rerank_prefix
from arc.domain.models import EntityKey, RetrievalUnit


def candidate(key: str) -> Candidate:
    unit = RetrievalUnit(key, EntityKey("technical", key, "1"), key, "body")
    return Candidate(unit, 99)


def test_rrf_uses_ranks_and_breaks_ties_by_entity() -> None:
    a, b, c = map(candidate, ("a", "b", "c"))
    result = reciprocal_rank_fusion((b, c), (a, c))
    assert [x.unit.unit_id for x in result] == ["c", "a", "b"]
    assert [x.score for x in result] == pytest.approx([2 / 62, 1 / 61, 1 / 61])
    with pytest.raises(ValueError, match="duplicate"):
        reciprocal_rank_fusion((a, a))


def test_rerank_keeps_full_set_and_tail() -> None:
    pool = tuple(candidate(f"{i:03d}") for i in range(100))
    result = rerank_prefix(pool, list(range(50)))
    assert [x.unit for x in result[:50]] == [x.unit for x in reversed(pool[:50])]
    assert result[50:] == pool[50:]
    assert {x.unit.entity_key for x in result} == {x.unit.entity_key for x in pool}
    with pytest.raises(ValueError, match="finite score"):
        rerank_prefix(pool, [float("nan")] * 50)
