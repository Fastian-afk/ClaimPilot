"""
ClaimPilot — Intake Agent Processor
Handles initial intake of insurance claims, validates data,
processes documents, and creates Maestro Cases.
"""

from __future__ import annotations
import os, sys, time
from datetime import datetime, timedelta
from typing import Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))
from src.utils.models import *
from src.utils.logger import setup_logger, log_agent_action

logger = setup_logger("intake_agent")

REQUIRED_FIELDS = ["claimant_name", "policy_number", "claim_type", "description", "incident_date", "claimed_amount"]

class IntakeProcessor:
    """Processes incoming claims and creates Maestro cases."""

    def validate_submission(self, raw_data: dict) -> tuple[bool, list[str]]:
        errors = []
        for field in REQUIRED_FIELDS:
            if field not in raw_data or not raw_data[field]:
                errors.append(f"Missing required field: {field}")
        try:
            amount = float(raw_data.get("claimed_amount", 0))
            if amount <= 0: errors.append("Claimed amount must be > 0")
        except (ValueError, TypeError):
            errors.append("Invalid claimed amount")
        return len(errors) == 0, errors

    def extract_documents(self, document_list: list[dict]) -> list[ClaimDocument]:
        return [
            ClaimDocument(
                filename=d.get("filename", "unknown"),
                document_type=d.get("type", "other"),
                extracted_data=d.get("extracted_data"),
                confidence_score=d.get("confidence_score"),
            ) for d in document_list
        ]

    def create_case(self, raw_data: dict) -> Optional[CaseRecord]:
        """Main entry point: validate → extract docs → create case → route to triage."""
        start = time.time()
        is_valid, errors = self.validate_submission(raw_data)
        if not is_valid:
            logger.warning("intake_rejected", errors=errors)
            return None

        documents = self.extract_documents(raw_data.get("documents", []))
        claim = Claim(
            claim_type=ClaimType(raw_data["claim_type"].lower()),
            claimant=ClaimantInfo(
                full_name=raw_data["claimant_name"],
                email=raw_data.get("claimant_email", ""),
                phone=raw_data.get("claimant_phone", ""),
                policy_number=raw_data["policy_number"],
            ),
            description=raw_data["description"],
            incident_date=datetime.fromisoformat(raw_data["incident_date"]),
            claimed_amount=float(raw_data["claimed_amount"]),
            documents=documents,
        )

        case = CaseRecord(claim=claim, current_stage=CaseStage.INTAKE, status=ClaimStatus.RECEIVED, assigned_to="intake_agent")
        case.add_audit_entry("case_created", "intake_agent", f"New {claim.claim_type.value} claim. Amount: ${claim.claimed_amount:,.2f}")
        case.transition_to(CaseStage.TRIAGE, actor="intake_agent")

        log_agent_action(logger, case.case_id, "intake_complete", "case_created", (time.time()-start)*1000)
        return case
