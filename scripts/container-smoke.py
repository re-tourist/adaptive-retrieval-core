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
    print("ARC HTTP smoke passed:", body["strategy_id"], body["snapshot_id"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("base")
    smoke(parser.parse_args().base.rstrip("/"))
