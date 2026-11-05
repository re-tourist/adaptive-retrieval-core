from collections import defaultdict
from collections.abc import Sequence
from math import isfinite

from arc.application.ports import Candidate
from arc.domain.models import EntityKey, RetrievalUnit


def reciprocal_rank_fusion(*branches: Sequence[Candidate]) -> tuple[Candidate, ...]:
    """Fuse each branch's first 100 unique entities with RRF k=60."""
    scores: dict[EntityKey, float] = defaultdict(float)
    units: dict[EntityKey, RetrievalUnit] = {}
    for branch in branches:
        seen: set[EntityKey] = set()
        for rank, candidate in enumerate(branch[:100], 1):
            key = candidate.unit.entity_key
            if key in seen:
                raise ValueError("RRF branch has duplicate entities")
            seen.add(key)
            units.setdefault(key, candidate.unit)
            if units[key] != candidate.unit:
                raise ValueError("RRF branches disagree on an entity's retrieval unit")
            scores[key] += 1 / (60 + rank)
    ordered = sorted(scores, key=lambda key: (-scores[key], key))
    return tuple(Candidate(units[key], scores[key]) for key in ordered[:100])


def rerank_prefix(ranking: Sequence[Candidate], scores: Sequence[float]) -> tuple[Candidate, ...]:
    """Replace ordering and scores only for the first 50 items."""
    prefix = ranking[:50]
    if len(scores) != len(prefix) or any(not isfinite(score) for score in scores):
        raise ValueError("Reranker must return one finite score per prefix item")
    reranked = sorted(
        (Candidate(hit.unit, score) for hit, score in zip(prefix, scores, strict=True)),
        key=lambda hit: (-hit.score, hit.unit.entity_key),
    )
    return (*reranked, *ranking[50:])
