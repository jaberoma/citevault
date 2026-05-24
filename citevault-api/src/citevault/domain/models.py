"""Citevault domain models. Pure dataclasses, no I/O."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class SourceKind(str, Enum):
    RESUME_MASTER = "resume_master"
    README = "readme"
    BLOG_POST = "blog_post"
    NOTE = "note"


class Source(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    kind: SourceKind
    path: str
    text: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Span(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    source_id: str
    start_offset: int
    end_offset: int
    text: str


class StructuredEntry(BaseModel):
    """Base class shared by Job/Project/Skill/Achievement."""

    model_config = ConfigDict(frozen=True)

    id: str
    source_id: str
    evidence_span_ids: list[str] = Field(default_factory=list)


class Job(StructuredEntry):
    company: str
    role: str
    start_date: str  # YYYY-MM
    end_date: str | None = None
    bullets: list[str] = Field(default_factory=list)


class Project(StructuredEntry):
    name: str
    role: str | None = None
    technologies: list[str] = Field(default_factory=list)
    bullets: list[str] = Field(default_factory=list)


class Skill(StructuredEntry):
    name: str


class Achievement(StructuredEntry):
    description: str


class Citation(BaseModel):
    model_config = ConfigDict(frozen=True)

    span_id: str | None = None
    structured_entry_id: str | None = None


class ClaimType(str, Enum):
    ACHIEVEMENT = "achievement"
    SKILL = "skill"
    EXPERIENCE = "experience"
    EDUCATION = "education"


class ClaimStatus(str, Enum):
    DRAFT = "DRAFT"
    VERIFIED = "VERIFIED"
    REWRITTEN = "REWRITTEN"
    REJECTED = "REJECTED"


class Claim(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    text: str
    claim_type: ClaimType
    citations: list[Citation] = Field(default_factory=list)
    status: ClaimStatus = ClaimStatus.DRAFT


class VerdictKind(str, Enum):
    SUPPORTS = "SUPPORTS"
    PARTIAL = "PARTIAL"
    UNCLEAR = "UNCLEAR"
    CONTRADICTS = "CONTRADICTS"


class VerificationResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    claim_id: str
    verdict: VerdictKind
    confidence: float
    explanation: str


class RequirementKind(str, Enum):
    MUST_HAVE = "must_have"
    NICE_TO_HAVE = "nice_to_have"


class Requirement(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    text: str
    kind: RequirementKind
    priority: int


class JobPosting(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    raw_text: str
    role_title: str | None = None
    company: str | None = None
    requirements: list[Requirement] = Field(default_factory=list)


class GapEntry(BaseModel):
    model_config = ConfigDict(frozen=True)

    requirement_text: str
    closest_evidence: str | None = None
    neutral_suggestion: str


class GapReport(BaseModel):
    model_config = ConfigDict(frozen=True)

    tailoring_id: str
    entries: list[GapEntry] = Field(default_factory=list)


class RetrievalCandidate(BaseModel):
    model_config = ConfigDict(frozen=True)

    span_id: str | None = None
    structured_entry_id: str | None = None
    text: str
    score: float
