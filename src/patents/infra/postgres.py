from __future__ import annotations

from contextlib import contextmanager
from typing import Callable, Dict, Iterable, Optional, Sequence, TypeVar

from sqlalchemy import Column, DateTime, ForeignKey, Integer, MetaData, String, Table, Text, create_engine, select
from sqlalchemy.dialects.postgresql import JSONB, insert
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from patents.adapters import ports
from patents.domain import models


metadata = MetaData()

inventions = Table(
    "inventions",
    metadata,
    Column("id", String, primary_key=True),
    Column("title", String, nullable=False),
    Column("summary", Text, nullable=False),
    Column("inventors", JSONB, nullable=False),
    Column("tags", JSONB, nullable=False, default=list),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
)

disclosures = Table(
    "disclosures",
    metadata,
    Column("id", String, primary_key=True),
    Column("invention_id", String, ForeignKey("inventions.id"), nullable=False),
    Column("text", Text, nullable=False),
    Column("source", String, nullable=False),
    Column("attachments", JSONB, nullable=False, default=list),
    Column("created_at", DateTime(timezone=True), nullable=False),
)

claims = Table(
    "claims",
    metadata,
    Column("id", String, primary_key=True),
    Column("invention_id", String, ForeignKey("inventions.id"), nullable=False),
    Column("text", Text, nullable=False),
    Column("claim_type", String, nullable=False),
    Column("status", String, nullable=False),
    Column("depends_on", JSONB, nullable=False, default=list),
    Column("created_at", DateTime(timezone=True), nullable=False),
)

spec_sections = Table(
    "spec_sections",
    metadata,
    Column("id", String, primary_key=True),
    Column("invention_id", String, ForeignKey("inventions.id"), nullable=False),
    Column("section_type", String, nullable=False),
    Column("text", Text, nullable=False),
    Column("section_order", Integer, nullable=False),
)

figures = Table(
    "figures",
    metadata,
    Column("id", String, primary_key=True),
    Column("invention_id", String, ForeignKey("inventions.id"), nullable=False),
    Column("label", String, nullable=False),
    Column("caption", Text, nullable=False),
    Column("file_ref", String, nullable=False),
)

prior_art = Table(
    "prior_art",
    metadata,
    Column("id", String, primary_key=True),
    Column("invention_id", String, ForeignKey("inventions.id"), nullable=False),
    Column("title", String, nullable=False),
    Column("url", String, nullable=True),
    Column("publication_date", String, nullable=True),
    Column("summary", Text, nullable=False),
    Column("tags", JSONB, nullable=False, default=list),
)

citations = Table(
    "citations",
    metadata,
    Column("id", String, primary_key=True),
    Column("invention_id", String, ForeignKey("inventions.id"), nullable=False),
    Column("prior_art_id", String, ForeignKey("prior_art.id"), nullable=False),
    Column("location", String, nullable=False),
    Column("quote", Text, nullable=False),
)

