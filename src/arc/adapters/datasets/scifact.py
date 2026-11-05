import csv
import json
from collections.abc import Iterator
from pathlib import Path

from arc.adapters.datasets.common import Dataset, fingerprints, make_corpus, make_queries


def _jsonl(path: Path) -> Iterator[dict]:
    with path.open(encoding="utf-8") as stream:
        for line in stream:
            yield json.loads(line)


def _qrels(path: Path) -> tuple[tuple[str, str, int], ...]:
    with path.open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream, delimiter="\t")
        if reader.fieldnames != ["query-id", "corpus-id", "score"]:
            raise ValueError(f"Unexpected SciFact judgments schema in {path.name}")
        return tuple((row["query-id"], row["corpus-id"], int(row["score"])) for row in reader)


def load_scifact(root: Path) -> Dataset:
    files = fingerprints(
        root, ("corpus.jsonl", "queries.jsonl", "qrels/train.tsv", "qrels/test.tsv")
    )
    corpus_rows = tuple(
        (row["_id"], row["title"], row["text"]) for row in _jsonl(root / "corpus.jsonl")
    )
    corpus = make_corpus(
        "scifact",
        "technical",
        ((eid, title, title + "\n" + body) for eid, title, body in corpus_rows),
        {"corpus.jsonl": files["corpus.jsonl"]},
    )
    queries = make_queries((row["_id"], row["text"]) for row in _jsonl(root / "queries.jsonl"))
    judgments = {"dev": _qrels(root / "qrels/train.tsv"), "test": _qrels(root / "qrels/test.tsv")}
    return Dataset(
        corpus,
        queries,
        judgments,
        files,
        {
            "title": sum(not title.strip() for _, title, _ in corpus_rows),
            "text": sum(not text.strip() for _, _, text in corpus_rows),
        },
    )
