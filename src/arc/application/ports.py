from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol

from arc.domain.models import Entity, RetrievalUnit


@dataclass(frozen=True, slots=True)
class IndexCompatibility:
    dataset_fingerprint: str
    representation_type: str
    schema_version: str
    encoder_revision: str | None = None
    vector_dimension: int | None = None
    distance: str | None = None
    precision: str | None = None


@dataclass(frozen=True, slots=True)
class IndexManifest:
    index_id: str
    compatibility: IndexCompatibility
    backend: str
    backend_version: str
    build_config_hash: str

    def require_compatible(self, expected: IndexCompatibility) -> None:
        if self.compatibility != expected:
            raise ValueError(f"Incompatible index snapshot: {self.index_id}")


@dataclass(frozen=True, slots=True)
class Candidate:
    unit: RetrievalUnit
    score: float


TraceHook = Callable[[str, float, int], None]


class Retriever(Protocol):
    @property
    def manifest(self) -> IndexManifest: ...

    def retrieve(
        self,
        query: str,
        domain: str,
        limit: int,
        *,
        allowed_ids: frozenset[str] | None = None,
        observe: TraceHook | None = None,
    ) -> tuple[Candidate, ...]: ...


@dataclass(frozen=True, slots=True)
class Corpus:
    entities: tuple[Entity, ...]
    units: tuple[RetrievalUnit, ...]

    def __post_init__(self) -> None:
        keys = {entity.key for entity in self.entities}
        identities = {(key.domain, key.entity_id) for key in keys}
        if len(identities) != len(self.entities):
            raise ValueError("Corpus must contain one revision per entity")
        if len({unit.unit_id for unit in self.units}) != len(self.units):
            raise ValueError("Duplicate retrieval unit ID")
        if any(unit.entity_key not in keys for unit in self.units):
            raise ValueError("Retrieval unit refers to an entity outside the corpus")
