"""Original ARC field notes for the CPU playground."""

import json
from hashlib import sha256

from arc.adapters.datasets.common import make_corpus
from arc.application.ports import Corpus

NOTES = (
    (
        "bm25",
        "BM25 keyword search",
        "BM25 ranks keyword matches using term frequency, inverse document frequency and "
        "document length normalization.",
    ),
    (
        "bge",
        "BGE text embeddings",
        "Dense retrieval encodes queries and documents as vectors so related concepts can "
        "match even when the query and the document use different words.",
    ),
    (
        "faiss",
        "FAISS exact vector search",
        "The dense adapter searches a flat FAISS index over normalized vectors. Inner "
        "product on normalized vectors is equivalent to cosine similarity.",
    ),
    (
        "rrf",
        "Reciprocal rank fusion",
        "Reciprocal rank fusion (RRF) combines BM25 and dense lists by candidate rank. A document "
        "can gain credit from both lists without comparing their raw scores.",
    ),
    (
        "minilm",
        "MiniLM reranking",
        "The cross-encoder scores the query and each candidate together. After reciprocal "
        "rank fusion it reranks the first 50 hybrid candidates and preserves the tail.",
    ),
    (
        "snapshot",
        "Snapshot compatibility",
        "A dense snapshot binds the index to a corpus fingerprint, encoder revision and "
        "ordered source IDs. The service rejects incompatible snapshots.",
    ),
    (
        "filters",
        "Entity ID filtering",
        "A filter restricts candidates to an allowlist of source entity IDs before "
        "ranking. An empty allowlist yields no candidates.",
    ),
    (
        "trace",
        "Stage trace and timing",
        "A summary trace reports stage names, elapsed milliseconds and item counts. "
        "The trace omits query text, relevance labels and cross-encoder logits.",
    ),
    (
        "scores",
        "Reading retrieval scores",
        "BM25, cosine, RRF and rank encodings use different score scales. Compare result "
        "order across strategies and use each score within its own strategy.",
    ),
    (
        "metrics",
        "Ranking metrics",
        "NDCG rewards highly relevant documents near the top. Observed recall measures "
        "coverage of known relevant documents when relevance judgments are incomplete.",
    ),
    (
        "judgments",
        "Offline relevance judgments",
        "Evaluation reads queries and relevance judgments in a separate offline path. "
        "Online retrieval receives corpus content and query text.",
    ),
    (
        "units",
        "Entities and retrieval units",
        "An entity represents a source object. A retrieval unit contains searchable "
        "text and points back to the entity and its position in the source.",
    ),
)


def load_playground_corpus() -> Corpus:
    fingerprint = sha256(json.dumps(NOTES).encode()).hexdigest()
    return make_corpus(
        "playground",
        "technical",
        ((key, title, f"{title}\n{body}") for key, title, body in NOTES),
        {"field-notes": fingerprint},
    )
