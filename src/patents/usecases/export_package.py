from __future__ import annotations

from dataclasses import dataclass

from patents.adapters import ports
from patents.domain import models


@dataclass(frozen=True)
class ExportPackageInput:
    invention: models.Invention
    version: str


@dataclass(frozen=True)
class ExportPackageOutput:
    package: models.DocumentPackage


class ExportFilingPackage:
    def __init__(
        self,
        claim_repo: ports.Repository[models.Claim],
        section_repo: ports.Repository[models.SpecSection],
        figure_repo: ports.Repository[models.Figure],
        prior_art_repo: ports.Repository[models.PriorArt],
        citation_repo: ports.Repository[models.Citation],
        package_repo: ports.Repository[models.DocumentPackage],
        renderer: ports.DocumentRenderer,
        storage: ports.Storage,
        id_gen: ports.IdGenerator,
        clock: ports.Clock,
    ) -> None:
        self._claim_repo = claim_repo
        self._section_repo = section_repo
        self._figure_repo = figure_repo
        self._prior_art_repo = prior_art_repo
        self._citation_repo = citation_repo
        self._package_repo = package_repo
        self._renderer = renderer
        self._storage = storage
        self._id_gen = id_gen
        self._clock = clock

    def execute(self, data: ExportPackageInput) -> ExportPackageOutput:
        claims = list(self._claim_repo.list_by_invention(data.invention.id))
        sections = list(self._section_repo.list_by_invention(data.invention.id))
        figures = list(self._figure_repo.list_by_invention(data.invention.id))
        prior_art = list(self._prior_art_repo.list_by_invention(data.invention.id))
        citations = list(self._citation_repo.list_by_invention(data.invention.id))

        package = ports.FilingPackage(
            invention=data.invention,
            claims=claims,
            sections=sections,
            figures=figures,
            prior_art=prior_art,
            citations=citations,
        )

        artifacts: list[str] = []
        spec_blob = self._renderer.render_spec(package)
        claims_blob = self._renderer.render_claims(package)
        abstract_blob = self._renderer.render_abstract(package)
        ids_blob = self._renderer.render_ids(package)

        extension = self._renderer.file_extension
        artifacts.append(self._storage.put(self._path(data, "spec", extension), spec_blob))
        artifacts.append(self._storage.put(self._path(data, "claims", extension), claims_blob))
        artifacts.append(self._storage.put(self._path(data, "abstract", extension), abstract_blob))
        artifacts.append(self._storage.put(self._path(data, "ids", extension), ids_blob))

        doc_package = models.DocumentPackage(
            id=self._id_gen.new_id(),
            invention_id=data.invention.id,
            version=data.version,
            artifacts=artifacts,
            created_at=self._clock.now(),
        )
        self._package_repo.save(doc_package)
        return ExportPackageOutput(package=doc_package)

    @staticmethod
    def _path(data: ExportPackageInput, filename: str, extension: str) -> str:
        ext = extension.lstrip(".") if extension else "txt"
        return f"{data.invention.id}/{data.version}/{filename}.{ext}"
