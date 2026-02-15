from __future__ import annotations

from dataclasses import dataclass

from patents.adapters import ports
from patents.domain import models


@dataclass(frozen=True)
class RunReviewInput:
    invention: models.Invention
    reviewer: str
    decision: models.ReviewDecision
    notes: str | None


@dataclass(frozen=True)
class RunReviewOutput:
    review: models.Review


class RunReviewCycle:
    def __init__(
        self,
        review_repo: ports.Repository[models.Review],
        id_gen: ports.IdGenerator,
        clock: ports.Clock,
    ) -> None:
        self._review_repo = review_repo
        self._id_gen = id_gen
        self._clock = clock

    def execute(self, data: RunReviewInput) -> RunReviewOutput:
        review = models.Review(
            id=self._id_gen.new_id(),
            invention_id=data.invention.id,
            reviewer=data.reviewer,
            decision=data.decision,
            notes=data.notes,
            created_at=self._clock.now(),
        )
        self._review_repo.save(review)
        return RunReviewOutput(review=review)
