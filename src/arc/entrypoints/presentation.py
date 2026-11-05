from dataclasses import asdict

from arc.application.harness import SearchResponse


def present(response: SearchResponse, *, units: bool, trace: bool) -> dict:
    body = {
        "status": "success",
        "snapshot_id": response.snapshot_id,
        "strategy_id": response.strategy_id,
        "trace_id": response.trace_id,
        "elapsed_ms": response.elapsed_ms,
        "hits": [
            {
                "entity_key": asdict(hit.entity.key),
                "title": hit.entity.title,
                "source_ref": hit.entity.source_ref,
                "rank": hit.rank,
                "score": hit.candidate.score,
                "score_type": response.score_type,
                **(
                    {"unit_id": hit.candidate.unit.unit_id, "location": hit.candidate.unit.location}
                    if units
                    else {}
                ),
            }
            for hit in response.hits
        ],
    }
    if trace:
        body["trace"] = [asdict(stage) for stage in response.stages]
    return body
