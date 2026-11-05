from collections.abc import Iterable
from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True, slots=True)
class RunRow:
    query_id: str
    entity_id: str
    rank: int
    score: float
    tag: str


def _token(value: str) -> bool:
    return bool(value) and not any(char.isspace() for char in value)


def validate_run(
    rows: Iterable[RunRow], query_ids: set[str], entity_ids: set[str]
) -> dict[str, tuple[str, ...]]:
    grouped: dict[str, dict[int, str]] = {}
    seen: set[tuple[str, str]] = set()
    tags: set[str] = set()
    for row in rows:
        if row.query_id not in query_ids or row.entity_id not in entity_ids:
            raise ValueError("Runfile contains a query outside its split or an unknown entity")
        if not all(_token(token) for token in (row.query_id, row.entity_id, row.tag)):
            raise ValueError("Invalid Runfile token")
        if type(row.rank) is not int or not 1 <= row.rank <= 100 or not isfinite(row.score):
            raise ValueError("Invalid Runfile rank or score")
        by_rank = grouped.setdefault(row.query_id, {})
        pair = (row.query_id, row.entity_id)
        if row.rank in by_rank or pair in seen:
            raise ValueError("Duplicate Runfile rank or entity")
        by_rank[row.rank] = row.entity_id
        seen.add(pair)
        tags.add(row.tag)
    if len(tags) > 1:
        raise ValueError("Runfile must contain a single run tag")
    if any(set(ranks) != set(range(1, len(ranks) + 1)) for ranks in grouped.values()):
        raise ValueError("Runfile ranks must be contiguous and start at one")
    return {qid: tuple(eid for _, eid in sorted(ranks.items())) for qid, ranks in grouped.items()}


def read_run(lines: Iterable[str], query_ids: set[str], entity_ids: set[str]) -> tuple[RunRow, ...]:
    rows = []
    for number, line in enumerate(lines, 1):
        fields = line.split()
        if len(fields) != 6 or fields[1] != "Q0":
            raise ValueError(f"Expected six TREC fields and Q0 on line {number}")
        qid, _, eid, rank, score, tag = fields
        rows.append(RunRow(qid, eid, int(rank), float(score), tag))
    validate_run(rows, query_ids, entity_ids)
    return tuple(rows)


def render_run(rows: Iterable[RunRow], query_ids: set[str], entity_ids: set[str]) -> str:
    checked = tuple(rows)
    validate_run(checked, query_ids, entity_ids)
    return "".join(
        f"{row.query_id} Q0 {row.entity_id} {row.rank} {row.score:.17g} {row.tag}\n"
        for row in sorted(checked, key=lambda row: (row.query_id, row.rank))
    )


def rank_scores(query_id: str, scores: Iterable[tuple[str, float]], tag: str) -> tuple[RunRow, ...]:
    scored = tuple(scores)
    if any(not isfinite(score) for _, score in scored):
        raise ValueError("Runfile scores must be finite")
    ordered = sorted(scored, key=lambda pair: (-pair[1], pair[0]))
    return tuple(
        RunRow(query_id, entity_id, rank, score, tag)
        for rank, (entity_id, score) in enumerate(ordered[:100], 1)
    )
