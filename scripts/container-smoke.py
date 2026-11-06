import argparse
import json
from time import monotonic, sleep
from urllib.error import URLError
from urllib.request import Request, urlopen


def smoke(base: str, *, catalog: bool = False) -> None:
    corpus, domain, query, expected = (
        ("catalog", "product", "woven basket for extra blankets", "haven-blanket-basket")
        if catalog
        else ("demo", "technical", "BM25", "sparse")
    )
    deadline = monotonic() + 45
    while True:
        try:
            with urlopen(base + "/healthz", timeout=2) as stream:
                health = json.load(stream)
            break
        except (URLError, ConnectionError, TimeoutError):
            if monotonic() >= deadline:
                raise
            sleep(1)
    assert health["status"] == "ready" and health["domain"] == domain
    assert list(health["snapshots"]) == ["bm25"]
    request = Request(
        base + "/search",
        data=json.dumps(
            {"query": query, "domain": domain, "top_k": 1, "trace_level": "summary"}
        ).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urlopen(request, timeout=10) as stream:
        body = json.load(stream)
    assert body["status"] == "success"
    assert body["snapshot_id"] == health["snapshots"]["bm25"]
    assert body["hits"][0]["entity_key"]["entity_id"] == expected
    assert [stage["name"] for stage in body["trace"]] == ["bm25", "assemble"]
    with urlopen(base + "/playground", timeout=10) as stream:
        assert stream.headers.get_content_type() == "text/html"
        assert b"Search Playground" in stream.read()
    for asset, content_type in (("playground.css", "text/css"), ("playground.js", "javascript")):
        with urlopen(base + "/playground/" + asset, timeout=10) as stream:
            assert content_type in stream.headers.get_content_type()
    with urlopen(base + "/playground/config", timeout=10) as stream:
        config = json.load(stream)
    assert config["corpus"] == corpus and config["snapshots"] == health["snapshots"]
    if catalog:
        assert config["products"][expected]["sheet"] == "storage"
        with urlopen(base + "/playground/assets/storage.webp", timeout=10) as stream:
            assert stream.read(12)[8:] == b"WEBP"
    print("ARC HTTP smoke passed:", corpus, expected, body["strategy_id"], body["snapshot_id"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("base")
    parser.add_argument("--catalog", action="store_true")
    args = parser.parse_args()
    smoke(args.base.rstrip("/"), catalog=args.catalog)
