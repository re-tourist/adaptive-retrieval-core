from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass
from hashlib import sha256


@dataclass(frozen=True, slots=True)
class QrelsAudit:
    rows: int
    label_counts: dict[int, int]
    identical_repeats: int
    conflicts: dict[tuple[str, str], tuple[int, ...]]
    unknown_queries: tuple[str, ...]
    unknown_entities: tuple[str, ...]
    positive_counts: dict[str, int]


def audit_qrels(
    rows: Iterable[tuple[str, str, int]], query_ids: set[str], entity_ids: set[str]
) -> tuple[dict[str, dict[str, int]] | None, QrelsAudit]:
    labels: dict[tuple[str, str], set[int]] = {}
    distribution: Counter[int] = Counter()
    repeats = 0
    for query_id, entity_id, grade in rows:
        if type(grade) is not int or grade not in (0, 1, 2):
            raise ValueError("Unsupported relevance grade")
        grades = labels.setdefault((query_id, entity_id), set())
        repeats += grade in grades
        grades.add(grade)
        distribution[grade] += 1
    conflicts = {key: tuple(sorted(grades)) for key, grades in labels.items() if len(grades) > 1}
    unknown_queries = tuple(sorted({q for q, _ in labels} - query_ids))
    unknown_entities = tuple(sorted({e for _, e in labels} - entity_ids))
    qrels = {qid: {} for qid in sorted(query_ids)}
    for (qid, eid), grades in labels.items():
        if qid in qrels and eid in entity_ids and len(grades) == 1:
            qrels[qid][eid] = next(iter(grades))
    audit = QrelsAudit(
        distribution.total(),
        dict(sorted(distribution.items())),
        repeats,
        conflicts,
        unknown_queries,
        unknown_entities,
        {qid: sum(grade > 0 for grade in docs.values()) for qid, docs in qrels.items()},
    )
    return (None if conflicts or unknown_queries or unknown_entities else qrels), audit


def wands_split(query_ids: Iterable[str]) -> tuple[tuple[str, ...], tuple[str, ...]]:
    unique_ids = set(query_ids)
    if len(unique_ids) != 480:
        raise ValueError(f"Expected 480 unique WANDS query IDs, found {len(unique_ids)}")
    ordered = sorted(
        unique_ids, key=lambda qid: (sha256(f"ARC-WANDS-v0.1|{qid}".encode()).digest(), qid)
    )
    return tuple(ordered[:80]), tuple(ordered[80:])
