import json
import subprocess
import sys

import pytest


def test_cpu_bm25_http_contract(monkeypatch: pytest.MonkeyPatch) -> None:
    pytest.importorskip("fastapi")
    pytest.importorskip("bm25s")
    pytest.importorskip("httpx")
    from fastapi.testclient import TestClient

    from arc.bootstrap import configured_harness
    from arc.entrypoints.api import create_app

    monkeypatch.setenv("ARC_DATASET", "demo")
    for name in ("ARC_BGE_MODEL", "ARC_DENSE_INDEX", "ARC_MINILM_MODEL"):
        monkeypatch.delenv(name, raising=False)

    with TestClient(create_app(configured_harness())) as client:
        health = client.get("/healthz")
        assert health.status_code == 200
        snapshot = health.json()["snapshots"]["bm25"]
        body = {"query": "BM25", "domain": "technical", "top_k": 1}
        response = client.post("/search", json=body)
        assert response.status_code == 200
        result = response.json()
        assert result["snapshot_id"] == snapshot
        assert result["hits"][0]["entity_key"]["entity_id"] == "sparse"
        assert "trace" not in result and "unit_id" not in result["hits"][0]
        body.update(
            {
                "filters": {"entity_ids": ["rrf"]},
                "trace_level": "summary",
                "return_level": "unit",
            }
        )
        filtered = client.post("/search", json=body).json()
        assert [h["entity_key"]["entity_id"] for h in filtered["hits"]] == ["rrf"]
        assert filtered["hits"][0]["unit_id"] == "rrf"
        assert [s["name"] for s in filtered["trace"]] == ["bm25", "assemble"]
        assert filtered["trace_id"] != result["trace_id"]
        assert (
            client.post("/search", json={**body, "filters": {"entity_ids": []}}).json()["hits"]
            == []
        )
        assert client.post("/search", json={**body, "domain": "product"}).status_code == 404
        assert client.post("/search", json={**body, "strategy_id": "dense"}).status_code == 404
        assert client.post("/search", json={**body, "snapshot_id": "old"}).status_code == 409
        assert client.post("/search", json={**body, "filters": {"label": 1}}).status_code == 422
        assert client.post("/search", json={**body, "query": "  "}).status_code == 422


def test_cli_stdout_is_one_json_document(monkeypatch: pytest.MonkeyPatch) -> None:
    pytest.importorskip("bm25s")
    monkeypatch.setenv("ARC_DATASET", "demo")
    for name in ("ARC_BGE_MODEL", "ARC_DENSE_INDEX", "ARC_MINILM_MODEL"):
        monkeypatch.delenv(name, raising=False)
    raw = subprocess.check_output(
        [sys.executable, "-m", "arc.entrypoints.cli", "search", "BM25", "--top-k", "1"]
    )
    assert json.loads(raw)["hits"][0]["entity_key"]["entity_id"] == "sparse"


def test_playground_assets_and_field_note_queries(monkeypatch: pytest.MonkeyPatch) -> None:
    pytest.importorskip("fastapi")
    pytest.importorskip("bm25s")
    pytest.importorskip("httpx")
    from fastapi.testclient import TestClient

    from arc.entrypoints.api import factory

    monkeypatch.setenv("ARC_DATASET", "playground")
    for name in ("ARC_BGE_MODEL", "ARC_DENSE_INDEX", "ARC_MINILM_MODEL"):
        monkeypatch.delenv(name, raising=False)
    with TestClient(factory()) as client:
        page = client.get("/playground")
        assert page.url.path == "/playground/" and "Search Playground" in page.text
        assert "text/css" in client.get("/playground/playground.css").headers["content-type"]
        assert "javascript" in client.get("/playground/playground.js").headers["content-type"]
        config = client.get("/playground/config").json()
        assert config == {**client.get("/healthz").json(), "corpus": "playground"}
        assert list(config["snapshots"]) == ["bm25"]
        for text, expected in (
            ("BM25", "bm25"),
            ("dense vector search", "faiss"),
            ("reciprocal rank fusion", "rrf"),
        ):
            response = client.post(
                "/search",
                json={
                    "query": text,
                    "domain": config["domain"],
                    "snapshot_id": config["snapshots"]["bm25"],
                    "trace_level": "summary",
                    "top_k": 3,
                },
            )
            assert response.status_code == 200
            payload = response.json()
            assert payload["hits"][0]["source_ref"] == f"playground://{expected}"
            assert payload["hits"][0]["score"] > 0
            assert [stage["name"] for stage in payload["trace"]] == ["bm25", "assemble"]


def test_live_catalog_uses_search_results_and_packaged_assets(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pytest.importorskip("fastapi")
    pytest.importorskip("bm25s")
    pytest.importorskip("httpx")
    from fastapi.testclient import TestClient

    from arc.entrypoints.api import factory

    monkeypatch.setenv("ARC_DATASET", "catalog")
    for name in ("ARC_BGE_MODEL", "ARC_DENSE_INDEX", "ARC_MINILM_MODEL"):
        monkeypatch.delenv(name, raising=False)
    with TestClient(factory()) as client:
        health = client.get("/healthz").json()
        config = client.get("/playground/config").json()
        assert health["domain"] == "product" and list(health["snapshots"]) == ["bm25"]
        assert config["corpus"] == "catalog" and config["snapshots"] == health["snapshots"]
        products = config["products"]
        assert len(products) == 22
        for sheet, count in (("lighting", 4), ("storage", 9), ("textiles", 9)):
            assert {p["tile"] for p in products.values() if p["sheet"] == sheet} == set(
                range(count)
            )
            photo = client.get(f"/playground/assets/{sheet}.webp")
            assert photo.status_code == 200 and photo.content[8:12] == b"WEBP"
        body = {
            "domain": "product",
            "top_k": 4,
            "snapshot_id": health["snapshots"]["bm25"],
            "trace_level": "summary",
        }
        for query, expected in (
            ("small brass reading lamp", "cove-reading-lamp"),
            ("small brass lamp for a reading nook", "cove-reading-lamp"),
            ("woven basket for extra blankets", "haven-blanket-basket"),
            ("soft green throw for a sofa", "moss-waffle-throw"),
            ("walnut catchall tray", "sill-walnut-tray"),
        ):
            result = client.post("/search", json={**body, "query": query})
            assert result.status_code == 200
            payload = result.json()
            assert payload["hits"][0]["entity_key"]["entity_id"] == expected
            for rank, hit in enumerate(payload["hits"], 1):
                key = hit["entity_key"]["entity_id"]
                assert hit["rank"] == rank and hit["score"] > 0
                assert (
                    hit["source_ref"] == f"catalog://{key}"
                    and len(products[key]["attributes"]) == 2
                )
            assert [stage["name"] for stage in payload["trace"]] == ["bm25", "assemble"]
        for query in ("zxqv889", "!!!"):
            assert client.post("/search", json={**body, "query": query}).json()["hits"] == []
        request = {**body, "query": "lamp"}
        assert client.post("/search", json={**request, "strategy_id": "hybrid"}).status_code == 404
        assert client.post("/search", json={**request, "snapshot_id": "old"}).status_code == 409
