import csv
from collections import Counter
from collections.abc import Iterator
from pathlib import Path

from arc.adapters.datasets.common import Dataset, fingerprints, make_corpus, make_queries

_TEXT_FIELDS = (
    "product_name",
    "product_class",
    "category_hierarchy",
    "product_features",
    "product_description",
)
# The official TSV spells this header with a space.
_PRODUCT_HEADERS = {"category_hierarchy": "category hierarchy"}
_GRADES = {"Exact": 2, "Partial": 1, "Irrelevant": 0}


def _rows(path: Path, required: tuple[str, ...]) -> Iterator[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream, delimiter="\t", strict=True)
        if not set(required).issubset(reader.fieldnames or []):
            raise ValueError(f"Unexpected WANDS header in {path.name}")
        for row in reader:
            if None in row or any(value is None for value in row.values()):
                raise ValueError(f"Malformed WANDS TSV row {reader.line_num} in {path.name}")
            yield row


def load_wands(root: Path) -> Dataset:
    files = fingerprints(root, ("product.csv", "query.csv", "label.csv"))
    empty_fields: Counter[str] = Counter(dict.fromkeys(_TEXT_FIELDS, 0))

    def products() -> Iterator[tuple[str, str, str]]:
        headers = tuple(_PRODUCT_HEADERS.get(field, field) for field in _TEXT_FIELDS)
        for row in _rows(root / "product.csv", ("product_id", *headers)):
            fields = dict(zip(_TEXT_FIELDS, (row[header] for header in headers), strict=True))
            empty_fields.update(field for field, value in fields.items() if not value.strip())
            text = "\n".join(f"{field}: {value}" for field, value in fields.items())
            yield row["product_id"], row["product_name"], text

    corpus = make_corpus("wands", "product", products(), {"product.csv": files["product.csv"]})
    return Dataset(
        corpus,
        load_wands_queries(root),
        {"all": load_wands_labels(root)},
        files,
        dict(empty_fields),
    )


def load_wands_queries(root: Path) -> dict[str, str]:
    return make_queries(
        (row["query_id"], row["query"]) for row in _rows(root / "query.csv", ("query_id", "query"))
    )


def load_wands_labels(root: Path) -> tuple[tuple[str, str, int], ...]:
    return tuple(
        (row["query_id"], row["product_id"], _GRADES[row["label"]])
        for row in _rows(root / "label.csv", ("query_id", "product_id", "label"))
    )
