from __future__ import annotations

from dataclasses import dataclass

from patents.adapters import ports
from patents.domain import models


@dataclass(frozen=True)
class GenerateClaimsInput:
    invention: models.Invention
    seed_text: str
    count: int = 5


@dataclass(frozen=True)
class GenerateClaimsOutput:
    claims: list[models.Claim]


class GenerateClaims:
    def __init__(
        self,
        claim_repo: ports.Repository[models.Claim],
        id_gen: ports.IdGenerator,
        clock: ports.Clock,
        llm: ports.LLMClient | None = None,
    ) -> None:
        self._claim_repo = claim_repo
        self._id_gen = id_gen
        self._clock = clock
        self._llm = llm

    def execute(self, data: GenerateClaimsInput) -> GenerateClaimsOutput:
        now = self._clock.now()
        claims: list[models.Claim] = []

        base_text = data.seed_text
        if self._llm is not None:
            prompt = (
                "Draft a set of patent claims based on this invention summary and seed text. "
                "Return one claim per line.\n\n"
                f"Title: {data.invention.title}\n"
                f"Summary: {data.invention.summary}\n"
                f"Seed: {data.seed_text}\n"
            )
            base_text = self._llm.generate(prompt).strip() or data.seed_text

        for idx in range(max(1, data.count)):
            claim_id = self._id_gen.new_id()
            if idx == 0:
                claim_text = f"A system comprising {base_text}."
                claim_type = models.ClaimType.INDEPENDENT
                depends_on: list[str] = []
            else:
                claim_text = f"The system of claim {idx} further comprising {base_text}."
                claim_type = models.ClaimType.DEPENDENT
                depends_on = [claims[0].id]

            claim = models.Claim(
                id=claim_id,
                invention_id=data.invention.id,
                text=claim_text,
                claim_type=claim_type,
                depends_on=depends_on,
                created_at=now,
            )
            self._claim_repo.save(claim)
            claims.append(claim)

        return GenerateClaimsOutput(claims=claims)
