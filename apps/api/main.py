from __future__ import annotations

import os
from typing import Dict, Iterable, Optional

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from patents.adapters import ports
from patents.domain import models
from patents.infra.memory import SystemClock, UuidGenerator
from patents.infra.postgres import (
    CitationRepository,
    ClaimRepository,
    DisclosureRepository,
    DocumentPackageRepository,
    FigureRepository,
    InventionRepository,
    PriorArtRepository,
    SpecSectionRepository,
    ReviewRepository,
    create_engine_from_url,
    create_sessionmaker,
)
from patents.infra.renderer import DocxRenderer, PdfRenderer, SimpleTextRenderer
from patents.infra.storage import FileStorage
from patents.usecases.assemble_ids import AssembleIDS, AssembleIdsInput
from patents.usecases.compose_spec import ComposeSpecInput, ComposeSpecification
from patents.usecases.export_package import ExportFilingPackage, ExportPackageInput
from patents.usecases.generate_claims import GenerateClaims, GenerateClaimsInput
from patents.usecases.ingest_disclosure import IngestDisclosure, IngestDisclosureInput
from patents.usecases.run_review import RunReviewCycle, RunReviewInput


DATABASE_URL = os.getenv(
    "PATENTS_DATABASE_URL",
    "postgresql+psycopg://postgres:postgres@localhost:5432/patents",
)
STORAGE_DIR = os.getenv("PATENTS_STORAGE_DIR", "./output")
DEFAULT_RENDERER = os.getenv("PATENTS_RENDERER", "text").lower()
API_KEYS_RAW = os.getenv("PATENTS_API_KEYS", "")

engine = create_engine_from_url(DATABASE_URL)
SessionLocal = create_sessionmaker(engine)

app = FastAPI(title="Patents API", version="0.1.0")


def _parse_api_keys(value: str) -> Dict[str, str]:
    mapping: Dict[str, str] = {}
    for item in value.split(","):
        item = item.strip()
        if not item:
            continue
        if ":" not in item:
            continue
        key, role = item.split(":", 1)
        mapping[key.strip()] = role.strip()
    return mapping


API_KEYS = _parse_api_keys(API_KEYS_RAW)


def require_role(*allowed: str):
    def _dependency(api_key: Optional[str] = Header(None, alias="X-API-Key")) -> str:
        if not API_KEYS:
            return "anonymous"
        if not api_key or api_key not in API_KEYS:
            raise HTTPException(status_code=401, detail="Invalid API key")
        role = API_KEYS[api_key]
        if allowed and role not in allowed:
            raise HTTPException(status_code=403, detail="Insufficient role")
        return role

    return _dependency


class IngestDisclosureRequest(BaseModel):
    title: str
    summary: str
    inventors: list[str]
    disclosure_text: str
    source: str
    tags: list[str] = Field(default_factory=list)


class IngestDisclosureResponse(BaseModel):
    invention_id: str
    disclosure_id: str


class GenerateClaimsRequest(BaseModel):
    seed_text: str
    count: int = 5


class ClaimResponse(BaseModel):
    id: str
    text: str
    claim_type: str
    status: str
    depends_on: list[str]


class GenerateClaimsResponse(BaseModel):
    claims: list[ClaimResponse]


class ComposeSpecRequest(BaseModel):
    notes: str = ""


class SpecSectionResponse(BaseModel):
    id: str
    section_type: str
    text: str
    order: int


class ComposeSpecResponse(BaseModel):
    sections: list[SpecSectionResponse]


class ReviewRequest(BaseModel):
    reviewer: str
    decision: str
    notes: Optional[str] = None


class PriorArtInput(BaseModel):
    id: Optional[str] = None
    title: str
    url: Optional[str] = None
    publication_date: Optional[str] = None
    summary: str
    tags: list[str] = Field(default_factory=list)


class CitationInput(BaseModel):
    id: Optional[str] = None
    prior_art_id: str
    location: str
    quote: str


class AssembleIdsRequest(BaseModel):
    prior_art: list[PriorArtInput] = Field(default_factory=list)
    citations: list[CitationInput] = Field(default_factory=list)


class ExportPackageRequest(BaseModel):
    version: str
    format: Optional[str] = None


class ExportPackageResponse(BaseModel):
    package_id: str
    artifacts: list[str]


class HealthResponse(BaseModel):
    status: str


def get_session() -> Iterable[Session]:
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")


def _get_invention(session: Session, invention_id: str) -> models.Invention:
    invention_repo = InventionRepository(session)
    invention = invention_repo.get(invention_id)
    if invention is None:
        raise HTTPException(status_code=404, detail="Invention not found")
    return invention


def _resolve_renderer(format_override: Optional[str]) -> ports.DocumentRenderer:
    key = (format_override or DEFAULT_RENDERER).lower()
    if key == "docx":
        return DocxRenderer()
    if key == "pdf":
        return PdfRenderer()
    return SimpleTextRenderer()


@app.post("/inventions", response_model=IngestDisclosureResponse)
def create_invention(
    payload: IngestDisclosureRequest,
    session: Session = Depends(get_session),
    role: str = Depends(require_role("inventor", "engineer", "attorney", "admin")),
) -> IngestDisclosureResponse:
    clock = SystemClock()
    id_gen = UuidGenerator()

    invention_repo = InventionRepository(session)
    disclosure_repo = DisclosureRepository(session)

    usecase = IngestDisclosure(invention_repo, disclosure_repo, id_gen, clock)
    result = usecase.execute(
        IngestDisclosureInput(
            title=payload.title,
            summary=payload.summary,
            inventors=payload.inventors,
            disclosure_text=payload.disclosure_text,
            source=payload.source,
            tags=payload.tags,
        )
    )

    return IngestDisclosureResponse(
        invention_id=result.invention.id, disclosure_id=result.disclosure.id
    )


