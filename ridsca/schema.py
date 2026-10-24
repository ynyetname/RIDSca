from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Finding(Strict):
    id: str
    category: str
    source: str
    title: str
    detail: str
    excerpt: str = ""
    weight: int = Field(default=0, ge=0, le=100)
    method: str = "rule"


class Check(Strict):
    component: str
    status: Literal["complete", "partial", "unavailable", "skipped", "failed"]
    detail: str
    source: str = "case"


class MediaSignal(Strict):
    source: str
    modality: str
    model: str
    raw_score: float = Field(ge=0, le=1)
    start: float | None = None
    end: float | None = None
    label: str = "experimental synthetic-content score; not a probability of fraud"


class Reference(Strict):
    id: str
    title: str
    text: str
    url: str
    score: float = 0
    reviewed_on: str


class ParsedInput(Strict):
    source: str
    kind: str
    text: str = ""
    qr: list[str] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)
    checks: list[Check] = Field(default_factory=list)


class Report(Strict):
    case_id: str
    created_at: str
    mode: str
    risk_score: int | None = None
    risk_band: str = "Inconclusive"
    summary: str
    findings: list[Finding] = Field(default_factory=list)
    checks: list[Check] = Field(default_factory=list)
    media: list[MediaSignal] = Field(default_factory=list)
    references: list[Reference] = Field(default_factory=list)
    actions: list[str] = Field(default_factory=list)
    inputs: list[dict] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)


class SemanticFinding(Strict):
    category: Literal[
        "credentials", "urgency", "remote_access", "advance_fee", "guaranteed_returns", "apk_install"
    ]
    quote: str = Field(min_length=3, max_length=350)


class SemanticResponse(Strict):
    findings: list[SemanticFinding] = Field(default_factory=list, max_length=6)


class ChatSelection(Strict):
    topic: Literal["findings", "actions", "media", "limits", "sources", "out_of_scope"]
    finding_ids: list[str] = Field(default_factory=list, max_length=6)


class EvidenceAudit(Strict):
    supported: bool
