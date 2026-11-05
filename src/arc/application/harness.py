from dataclasses import dataclass, replace
from hashlib import sha256
from threading import Lock
from time import perf_counter
from typing import Protocol
from uuid import uuid4

from arc.application.ports import Candidate
from arc.application.ranking import reciprocal_rank_fusion, rerank_prefix
from arc.application.search import SearchQuery, SearchService
from arc.domain.models import Entity, EntityKey

STRATEGIES = ("bm25", "dense", "hybrid", "hybrid_rerank")


class Reranker(Protocol):
    revision: str

    def score(self, query: str, passages: list[str]) -> tuple[list[float], int]: ...


class SnapshotMismatch(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class Stage:
    name: str
    elapsed_ms: float
    count: int


@dataclass(frozen=True, slots=True)
class Hit:
    entity: Entity
    candidate: Candidate
    rank: int


@dataclass(frozen=True, slots=True)
class SearchResponse:
    hits: tuple[Hit, ...]
    snapshot_id: str
    strategy_id: str
    score_type: str
    trace_id: str
    elapsed_ms: float
    stages: tuple[Stage, ...]


class SearchHarness:
    def __init__(
        self,
        domain: str,
        entities: dict[EntityKey, Entity],
        sparse: SearchService,
        dense: SearchService | None = None,
        reranker: Reranker | None = None,
    ) -> None:
        self.domain = domain
        self._entities = entities
        self._sparse = sparse
        self._dense = dense
        self._reranker = reranker
        self._lock = Lock()
        if dense and (
            dense.manifest.compatibility.dataset_fingerprint
            != sparse.manifest.compatibility.dataset_fingerprint
        ):
            raise ValueError("Sparse and dense snapshots use different corpora")
        self._snapshots = {"bm25": sparse.manifest.index_id}
        if dense:
            self._snapshots["dense"] = dense.manifest.index_id
            combined = f"{sparse.manifest.index_id}|{dense.manifest.index_id}|rrf60"
            self._snapshots["hybrid"] = "hybrid-" + sha256(combined.encode()).hexdigest()
            if reranker:
                config = f"{combined}|{reranker.revision}|prefix50"
                self._snapshots["hybrid_rerank"] = "rerank-" + sha256(config.encode()).hexdigest()

    @property
    def snapshots(self) -> dict[str, str]:
        return self._snapshots.copy()

    def search(
        self, query: SearchQuery, strategy: str = "bm25", *, snapshot_id: str | None = None
    ) -> SearchResponse:
        started = perf_counter()
        if query.domain != self.domain:
            raise KeyError("Domain unavailable")
        if strategy not in self._snapshots:
            raise KeyError("Strategy unavailable in the configured snapshot")
        current = self._snapshots[strategy]
        if snapshot_id is not None and snapshot_id != current:
            raise SnapshotMismatch("Requested snapshot is unavailable")
        stages: list[Stage] = []

        def observe(name: str, elapsed: float, count: int) -> None:
            stages.append(Stage(name, elapsed, count))

        with self._lock:
            hybrid = strategy.startswith("hybrid")
            request = replace(query, top_k=100) if hybrid else query
            if strategy != "dense":
                step = perf_counter()
                sparse = self._sparse.search(request).hits
                observe("bm25", (perf_counter() - step) * 1000, len(sparse))
            if strategy != "bm25":
                dense = self._dense.search(request, observe=observe).hits
            if hybrid:
                step = perf_counter()
                ranking = reciprocal_rank_fusion(sparse, dense)
                observe("rrf", (perf_counter() - step) * 1000, len(ranking))
                if strategy == "hybrid_rerank" and ranking:
                    step = perf_counter()
                    scores, _ = self._reranker.score(
                        query.text, [h.unit.text for h in ranking[:50]]
                    )
                    ranking = rerank_prefix(ranking, scores)
                    observe("minilm", (perf_counter() - step) * 1000, len(scores))
            else:
                ranking = sparse if strategy == "bm25" else dense
            step = perf_counter()
            hits = tuple(
                Hit(
                    self._entities[hit.unit.entity_key],
                    Candidate(hit.unit, float(101 - rank)) if strategy == "hybrid_rerank" else hit,
                    rank,
                )
                for rank, hit in enumerate(ranking[: query.top_k], 1)
            )
            observe("assemble", (perf_counter() - step) * 1000, len(hits))

        score_type = {
            "bm25": "bm25",
            "dense": "cosine",
            "hybrid": "rrf",
            "hybrid_rerank": "rank",
        }[strategy]
        return SearchResponse(
            hits,
            current,
            strategy,
            score_type,
            uuid4().hex,
            (perf_counter() - started) * 1000,
            tuple(stages),
        )
