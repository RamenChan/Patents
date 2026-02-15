from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, List, Optional, Protocol, Sequence, TypeVar

from patents.domain import models


T = TypeVar("T")


class Clock(Protocol):
    def now(self) -> "datetime":
        ...


class IdGenerator(Protocol):
    def new_id(self) -> str:
        ...


class Repository(Protocol[T]):
    def get(self, entity_id: str) -> Optional[T]:
        ...

    def list_by_invention(self, invention_id: str) -> Sequence[T]:
        ...

    def save(self, entity: T) -> None:
        ...


class LLMClient(Protocol):
    def generate(self, prompt: str) -> str:
        ...


class Storage(Protocol):
    def put(self, key: str, data: bytes) -> str:
        ...

    def get(self, key: str) -> bytes:
        ...


@dataclass(frozen=True)
class FilingPackage:
    invention: models.Invention
    claims: List[models.Claim]
    sections: List[models.SpecSection]
    figures: List[models.Figure]
    prior_art: List[models.PriorArt]
    citations: List[models.Citation]


class DocumentRenderer(Protocol):
    file_extension: str

    def render_spec(self, package: FilingPackage) -> bytes:
        ...

    def render_claims(self, package: FilingPackage) -> bytes:
        ...

    def render_abstract(self, package: FilingPackage) -> bytes:
        ...

    def render_ids(self, package: FilingPackage) -> bytes:
        ...