@app.post("/inventions/{invention_id}/claims", response_model=GenerateClaimsResponse)
def generate_claims(
    invention_id: str,
    payload: GenerateClaimsRequest,
    session: Session = Depends(get_session),
    role: str = Depends(require_role("engineer", "attorney", "admin")),
) -> GenerateClaimsResponse:
    invention = _get_invention(session, invention_id)
    clock = SystemClock()
    id_gen = UuidGenerator()

    claim_repo = ClaimRepository(session)
    usecase = GenerateClaims(claim_repo, id_gen, clock)
    result = usecase.execute(
        GenerateClaimsInput(
            invention=invention,
            seed_text=payload.seed_text,
            count=payload.count,
        )
    )

    claims = [
        ClaimResponse(
            id=claim.id,
            text=claim.text,
            claim_type=claim.claim_type.value,
            status=claim.status.value,
            depends_on=list(claim.depends_on),
        )
        for claim in result.claims
    ]
    return GenerateClaimsResponse(claims=claims)


@app.post("/inventions/{invention_id}/spec", response_model=ComposeSpecResponse)
def compose_spec(
    invention_id: str,
    payload: ComposeSpecRequest,
    session: Session = Depends(get_session),
    role: str = Depends(require_role("engineer", "attorney", "admin")),
) -> ComposeSpecResponse:
    invention = _get_invention(session, invention_id)
    id_gen = UuidGenerator()

    claim_repo = ClaimRepository(session)
    section_repo = SpecSectionRepository(session)

    claims = list(claim_repo.list_by_invention(invention_id))
    usecase = ComposeSpecification(section_repo, id_gen)
    result = usecase.execute(
        ComposeSpecInput(invention=invention, claims=claims, notes=payload.notes)
    )

    sections = [
        SpecSectionResponse(
            id=section.id,
            section_type=section.section_type.value,
            text=section.text,
            order=section.order,
        )
        for section in result.sections
    ]
    return ComposeSpecResponse(sections=sections)


@app.post("/inventions/{invention_id}/review")
def review_invention(
    invention_id: str,
    payload: ReviewRequest,
    session: Session = Depends(get_session),
    role: str = Depends(require_role("reviewer", "attorney", "admin")),
) -> dict:
    invention = _get_invention(session, invention_id)
    clock = SystemClock()
    id_gen = UuidGenerator()

    review_repo = ReviewRepository(session)
    usecase = RunReviewCycle(review_repo, id_gen, clock)
    try:
        decision = models.ReviewDecision(payload.decision)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid decision") from exc

    result = usecase.execute(
        RunReviewInput(
            invention=invention,
            reviewer=payload.reviewer,
            decision=decision,
            notes=payload.notes,
        )
    )

    return {"review_id": result.review.id, "decision": result.review.decision.value}


@app.post("/inventions/{invention_id}/ids")
def assemble_ids(
    invention_id: str,
    payload: AssembleIdsRequest,
    session: Session = Depends(get_session),
    role: str = Depends(require_role("analyst", "attorney", "admin")),
) -> dict:
    invention = _get_invention(session, invention_id)
    id_gen = UuidGenerator()

    prior_art_repo = PriorArtRepository(session)
    citation_repo = CitationRepository(session)
    usecase = AssembleIDS(prior_art_repo, citation_repo)

    prior_art = [
        models.PriorArt(
            id=item.id or id_gen.new_id(),
            invention_id=invention_id,
            title=item.title,
            url=item.url,
            publication_date=item.publication_date,
            summary=item.summary,
            tags=item.tags,
        )
        for item in payload.prior_art
    ]

    citations = [
        models.Citation(
            id=item.id or id_gen.new_id(),
            invention_id=invention_id,
            prior_art_id=item.prior_art_id,
            location=item.location,
            quote=item.quote,
        )
        for item in payload.citations
    ]

    result = usecase.execute(
        AssembleIdsInput(invention=invention, prior_art=prior_art, citations=citations)
    )

    return {"prior_art": len(result.prior_art), "citations": len(result.citations)}


@app.post("/inventions/{invention_id}/export", response_model=ExportPackageResponse)
def export_package(
    invention_id: str,
    payload: ExportPackageRequest,
    session: Session = Depends(get_session),
    role: str = Depends(require_role("attorney", "admin")),
) -> ExportPackageResponse:
    invention = _get_invention(session, invention_id)
    clock = SystemClock()
    id_gen = UuidGenerator()

    claim_repo = ClaimRepository(session)
    section_repo = SpecSectionRepository(session)
    figure_repo = FigureRepository(session)
    prior_art_repo = PriorArtRepository(session)
    citation_repo = CitationRepository(session)
    package_repo = DocumentPackageRepository(session)

    renderer = _resolve_renderer(payload.format)
    storage = FileStorage(STORAGE_DIR)

    usecase = ExportFilingPackage(
        claim_repo,
        section_repo,
        figure_repo,
        prior_art_repo,
        citation_repo,
        package_repo,
        renderer,
        storage,
        id_gen,
        clock,
    )

    result = usecase.execute(
        ExportPackageInput(invention=invention, version=payload.version)
    )
    return ExportPackageResponse(
        package_id=result.package.id, artifacts=result.package.artifacts
    )
