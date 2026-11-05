import json
from dataclasses import asdict
from hashlib import file_digest, sha256
from importlib.metadata import version
from pathlib import Path

import faiss
import numpy as np
import torch
from sentence_transformers import SentenceTransformer

from arc.application.ports import Candidate, Corpus, IndexCompatibility, IndexManifest

MODEL_ID = "BAAI/bge-small-en-v1.5"
MODEL_REVISION = "5c38ec7c405ec4b44b94cc5a9bb96e735b38267a"
QUERY_PREFIX = "Represent this sentence for searching relevant passages: "
MAX_LENGTH = 512
EMBEDDING_DIMENSION = 384
MODEL_FILES = {
    "1_Pooling/config.json": "d1caf60c96f5fba2157c0c26b76d80818fad6cf0b8eb5e73ec372ff9818eba5c",
    "config.json": "094f8e891b932f2000c92cfc663bac4c62069f5d8af5b5278c4306aef3084750",
    "config_sentence_transformers.json": "940d5f50db195fa6e5e6a4f122c095f77880de259d74b14a65779ed48bdd7c56",  # noqa: E501
    "modules.json": "84e40c8e006c9b1d6c122e02cba9b02458120b5fb0c87b746c41e0207cf642cf",
    "sentence_bert_config.json": "84e39fda68ccbff05bfa723ae9c0e70e23e2ec373b76e0f8c6e71af72a693cbf",
    "special_tokens_map.json": "b6d346be366a7d1d48332dbc9fdf3bf8960b5d879522b7799ddba59e76237ee3",
    "tokenizer.json": "d241a60d5e8f04cc1b2b3e9ef7a4921b27bf526d9f6050ab90f9267a1f9e5c66",
    "tokenizer_config.json": "9261e7d79b44c8195c1cada2b453e55b00aeb81e907a6664974b4d7776172ab3",
    "vocab.txt": "07eced375cec144d27c900241f3e339478dec958f92fddbc551f295c992038a3",
    "model.safetensors": "3c9f31665447c8911517620762200d2245a2518d6e7208acc78cd9db317e21ad",
}


class BGEEncoder:
    def __init__(self, model_path: Path, device: str, batch_size: int) -> None:
        if device.startswith("cuda") and not torch.cuda.is_available():
            raise RuntimeError("Requested CUDA device is unavailable")
        if batch_size < 1:
            raise ValueError("batch_size must be positive")
        for name, expected in MODEL_FILES.items():
            with (model_path / name).open("rb") as stream:
                if file_digest(stream, "sha256").hexdigest() != expected:
                    raise ValueError(f"BGE snapshot fingerprint mismatch: {name}")
        torch.manual_seed(20261105)
        self.model = SentenceTransformer(
            str(model_path),
            device=device,
            local_files_only=True,
            trust_remote_code=False,
            model_kwargs={"use_safetensors": True},
        )
        if next(self.model.parameters()).dtype != torch.float32:
            raise ValueError("BGE parameters must be float32")
        self.model.max_seq_length = MAX_LENGTH
        self.batch_size = batch_size

    def encode(self, texts: list[str]) -> tuple[np.ndarray, int]:
        truncated = 0
        for start in range(0, len(texts), self.batch_size):
            batch = texts[start : start + self.batch_size]
            tokens = self.model.tokenizer(batch, truncation=False, verbose=False)["input_ids"]
            truncated += sum(len(token_ids) > MAX_LENGTH for token_ids in tokens)
        vectors = self.model.encode(
            texts, batch_size=self.batch_size, normalize_embeddings=True, show_progress_bar=False
        )
        return np.ascontiguousarray(vectors, dtype=np.float32), truncated


class DenseRetriever:
    def __init__(
        self,
        corpus: Corpus,
        fingerprint: str,
        encoder: BGEEncoder,
        *,
        snapshot: Path | None = None,
    ) -> None:
        self.units = tuple(sorted(corpus.units, key=lambda unit: unit.unit_id))
        self.domain = self.units[0].entity_key.domain
        if any(unit.entity_key.domain != self.domain for unit in self.units):
            raise ValueError("Dense snapshot must contain one domain")
        self.encoder = encoder
        self.query_truncations = 0
        self.config = {
            "model": MODEL_ID,
            "revision": MODEL_REVISION,
            "query_prefix": QUERY_PREFIX,
            "max_length": MAX_LENGTH,
            "batch_size": encoder.batch_size,
            "normalize": "L2",
            "precision": "float32",
            "seed": 20261105,
            "files_sha256": MODEL_FILES,
        }
        config_hash = sha256(json.dumps(self.config, sort_keys=True).encode()).hexdigest()
        compatibility = IndexCompatibility(
            fingerprint,
            "dense",
            "1",
            MODEL_REVISION,
            EMBEDDING_DIMENSION,
            "inner_product",
            "float32",
        )
        self.manifest = IndexManifest(
            f"dense-{fingerprint}-{config_hash}",
            compatibility,
            "IndexFlatIP",
            version("faiss-cpu"),
            config_hash,
        )

        if snapshot is None:
            vectors, self.document_truncations = encoder.encode([unit.text for unit in self.units])
            if vectors.shape != (len(self.units), EMBEDDING_DIMENSION):
                raise ValueError("Unexpected BGE embedding shape")
            self.index = faiss.IndexFlatIP(EMBEDDING_DIMENSION)
            self.index.add(vectors)
        else:
            meta = json.loads((snapshot / "index_manifest.json").read_bytes())
            if meta["index"] != asdict(self.manifest):
                raise ValueError("Incompatible saved dense index manifest")
            inventory = json.loads((snapshot / "entity_ids.json").read_bytes())
            if inventory != [unit.unit_id for unit in self.units]:
                raise ValueError("Saved dense index entity order differs from corpus")
            index_path = snapshot / "index.faiss"
            with index_path.open("rb") as stream:
                digest = file_digest(stream, "sha256").hexdigest()
            if digest != meta["index_files_sha256"]["index.faiss"]:
                raise ValueError("Saved dense index fingerprint mismatch")
            self.index = faiss.read_index(str(index_path))
            if (
                not isinstance(self.index, faiss.IndexFlatIP)
                or self.index.ntotal != len(self.units)
                or self.index.d != EMBEDDING_DIMENSION
            ):
                raise ValueError("Saved dense index format or shape mismatch")
            self.document_truncations = meta["document_truncations"]

    def retrieve(self, query: str, domain: str, limit: int) -> tuple[Candidate, ...]:
        if domain != self.domain:
            return ()
        vectors, truncated = self.encoder.encode([QUERY_PREFIX + query])
        self.query_truncations += truncated
        scores, indices = self.index.search(vectors, min(limit + 1, len(self.units)))
        if len(scores[0]) > limit and scores[0, limit - 1] == scores[0, limit]:
            scores, indices = self.index.search(vectors, len(self.units))
        ranked = sorted(
            zip(indices[0], scores[0], strict=True),
            key=lambda pair: (-float(pair[1]), self.units[pair[0]].unit_id),
        )
        return tuple(Candidate(self.units[i], float(score)) for i, score in ranked[:limit])
