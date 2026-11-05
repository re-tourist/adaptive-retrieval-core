from dataclasses import replace

import pytest

from arc.application.ports import Candidate, Corpus, IndexCompatibility, IndexManifest
from arc.application.search import SearchQuery, SearchService
from arc.bootstrap import fake_search_service
from arc.domain.models import Entity, EntityKey, RetrievalUnit


def adapt_fixture_dataset(rows: tuple[tuple[str, str], ...]) -> Corpus:
    entities = []
    units = []
    for source_id, text in rows:
        key = EntityKey("technical", source_id, "fixture-v1")
        entities.append(Entity(key, source_id, f"fixture://third-dataset/{source_id}"))
        units.append(RetrievalUnit(f"fixture-{source_id}", key, text, "body"))
    return Corpus(tuple(entities), tuple(units))


def fixture_corpus() -> Corpus:
    return adapt_fixture_dataset((("original-id", "Retrieval contract"),))


def manifest() -> IndexManifest:
    compatibility = IndexCompatibility("fixture-v1", "fake", "1", "encoder-v1", 2, "ip", "f32")
    return IndexManifest("snapshot", compatibility, "fixture", "1", "fixture-config")


def test_dataset_adapter_fixture_and_search_contract() -> None:
    corpus = fixture_corpus()
    service = fake_search_service(corpus, manifest())
    result = service.search(SearchQuery("retrieval", "technical"))
    assert result.hits == (Candidate(corpus.units[0], 1.0),)
    # Judgments live only in the offline test, outside corpus and request.
    judged_ids = {"original-id"}
    assert {hit.unit.entity_key.entity_id for hit in result.hits} == judged_ids
    assert (result.snapshot_id, result.score_type) == ("snapshot", "fake")
    assert service.search(SearchQuery("retrieval", "product")).hits == ()


def test_retriever_is_replaceable() -> None:
    class EmptyRetriever:
        def __init__(self, snapshot: IndexManifest) -> None:
            self.manifest = snapshot

        def retrieve(self, query: str, domain: str, limit: int) -> tuple[Candidate, ...]:
            assert (query, domain, limit) == ("retrieval", "technical", 5)
            return ()

    snapshot = manifest()
    service = SearchService(EmptyRetriever(snapshot), snapshot.compatibility)
    assert service.search(SearchQuery("retrieval", "technical", 5)).hits == ()


@pytest.mark.parametrize(
    ("field", "value"),
    [("representation_type", "dense"), ("encoder_revision", "encoder-v2"), ("vector_dimension", 4)],
)
def test_incompatible_index_refused(field: str, value: str | int) -> None:
    from arc.adapters.fake import FakeRetriever

    snapshot = manifest()
    expected = replace(snapshot.compatibility, **{field: value})
    service = SearchService(FakeRetriever(fixture_corpus(), snapshot), expected)
    with pytest.raises(ValueError, match="Incompatible index"):
        service.search(SearchQuery("retrieval", "technical"))


def test_corpus_refuses_unbound_unit_and_mixed_revisions() -> None:
    corpus = fixture_corpus()
    old = replace(corpus.entities[0], key=EntityKey("technical", "original-id", "old"))
    with pytest.raises(ValueError, match="outside the corpus"):
        Corpus((old,), corpus.units)
    with pytest.raises(ValueError, match="one revision"):
        Corpus((*corpus.entities, old), corpus.units)


@pytest.mark.parametrize("top_k", [0, 101, True])
def test_invalid_query_limit_refused(top_k: int) -> None:
    with pytest.raises(ValueError, match="top_k"):
        SearchQuery("retrieval", "technical", top_k)
