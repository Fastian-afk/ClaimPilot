"""Tests for data models."""
import pytest
from datetime import datetime
from src.utils.models import *


class TestCaseRecord:
    def test_audit_logging(self):
        claim = Claim(
            claim_type=ClaimType.AUTO,
            claimant=ClaimantInfo(full_name="Test", email="t@t.com", phone="555", policy_number="POL-1"),
            description="Test", incident_date=datetime.utcnow(), claimed_amount=1000,
        )
        case = CaseRecord(claim=claim)
        case.add_audit_entry("test_action", "test_actor", "test details")
        assert len(case.audit_log) == 1
        assert case.audit_log[0]["action"] == "test_action"

    def test_stage_transition(self):
        claim = Claim(
            claim_type=ClaimType.AUTO,
            claimant=ClaimantInfo(full_name="Test", email="t@t.com", phone="555", policy_number="POL-1"),
            description="Test", incident_date=datetime.utcnow(), claimed_amount=1000,
        )
        case = CaseRecord(claim=claim, current_stage=CaseStage.INTAKE)
        case.transition_to(CaseStage.TRIAGE, actor="test")
        assert case.current_stage == CaseStage.TRIAGE
        assert len(case.audit_log) == 1

    def test_claim_id_format(self):
        claim = Claim(
            claim_type=ClaimType.AUTO,
            claimant=ClaimantInfo(full_name="Test", email="t@t.com", phone="555", policy_number="POL-1"),
            description="Test", incident_date=datetime.utcnow(), claimed_amount=1000,
        )
        assert claim.claim_id.startswith("CLM-")
