from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional


class ClaimType(str, Enum):
    INDEPENDENT = "independent"
    DEPENDENT = "dependent"


class ClaimStatus(str, Enum):
    DRAFT = "draft"
    FINAL = "final"


class SpecSectionType(str, Enum):
    TITLE = "title"
    FIELD = "field"
    BACKGROUND = "background"
    SUMMARY = "summary"
    BRIEF_DESCRIPTION = "brief_description"
    DETAILED_DESCRIPTION = "detailed_description"
    ABSTRACT = "abstract"


class ReviewDecision(str, Enum):
    APPROVE = "approve"
    REVISE = "revise"
    REJECT = "reject"


class DocketStatus(str, Enum):
    OPEN = "open"
    SUBMITTED = "submitted"
    CLOSED = "closed"


@dataclass(frozen=True)
class Invention:
    id: str
    title: str
    summary: str
    inventors: List[str]
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass(frozen=True)
class Disclosure:
    id: str
    invention_id: str
    text: str
    source: str
    attachments: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass(frozen=True)
class PriorArt:
    id: str
    invention_id: str
    title: str
    url: Optional[str]
    publication_date: Optional[str]
    summary: str
    tags: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class Citation:
    id: str
    invention_id: str
    prior_art_id: str
    location: str
    quote: str


@dataclass(frozen=True)
class Claim:
    id: str
    invention_id: str
    text: str
    claim_type: ClaimType
    status: ClaimStatus = ClaimStatus.DRAFT
    depends_on: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass(frozen=True)
class SpecSection:
    id: str
    invention_id: str
    section_type: SpecSectionType
    text: str
    order: int


@dataclass(frozen=True)
class Figure:
    id: str
    invention_id: str
    label: str
    caption: str
    file_ref: str


@dataclass(frozen=True)
class DocketItem:
    id: str
    invention_id: str
    jurisdiction: str
    due_date: str
    status: DocketStatus = DocketStatus.OPEN
    notes: Optional[str] = None


@dataclass(frozen=True)
class Review:
    id: str
    invention_id: str
    reviewer: str
    decision: ReviewDecision
    notes: Optional[str]
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass(frozen=True)
class DocumentPackage:
    id: str
    invention_id: str
    version: str
    artifacts: List[str]
    created_at: datetime = field(default_factory=datetime.utcnow)
