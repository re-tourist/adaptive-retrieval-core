from dataclasses import asdict
from pathlib import Path

import pytest

from arc.application.ports import Corpus
from arc.domain.models import Entity, EntityKey, RetrievalUnit
from arc.evaluation.audit import write_json
from arc.evaluation.baselines import _digest


def test_dense_replay_verifies_inventory_and_index_bytes(tmp_path: Path) -> None:
    faiss = pytest.importorskip("faiss")
    np = pytest.importorskip("numpy")
    pytest.importorskip("sentence_transformers")
    from arc.adapters.retrievers.dense import EMBEDDING_DIMENSION, DenseRetriever

    class FixtureEncoder:
        batch_size = 2

        def encode(self, texts: list[str]):
            vectors = np.zeros((len(texts), EMBEDDING_DIMENSION), dtype=np.float32)
            vectors[:, 0] = 1
            return vectors, 0

    key = EntityKey("technical", "one", "revision")
    corpus = Corpus(
        (Entity(key, "one", "fixture://one"),),
        (RetrievalUnit("one", key, "first", "body"),),
    )
    encoder = FixtureEncoder()
    built = DenseRetriever(corpus, "revision", encoder)
    path = tmp_path / "index.faiss"
    faiss.write_index(built.index, str(path))
    write_json(tmp_path / "entity_ids.json", ["one"])
    write_json(
        tmp_path / "index_manifest.json",
        {
            "index": asdict(built.manifest),
            "index_files_sha256": {"index.faiss": _digest(path)},
            "document_truncations": 0,
        },
    )
    replay = DenseRetriever(corpus, "revision", encoder, snapshot=tmp_path)
    assert replay.retrieve("first", "technical", 1) == built.retrieve("first", "technical", 1)
    write_json(tmp_path / "entity_ids.json", ["wrong"])
    with pytest.raises(ValueError, match="entity order"):
        DenseRetriever(corpus, "revision", encoder, snapshot=tmp_path)
    write_json(tmp_path / "entity_ids.json", ["one"])
    path.write_bytes(b"corrupt")
    with pytest.raises(ValueError, match="fingerprint mismatch"):
        DenseRetriever(corpus, "revision", encoder, snapshot=tmp_path)
