from arc.application.ports import Candidate, Corpus, IndexManifest, TraceHook


class FakeRetriever:
    """Deterministic fixture adapter for exercising the search port."""

    def __init__(self, corpus: Corpus, manifest: IndexManifest) -> None:
        self._corpus = corpus
        self._manifest = manifest

    @property
    def manifest(self) -> IndexManifest:
        return self._manifest

    def retrieve(
        self,
        query: str,
        domain: str,
        limit: int,
        *,
        allowed_ids: frozenset[str] | None = None,
        observe: TraceHook | None = None,
    ) -> tuple[Candidate, ...]:
        matching = (
            Candidate(unit, 1.0)
            for unit in self._corpus.units
            if unit.entity_key.domain == domain
            and (allowed_ids is None or unit.entity_key.entity_id in allowed_ids)
            and query.casefold() in unit.text.casefold()
        )
        return tuple(matching)[:limit]
