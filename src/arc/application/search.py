from dataclasses import dataclass

from arc.application.ports import Candidate, IndexCompatibility, Retriever


@dataclass(frozen=True, slots=True)
class SearchQuery:
    text: str
    domain: str
    top_k: int = 10

    def __post_init__(self) -> None:
        if not self.text.strip() or not self.domain.strip():
            raise ValueError("Query text and domain must be nonempty")
        if type(self.top_k) is not int or not 1 <= self.top_k <= 100:
            raise ValueError("top_k must be an integer between 1 and 100")


@dataclass(frozen=True, slots=True)
class SearchResult:
    hits: tuple[Candidate, ...]
    snapshot_id: str
    score_type: str


class SearchService:
    def __init__(self, retriever: Retriever, expected: IndexCompatibility) -> None:
        self._retriever = retriever
        self._expected = expected

    def search(self, query: SearchQuery) -> SearchResult:
        manifest = self._retriever.manifest
        manifest.require_compatible(self._expected)
        hits = self._retriever.retrieve(query.text, query.domain, query.top_k)
        if len(hits) > query.top_k or any(
            hit.unit.entity_key.domain != query.domain for hit in hits
        ):
            raise ValueError("Retriever violated query scope or candidate limit")
        return SearchResult(hits, manifest.index_id, manifest.compatibility.representation_type)
