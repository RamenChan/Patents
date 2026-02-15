from __future__ import annotations

from dataclasses import dataclass

from patents.adapters import ports
from patents.domain import models


@dataclass(frozen=True)
class AssembleIdsInput:
    invention: models.Invention
    prior_art: list[models.PriorArt]
    citations: list[models.Citation]


@dataclass(frozen=True)
class AssembleIdsOutput:
    prior_art: list[models.PriorArt]
    citations: list[models.Citation]


class AssembleIDS:
    def __init__(
        self,
        prior_art_repo: ports.Repository[models.PriorArt],
        citation_repo: ports.Repository[models.Citation],
    ) -> None:
        self._prior_art_repo = prior_art_repo
        self._citation_repo = citation_repo

    def execute(self, data: AssembleIdsInput) -> AssembleIdsOutput:
        for item in data.prior_art:
            self._prior_art_repo.save(item)
        for citation in data.citations:
            self._citation_repo.save(citation)
        return AssembleIdsOutput(prior_art=data.prior_art, citations=data.citations)
