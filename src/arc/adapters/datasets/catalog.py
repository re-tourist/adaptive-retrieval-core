"""Original homewares for the opt-in Showcase catalog."""

import json
from functools import cache
from hashlib import sha256
from pathlib import Path

from arc.adapters.datasets.common import make_corpus
from arc.application.ports import Corpus


@cache
def _products() -> list[dict]:
    return json.loads(Path(__file__).with_suffix(".json").read_text(encoding="utf-8"))


def load_catalog_corpus() -> Corpus:
    rows = [
        (
            product["id"],
            product["title"],
            "\n".join((product["title"], *product["attributes"], product["description"])),
        )
        for product in _products()
    ]
    # Bind the index to retrieval content, independent of line endings and photo placement.
    fingerprint = sha256(json.dumps(rows).encode()).hexdigest()
    return make_corpus("catalog", "product", rows, {"catalog": fingerprint})


def catalog_cards() -> dict:
    return {
        product["id"]: {
            "attributes": tuple(product["attributes"]),
            "sheet": product["sheet"],
            "tile": product["tile"],
        }
        for product in _products()
    }
