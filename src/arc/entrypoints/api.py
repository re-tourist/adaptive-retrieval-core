import os
from pathlib import Path
from typing import Annotated, Literal

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field

from arc.application.harness import SearchHarness, SnapshotMismatch
from arc.application.search import SearchQuery
from arc.bootstrap import configured_harness
from arc.entrypoints.presentation import present


class Filters(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    entity_ids: list[Annotated[str, Field(min_length=1, max_length=256)]] | None = Field(
        default=None, max_length=1000
    )


class Request(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    query: str = Field(min_length=1, max_length=4096)
    domain: Literal["technical", "product"]
    top_k: int = Field(default=10, ge=1, le=100)
    strategy_id: Literal["bm25", "dense", "hybrid", "hybrid_rerank"] = "bm25"
    return_level: Literal["entity", "unit"] = "entity"
    trace_level: Literal["none", "summary"] = "none"
    filters: Filters | None = None
    snapshot_id: str | None = Field(default=None, max_length=256)


def create_app(harness: SearchHarness, *, corpus_name: str | None = None) -> FastAPI:
    app = FastAPI(title="ARC", version="0.1.0")

    @app.get("/healthz")
    def health() -> dict:
        return {"status": "ready", "domain": harness.domain, "snapshots": harness.snapshots}

    @app.get("/playground/config", include_in_schema=False)
    def playground_config() -> dict:
        return {**health(), "corpus": corpus_name}

    app.mount(
        "/playground",
        StaticFiles(directory=Path(__file__).with_name("playground"), html=True),
        name="playground",
    )

    @app.post("/search")
    def search(request: Request) -> dict:
        ids = request.filters.entity_ids if request.filters is not None else None
        try:
            query = SearchQuery(
                request.query,
                request.domain,
                request.top_k,
                None if ids is None else frozenset(ids),
            )
        except ValueError as error:
            raise HTTPException(422, str(error)) from error
        try:
            response = harness.search(query, request.strategy_id, snapshot_id=request.snapshot_id)
        except SnapshotMismatch as error:
            raise HTTPException(409, str(error)) from error
        except KeyError as error:
            raise HTTPException(404, "Domain or strategy unavailable") from error
        return present(
            response, units=request.return_level == "unit", trace=request.trace_level == "summary"
        )

    return app


def factory() -> FastAPI:
    return create_app(configured_harness(), corpus_name=os.getenv("ARC_DATASET", "demo"))
