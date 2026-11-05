from arc.adapters.fake import FakeRetriever
from arc.application.ports import Corpus, IndexManifest
from arc.application.search import SearchService


def fake_search_service(corpus: Corpus, manifest: IndexManifest) -> SearchService:
    return SearchService(FakeRetriever(corpus, manifest), manifest.compatibility)
