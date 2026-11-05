from dataclasses import dataclass

from arc.application.ports import Candidate, IndexCompatibility, IndexManifest, Retriever, TraceHook


@dataclass(frozen=True, slots=True)
class SearchQuery:
    text: str
    domain: str
    top_k: int = 10
    entity_ids: frozenset[str] | None = None

    def __post_init__(self) -> None:
        if not self.text.strip() or not self.domain.strip():
            raise ValueError("Query text and domain must be nonempty")
        if type(self.top_k) is not int or not 1 <= self.top_k <= 100:
            raise ValueError("top_k must be an integer between 1 and 100")
        if self.entity_ids is not None and (
            not isinstance(self.entity_ids, frozenset)
            or any(not isinstance(value, str) or not value.strip() for value in self.entity_ids)
        ):
            raise ValueError("entity_ids must be a frozenset of nonblank IDs")


@dataclass(frozen=True, slots=True)
class SearchResult:
    hits: tuple[Candidate, ...]
    snapshot_id: str
    score_type: str


class SearchService:
    def __init__(self, retriever: Retriever, expected: IndexCompatibility) -> None:
        self._retriever = retriever
        self._expected = expected

    @property
    def manifest(self) -> IndexManifest:
        return self._retriever.manifest

    def search(self, query: SearchQuery, *, observe: TraceHook | None = None) -> SearchResult:
        manifest = self._retriever.manifest
        manifest.require_compatible(self._expected)
        options = {}
        if query.entity_ids is not None:
            options["allowed_ids"] = query.entity_ids
        if observe is not None:
            options["observe"] = observe
        hits = self._retriever.retrieve(query.text, query.domain, query.top_k, **options)
        if len(hits) > query.top_k or any(
            hit.unit.entity_key.domain != query.domain
            or (
                query.entity_ids is not None
                and hit.unit.entity_key.entity_id not in query.entity_ids
            )
            for hit in hits
        ):
            raise ValueError("Retriever violated query scope or candidate limit")
        return SearchResult(hits, manifest.index_id, manifest.compatibility.representation_type)
