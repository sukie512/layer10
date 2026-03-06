from dataclasses import dataclass, field
from typing import Optional

ENTITY_TYPES = {
    "Person": "A human individual",
    "Organization": "A company, team, or department",
    "Project": "A project, initiative, or product",
    "FinancialItem": "Revenue target, debt amount, partnership, etc.",
    "Role": "A job title or organisational role",
    "Event": "A discrete event (resignation, restatement, etc.)",
}

CLAIM_TYPES = {
    "HOLDS_ROLE": "Person currently holds a Role",
    "HELD_ROLE": "Person historically held a Role (superseded)",
    "WORKS_AT": "Person works at Organization",
    "SENT_MESSAGE": "Person sent a message",
    "RESIGNED": "Person resigned from a Role",
    "HAS_REVENUE_TARGET": "Organization has a revenue target",
    "HAS_DEBT": "Organization has off-balance-sheet debt",
    "INVOLVES_STRUCTURE": "Entity involves a financial structure",
    "DECISION_MADE": "A decision was made",
    "DECISION_REVERSED": "A previously made decision was reversed",
    "CONCERN_RAISED": "A concern or whistleblower claim was raised",
    "RESTATEMENT": "Financial restatement announced",
    "RELATED_TO": "Generic relationship between two entities",
}

@dataclass
class RawArtifact:
    artifact_id: str
    source_type: str
    timestamp: str
    content: str
    metadata: dict
    redacted: bool = False
    ingest_version: str = "v1.0"

@dataclass
class Evidence:
    evidence_id: str
    artifact_id: str
    excerpt: str
    char_start: int
    char_end: int
    timestamp: str

@dataclass
class Entity:
    entity_id: str
    entity_type: str
    canonical_name: str
    aliases: list = field(default_factory=list)
    merged_from: list = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    created_at: str = ""
    updated_at: str = ""

@dataclass
class Claim:
    claim_id: str
    claim_type: str
    subject_id: str
    object_id: Optional[str]
    object_value: Optional[str]
    evidence_ids: list
    confidence: float
    valid_from: Optional[str]
    valid_to: Optional[str]
    superseded_by: Optional[str] = None
    extraction_version: str = "v1.0"
    extracted_at: str = ""
    notes: str = ""
