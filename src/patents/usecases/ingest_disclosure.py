from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from patents.adapters import ports
from patents.domain import models


@dataclass(frozen=True)
class IngestDisclosureInput:
    title: str
    summary: str
    inventors: list[str]
    disclosure_text: str
    source: str
    tags: list[str] | None = None


@dataclass(frozen=True)
class IngestDisclosureOutput:
    invention: models.Invention
    disclosure: models.Disclosure


class IngestDisclosure:
    def __init__(
        self,
        invention_repo: ports.Repository[models.Invention],
        disclosure_repo: ports.Repository[models.Disclosure],
        id_gen: ports.IdGenerator,
        clock: ports.Clock,
    ) -> None:
        self._invention_repo = invention_repo
        self._disclosure_repo = disclosure_repo
        self._id_gen = id_gen
        self._clock = clock

    def execute(self, data: IngestDisclosureInput) -> IngestDisclosureOutput:
        now = self._clock.now()
        invention = models.Invention(
            id=self._id_gen.new_id(),
            title=data.title,
            summary=data.summary,
            inventors=data.inventors,
            tags=data.tags or [],
            created_at=now,
            updated_at=now,
        )
        disclosure = models.Disclosure(
            id=self._id_gen.new_id(),
            invention_id=invention.id,
            text=data.disclosure_text,
            source=data.source,
            created_at=now,
        )
        self._invention_repo.save(invention)
        self._disclosure_repo.save(disclosure)
        return IngestDisclosureOutput(invention=invention, disclosure=disclosure)
