from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from hashlib import file_digest, sha256
from pathlib import Path

from arc.application.ports import Corpus
from arc.domain.models import Entity, EntityKey, RetrievalUnit


@dataclass(frozen=True, slots=True)
class Dataset:
    corpus: Corpus
    queries: dict[str, str]
    judgments: dict[str, tuple[tuple[str, str, int], ...]]
    files: dict[str, str]
    empty_fields: dict[str, int]


def fingerprints(root: Path, names: Iterable[str]) -> dict[str, str]:
    result = {}
    for name in names:
        with (root / name).open("rb") as stream:
            result[name] = file_digest(stream, "sha256").hexdigest()
    return result


def make_corpus(
    dataset: str, domain: str, rows: Iterable[tuple[str, str, str]], files: Mapping[str, str]
) -> Corpus:
    revision = sha256("".join(files.values()).encode()).hexdigest()
    entities, units = [], []
    for source_id, title, text in rows:
        key = EntityKey(domain, source_id, revision)
        entities.append(Entity(key, title, f"{dataset}://{source_id}"))
        units.append(RetrievalUnit(source_id, key, text, "document"))
    return Corpus(tuple(entities), tuple(units))


def make_queries(rows: Iterable[tuple[str, str]]) -> dict[str, str]:
    queries = {}
    for qid, text in rows:
        if not qid or qid in queries or not text.strip():
            raise ValueError(f"Empty or duplicate query ID/text: {qid!r}")
        queries[qid] = text
    return queries
