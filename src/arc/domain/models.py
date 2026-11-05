from dataclasses import dataclass


@dataclass(frozen=True, slots=True, order=True)
class EntityKey:
    domain: str
    entity_id: str
    revision: str

    def __post_init__(self) -> None:
        if not all(value.strip() for value in (self.domain, self.entity_id, self.revision)):
            raise ValueError("Entity domain, ID and revision must be nonempty")


@dataclass(frozen=True, slots=True)
class Entity:
    key: EntityKey
    title: str
    source_ref: str

    def __post_init__(self) -> None:
        if not self.source_ref.strip():
            raise ValueError("Entity source reference must be nonempty")


@dataclass(frozen=True, slots=True)
class RetrievalUnit:
    unit_id: str
    entity_key: EntityKey
    text: str
    location: str

    def __post_init__(self) -> None:
        if not self.unit_id.strip() or not self.location.strip():
            raise ValueError("Unit ID and location must be nonempty")
