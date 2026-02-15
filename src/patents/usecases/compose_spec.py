from __future__ import annotations

from dataclasses import dataclass

from patents.adapters import ports
from patents.domain import models


@dataclass(frozen=True)
class ComposeSpecInput:
    invention: models.Invention
    claims: list[models.Claim]
    notes: str = ""


@dataclass(frozen=True)
class ComposeSpecOutput:
    sections: list[models.SpecSection]


class ComposeSpecification:
    def __init__(
        self,
        section_repo: ports.Repository[models.SpecSection],
        id_gen: ports.IdGenerator,
        llm: ports.LLMClient | None = None,
    ) -> None:
        self._section_repo = section_repo
        self._id_gen = id_gen
        self._llm = llm

    def execute(self, data: ComposeSpecInput) -> ComposeSpecOutput:
        sections: list[models.SpecSection] = []
        seed = data.notes or data.invention.summary

        def make_text(label: str) -> str:
            if self._llm is None:
                return f"{label}: {seed}"
            prompt = (
                f"Draft the {label} section for a patent specification. "
                f"Title: {data.invention.title}\n"
                f"Summary: {data.invention.summary}\n"
                f"Notes: {data.notes}\n"
            )
            return self._llm.generate(prompt).strip() or f"{label}: {seed}"

        ordered = [
            (models.SpecSectionType.TITLE, data.invention.title),
            (models.SpecSectionType.FIELD, make_text("Field")),
            (models.SpecSectionType.BACKGROUND, make_text("Background")),
            (models.SpecSectionType.SUMMARY, make_text("Summary")),
            (models.SpecSectionType.BRIEF_DESCRIPTION, make_text("Brief Description")),
            (models.SpecSectionType.DETAILED_DESCRIPTION, make_text("Detailed Description")),
            (models.SpecSectionType.ABSTRACT, make_text("Abstract")),
        ]

        for idx, (section_type, text) in enumerate(ordered):
            section = models.SpecSection(
                id=self._id_gen.new_id(),
                invention_id=data.invention.id,
                section_type=section_type,
                text=text,
                order=idx,
            )
            self._section_repo.save(section)
            sections.append(section)

        return ComposeSpecOutput(sections=sections)
