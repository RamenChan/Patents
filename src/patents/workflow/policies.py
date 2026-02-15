from __future__ import annotations

from dataclasses import dataclass

from patents.domain import models


@dataclass(frozen=True)
class ReadinessReport:
    ready: bool
    missing: list[str]


def check_filing_readiness(
    invention: models.Invention,
    claims: list[models.Claim],
    sections: list[models.SpecSection],
) -> ReadinessReport:
    missing: list[str] = []
    if not invention.title:
        missing.append("title")
    if not claims:
        missing.append("claims")
    if not sections:
        missing.append("specification")
    return ReadinessReport(ready=not missing, missing=missing)
