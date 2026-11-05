import re
import unicodedata
from hashlib import sha256
from importlib.metadata import version

import bm25s

from arc.application.ports import Candidate, Corpus, IndexCompatibility, IndexManifest, TraceHook

_TOKEN = re.compile(r"[^\W_]+(?:-[^\W_]+)*")
CONFIG = {
    "method": "lucene",
    "k1": 1.2,
    "b": 0.75,
    "tokenizer": "unicode-nfkc-casefold-hyphen-v1",
    "stemming": False,
    "stopwords": False,
}


def tokenize(text: str) -> list[str]:
    return _TOKEN.findall(unicodedata.normalize("NFKC", text).casefold())


class BM25Retriever:
    def __init__(self, corpus: Corpus, fingerprint: str) -> None:
        self.units = tuple(sorted(corpus.units, key=lambda unit: unit.unit_id))
        self.domain = self.units[0].entity_key.domain
        if any(unit.entity_key.domain != self.domain for unit in self.units):
            raise ValueError("BM25 snapshot must contain one domain")
        self.index = bm25s.BM25(k1=CONFIG["k1"], b=CONFIG["b"], method=CONFIG["method"])
        self.index.index([tokenize(unit.text) for unit in self.units], show_progress=False)
        config_hash = sha256(repr(CONFIG).encode()).hexdigest()
        compatibility = IndexCompatibility(fingerprint, "bm25", "1")
        self.manifest = IndexManifest(
            f"bm25-{fingerprint}-{config_hash}",
            compatibility,
            "bm25s",
            version("bm25s"),
            config_hash,
        )

    def retrieve(
        self,
        query: str,
        domain: str,
        limit: int,
        *,
        allowed_ids: frozenset[str] | None = None,
        observe: TraceHook | None = None,
    ) -> tuple[Candidate, ...]:
        if domain != self.domain:
            return ()
        eligible = [
            i
            for i, unit in enumerate(self.units)
            if allowed_ids is None or unit.entity_key.entity_id in allowed_ids
        ]
        if not eligible:
            return ()
        tokens = tokenize(query)
        if not tokens:
            return tuple(Candidate(unit, 0.0) for unit in (self.units[i] for i in eligible[:limit]))
        scores = self.index.get_scores(tokens)
        order = sorted(eligible, key=lambda i: (-float(scores[i]), self.units[i].unit_id))
        return tuple(Candidate(self.units[i], float(scores[i])) for i in order[:limit])
