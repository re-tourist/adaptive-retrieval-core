import os
from pathlib import Path

from arc.adapters.fake import FakeRetriever
from arc.application.harness import SearchHarness
from arc.application.ports import Corpus, IndexManifest
from arc.application.search import SearchService


def fake_search_service(corpus: Corpus, manifest: IndexManifest) -> SearchService:
    return SearchService(FakeRetriever(corpus, manifest), manifest.compatibility)


def configured_harness() -> SearchHarness:
    from arc.adapters.datasets.common import make_corpus
    from arc.adapters.datasets.scifact import load_scifact_corpus
    from arc.adapters.datasets.wands import load_wands_corpus
    from arc.adapters.retrievers.bm25 import BM25Retriever

    dataset = os.getenv("ARC_DATASET", "demo")
    if dataset == "demo":
        corpus = make_corpus(
            "demo",
            "technical",
            (
                ("sparse", "BM25", "BM25 uses term statistics for sparse keyword retrieval."),
                ("dense", "Dense", "Dense embeddings search a vector index."),
                ("rrf", "RRF", "Reciprocal rank fusion combines ranked candidate lists."),
            ),
            {"demo": "arc-v0-demo-1"},
        )
    elif dataset == "playground":
        from arc.adapters.datasets.playground import load_playground_corpus

        corpus = load_playground_corpus()
    else:
        loaders = {"scifact": load_scifact_corpus, "wands": load_wands_corpus}
        if dataset not in loaders:
            raise ValueError("ARC_DATASET must be demo, playground, scifact or wands")
        corpus = loaders[dataset](Path(os.environ["ARC_DATA"]))
    fingerprint = corpus.entities[0].key.revision
    sparse = BM25Retriever(corpus, fingerprint)
    sparse_service = SearchService(sparse, sparse.manifest.compatibility)
    dense_service = reranker = None
    model = os.getenv("ARC_BGE_MODEL")
    snapshot = os.getenv("ARC_DENSE_INDEX")
    mini = os.getenv("ARC_MINILM_MODEL")
    device = os.getenv("ARC_DEVICE", "cpu")
    if bool(model) != bool(snapshot) or (mini and not model):
        raise ValueError("Configure the BGE model and saved dense index together before MiniLM")
    if model and snapshot:
        from arc.adapters.retrievers.dense import BGEEncoder, DenseRetriever

        encoder = BGEEncoder(Path(model), device, 32)
        dense = DenseRetriever(corpus, fingerprint, encoder, snapshot=Path(snapshot))
        dense_service = SearchService(dense, dense.manifest.compatibility)
    if mini:
        from arc.adapters.retrievers.minilm import MiniLMReranker

        reranker = MiniLMReranker(Path(mini), device, 32)
    return SearchHarness(
        corpus.entities[0].key.domain,
        {entity.key: entity for entity in corpus.entities},
        sparse_service,
        dense_service,
        reranker,
    )
