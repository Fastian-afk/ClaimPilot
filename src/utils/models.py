"""
ClaimPilot — Data Models
Pydantic models for claims, cases, and agent communication.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ──────────────────────────────────────────────
# Enums
# ──────────────────────────────────────────────

class ClaimType(str, Enum):
    """Types of insurance claims."""
    AUTO = "auto"
    PROPERTY = "property"
    HEALTH = "health"
    LIABILITY = "liability"
    LIFE = "life"


class CaseStage(str, Enum):
    """Maestro Case lifecycle stages."""
    INTAKE = "intake"
    TRIAGE = "triage"
    INVESTIGATION = "investigation"
    ASSESSMENT = "assessment"
    SETTLEMENT = "settlement"
    CLOSED = "closed"


class RiskLevel(str, Enum):
    """Fraud risk classification."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ClaimStatus(str, Enum):
    """Overall claim processing status."""
    RECEIVED = "received"
    IN_REVIEW = "in_review"
    INVESTIGATING = "investigating"
    APPROVED = "approved"
    REJECTED = "rejected"
    ESCALATED = "escalated"
    SETTLED = "settled"
    CLOSED = "closed"


class DecisionOutcome(str, Enum):
    """Human adjuster decision outcomes."""
    APPROVE = "approve"
    REJECT = "reject"
    ESCALATE = "escalate"
    REQUEST_INFO = "request_info"


# ──────────────────────────────────────────────
# Core Models
# ──────────────────────────────────────────────

class ClaimantInfo(BaseModel):
    """Information about the person filing the claim."""
    claimant_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    full_name: str
    email: str
    phone: str
    policy_number: str
    address: Optional[str] = None


class ClaimDocument(BaseModel):
    """A document attached to a claim."""
    document_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    filename: str
    document_type: str  # e.g., "claim_form", "photo", "medical_report", "invoice"
    extracted_data: Optional[dict] = None
    confidence_score: Optional[float] = None
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)


class Claim(BaseModel):
    """An insurance claim submitted for processing."""
    claim_id: str = Field(default_factory=lambda: f"CLM-{str(uuid.uuid4())[:8].upper()}")
    claim_type: ClaimType
    claimant: ClaimantInfo
    description: str
    incident_date: datetime
    claimed_amount: float
    documents: list[ClaimDocument] = []
    submitted_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict = {}


class FraudSignal(BaseModel):
    """A single fraud indicator detected during analysis."""
    signal_type: str  # e.g., "velocity", "duplicate", "amount_outlier"
    description: str
    severity: float  # 0.0 to 1.0
    evidence: dict = {}


class FraudAnalysisResult(BaseModel):
    """Output of the Fraud Detection Agent."""
    claim_id: str
    risk_score: float  # 0.0 to 1.0
    risk_level: RiskLevel
    signals: list[FraudSignal] = []
    recommendation: str
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)
    model_version: str = "1.0.0"


class PolicyInfo(BaseModel):
    """Insurance policy details from external policy database."""
    policy_number: str
    holder_name: str
    policy_type: str
    coverage_limit: float
    deductible: float
    effective_date: datetime
    expiry_date: datetime
    is_active: bool = True
    exclusions: list[str] = []


class AssessmentResult(BaseModel):
    """Output of the Assessment Agent."""
    claim_id: str
    policy: PolicyInfo
    is_covered: bool
    coverage_amount: float
    deductible_applied: float
    net_payout: float
    assessment_notes: str
    requires_human_review: bool = False
    assessed_at: datetime = Field(default_factory=datetime.utcnow)


class SettlementResult(BaseModel):
    """Output of the Settlement Agent."""
    claim_id: str
    settlement_amount: float
    payment_method: str
    payment_reference: str = Field(default_factory=lambda: f"PAY-{str(uuid.uuid4())[:8].upper()}")
    settled_at: datetime = Field(default_factory=datetime.utcnow)
    confirmation_sent: bool = False


class HumanDecision(BaseModel):
    """A decision made by a human adjuster via Action Center."""
    claim_id: str
    adjuster_id: str
    adjuster_name: str
    decision: DecisionOutcome
    reason: str
    notes: Optional[str] = None
    decided_at: datetime = Field(default_factory=datetime.utcnow)


class CaseRecord(BaseModel):
    """
    The master case record in Maestro — tracks the full lifecycle of a claim.
    This maps to a UiPath Maestro Case instance.
    """
    case_id: str = Field(default_factory=lambda: f"CASE-{str(uuid.uuid4())[:8].upper()}")
    claim: Claim
    current_stage: CaseStage = CaseStage.INTAKE
    status: ClaimStatus = ClaimStatus.RECEIVED
    assigned_to: Optional[str] = None
    fraud_analysis: Optional[FraudAnalysisResult] = None
    assessment: Optional[AssessmentResult] = None
    settlement: Optional[SettlementResult] = None
    human_decisions: list[HumanDecision] = []
    audit_log: list[dict] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    closed_at: Optional[datetime] = None
    sla_deadline: Optional[datetime] = None

    def add_audit_entry(self, action: str, actor: str, details: str = "") -> None:
        """Add an entry to the case audit log."""
        self.audit_log.append({
            "timestamp": datetime.utcnow().isoformat(),
            "action": action,
            "actor": actor,
            "details": details,
            "stage": self.current_stage.value,
        })
        self.updated_at = datetime.utcnow()

    def transition_to(self, new_stage: CaseStage, actor: str) -> None:
        """Move the case to a new stage with audit logging."""
        old_stage = self.current_stage
        self.current_stage = new_stage
        self.add_audit_entry(
            action=f"stage_transition",
            actor=actor,
            details=f"Transitioned from {old_stage.value} to {new_stage.value}",
        )
