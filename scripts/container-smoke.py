import argparse
import json
from time import monotonic, sleep
from urllib.error import URLError
from urllib.request import Request, urlopen


def smoke(base: str) -> None:
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
    assert health["status"] == "ready" and health["domain"] == "technical"
    request = Request(
        base + "/search",
        data=json.dumps(
            {"query": "BM25", "domain": "technical", "top_k": 1, "trace_level": "summary"}
        ).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urlopen(request, timeout=10) as stream:
        body = json.load(stream)
    assert body["status"] == "success"
    assert body["snapshot_id"] == health["snapshots"]["bm25"]
    assert body["hits"][0]["entity_key"]["entity_id"] == "sparse"
    assert [stage["name"] for stage in body["trace"]] == ["bm25", "assemble"]
    with urlopen(base + "/playground", timeout=10) as stream:
        assert stream.headers.get_content_type() == "text/html"
        assert b"Search Playground" in stream.read()
    for asset, content_type in (("playground.css", "text/css"), ("playground.js", "javascript")):
        with urlopen(base + "/playground/" + asset, timeout=10) as stream:
            assert content_type in stream.headers.get_content_type()
    with urlopen(base + "/playground/config", timeout=10) as stream:
        config = json.load(stream)
    assert config["corpus"] == "demo" and config["snapshots"] == health["snapshots"]
    print("ARC HTTP smoke passed:", body["strategy_id"], body["snapshot_id"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("base")
    smoke(parser.parse_args().base.rstrip("/"))