reviews = Table(
    "reviews",
    metadata,
    Column("id", String, primary_key=True),
    Column("invention_id", String, ForeignKey("inventions.id"), nullable=False),
    Column("reviewer", String, nullable=False),
    Column("decision", String, nullable=False),
    Column("notes", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
)

document_packages = Table(
    "document_packages",
    metadata,
    Column("id", String, primary_key=True),
    Column("invention_id", String, ForeignKey("inventions.id"), nullable=False),
    Column("version", String, nullable=False),
    Column("artifacts", JSONB, nullable=False, default=list),
    Column("created_at", DateTime(timezone=True), nullable=False),
)

docket_items = Table(
    "docket_items",
    metadata,
    Column("id", String, primary_key=True),
    Column("invention_id", String, ForeignKey("inventions.id"), nullable=False),
    Column("jurisdiction", String, nullable=False),
    Column("due_date", String, nullable=False),
    Column("status", String, nullable=False),
    Column("notes", Text, nullable=True),
)


def create_engine_from_url(database_url: str) -> Engine:
    return create_engine(database_url, future=True)


def create_sessionmaker(engine: Engine) -> sessionmaker:
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


@contextmanager
def session_scope(SessionLocal: sessionmaker) -> Iterable[Session]:
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


T = TypeVar("T")


class _BaseRepository(ports.Repository[T]):
    def __init__(
        self,
        session: Session,
        table: Table,
        to_model: Callable[[Dict], T],
        from_model: Callable[[T], Dict],
        invention_id_column: Optional[str],
    ) -> None:
        self._session = session
        self._table = table
        self._to_model = to_model
        self._from_model = from_model
        self._invention_id_column = invention_id_column

    def get(self, entity_id: str) -> Optional[T]:
        row = (
            self._session.execute(
                select(self._table).where(self._table.c.id == entity_id)
            )
            .mappings()
            .first()
        )
        return self._to_model(row) if row else None

    def list_by_invention(self, invention_id: str) -> Sequence[T]:
        if self._invention_id_column is None:
            return []
        column = getattr(self._table.c, self._invention_id_column)
        rows = (
            self._session.execute(select(self._table).where(column == invention_id))
            .mappings()
            .all()
        )
        return [self._to_model(row) for row in rows]

    def save(self, entity: T) -> None:
        data = self._from_model(entity)
        stmt = insert(self._table).values(**data)
        stmt = stmt.on_conflict_do_update(index_elements=[self._table.c.id], set_=data)
        self._session.execute(stmt)


class InventionRepository(_BaseRepository[models.Invention]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, inventions, _to_invention, _from_invention, None)

    def list_by_invention(self, invention_id: str) -> Sequence[models.Invention]:
        item = self.get(invention_id)
        return [item] if item else []


class DisclosureRepository(_BaseRepository[models.Disclosure]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, disclosures, _to_disclosure, _from_disclosure, "invention_id")


class ClaimRepository(_BaseRepository[models.Claim]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, claims, _to_claim, _from_claim, "invention_id")


class SpecSectionRepository(_BaseRepository[models.SpecSection]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, spec_sections, _to_spec_section, _from_spec_section, "invention_id")


class FigureRepository(_BaseRepository[models.Figure]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, figures, _to_figure, _from_figure, "invention_id")


class PriorArtRepository(_BaseRepository[models.PriorArt]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, prior_art, _to_prior_art, _from_prior_art, "invention_id")


class CitationRepository(_BaseRepository[models.Citation]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, citations, _to_citation, _from_citation, "invention_id")


class ReviewRepository(_BaseRepository[models.Review]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, reviews, _to_review, _from_review, "invention_id")


class DocumentPackageRepository(_BaseRepository[models.DocumentPackage]):
    def __init__(self, session: Session) -> None:
        super().__init__(
            session, document_packages, _to_document_package, _from_document_package, "invention_id"
        )


class DocketItemRepository(_BaseRepository[models.DocketItem]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, docket_items, _to_docket_item, _from_docket_item, "invention_id")


# Mapping helpers


def _to_invention(row: Dict) -> models.Invention:
    return models.Invention(
        id=row["id"],
        title=row["title"],
        summary=row["summary"],
        inventors=list(row.get("inventors") or []),
        tags=list(row.get("tags") or []),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _from_invention(model: models.Invention) -> Dict:
    return {
        "id": model.id,
        "title": model.title,
        "summary": model.summary,
        "inventors": list(model.inventors),
        "tags": list(model.tags),
        "created_at": model.created_at,
        "updated_at": model.updated_at,
    }


def _to_disclosure(row: Dict) -> models.Disclosure:
    return models.Disclosure(
        id=row["id"],
        invention_id=row["invention_id"],
        text=row["text"],
        source=row["source"],
        attachments=list(row.get("attachments") or []),
        created_at=row["created_at"],
    )


def _from_disclosure(model: models.Disclosure) -> Dict:
    return {
        "id": model.id,
        "invention_id": model.invention_id,
        "text": model.text,
        "source": model.source,
        "attachments": list(model.attachments),
        "created_at": model.created_at,
    }


def _to_claim(row: Dict) -> models.Claim:
    return models.Claim(
        id=row["id"],
        invention_id=row["invention_id"],
        text=row["text"],
        claim_type=models.ClaimType(row["claim_type"]),
        status=models.ClaimStatus(row["status"]),
        depends_on=list(row.get("depends_on") or []),
        created_at=row["created_at"],
    )


def _from_claim(model: models.Claim) -> Dict:
    return {
        "id": model.id,
        "invention_id": model.invention_id,
        "text": model.text,
        "claim_type": model.claim_type.value,
        "status": model.status.value,
        "depends_on": list(model.depends_on),
        "created_at": model.created_at,
    }


def _to_spec_section(row: Dict) -> models.SpecSection:
    return models.SpecSection(
        id=row["id"],
        invention_id=row["invention_id"],
        section_type=models.SpecSectionType(row["section_type"]),
        text=row["text"],
        order=row["section_order"],
    )


def _from_spec_section(model: models.SpecSection) -> Dict:
    return {
        "id": model.id,
        "invention_id": model.invention_id,
        "section_type": model.section_type.value,
        "text": model.text,
        "section_order": model.order,
    }


def _to_figure(row: Dict) -> models.Figure:
    return models.Figure(
        id=row["id"],
        invention_id=row["invention_id"],
        label=row["label"],
        caption=row["caption"],
        file_ref=row["file_ref"],
    )


def _from_figure(model: models.Figure) -> Dict:
    return {
        "id": model.id,
        "invention_id": model.invention_id,
        "label": model.label,
        "caption": model.caption,
        "file_ref": model.file_ref,
    }


def _to_prior_art(row: Dict) -> models.PriorArt:
    return models.PriorArt(
        id=row["id"],
        invention_id=row["invention_id"],
        title=row["title"],
        url=row.get("url"),
        publication_date=row.get("publication_date"),
        summary=row["summary"],
        tags=list(row.get("tags") or []),
    )


def _from_prior_art(model: models.PriorArt) -> Dict:
    return {
        "id": model.id,
        "invention_id": model.invention_id,
        "title": model.title,
        "url": model.url,
        "publication_date": model.publication_date,
        "summary": model.summary,
        "tags": list(model.tags),
    }


def _to_citation(row: Dict) -> models.Citation:
    return models.Citation(
        id=row["id"],
        invention_id=row["invention_id"],
        prior_art_id=row["prior_art_id"],
        location=row["location"],
        quote=row["quote"],
    )


def _from_citation(model: models.Citation) -> Dict:
    return {
        "id": model.id,
        "invention_id": model.invention_id,
        "prior_art_id": model.prior_art_id,
        "location": model.location,
        "quote": model.quote,
    }


def _to_review(row: Dict) -> models.Review:
    return models.Review(
        id=row["id"],
        invention_id=row["invention_id"],
        reviewer=row["reviewer"],
        decision=models.ReviewDecision(row["decision"]),
        notes=row.get("notes"),
        created_at=row["created_at"],
    )


def _from_review(model: models.Review) -> Dict:
    return {
        "id": model.id,
        "invention_id": model.invention_id,
        "reviewer": model.reviewer,
        "decision": model.decision.value,
        "notes": model.notes,
        "created_at": model.created_at,
    }


def _to_document_package(row: Dict) -> models.DocumentPackage:
    return models.DocumentPackage(
        id=row["id"],
        invention_id=row["invention_id"],
        version=row["version"],
        artifacts=list(row.get("artifacts") or []),
        created_at=row["created_at"],
    )


def _from_document_package(model: models.DocumentPackage) -> Dict:
    return {
        "id": model.id,
        "invention_id": model.invention_id,
        "version": model.version,
        "artifacts": list(model.artifacts),
        "created_at": model.created_at,
    }


def _to_docket_item(row: Dict) -> models.DocketItem:
    return models.DocketItem(
        id=row["id"],
        invention_id=row["invention_id"],
        jurisdiction=row["jurisdiction"],
        due_date=row["due_date"],
        status=models.DocketStatus(row["status"]),
        notes=row.get("notes"),
    )


def _from_docket_item(model: models.DocketItem) -> Dict:
    return {
        "id": model.id,
        "invention_id": model.invention_id,
        "jurisdiction": model.jurisdiction,
        "due_date": model.due_date,
        "status": model.status.value,
        "notes": model.notes,
    }
