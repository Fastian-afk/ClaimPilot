"""
ClaimPilot — Settlement Agent (Processor)
Handles final settlement: payment processing, confirmation, and case closure.
Runs as a low-code agent in UiPath Agent Builder.
"""

from __future__ import annotations
import os, sys, time
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))
from src.utils.models import *
from src.utils.logger import setup_logger, log_agent_action

logger = setup_logger("settlement_agent")


class SettlementProcessor:
    """Processes approved claims for settlement and payment."""

    def process_settlement(self, case: CaseRecord) -> SettlementResult:
        """
        Process settlement for an approved claim:
        1. Verify assessment is complete and approved
        2. Process payment via API Workflow
        3. Generate settlement confirmation
        4. Trigger notification RPA bot
        """
        start = time.time()
        claim = case.claim
        assessment = case.assessment

        if not assessment or not assessment.is_covered:
            logger.error("settlement_blocked", case_id=case.case_id, reason="No valid assessment")
            raise ValueError("Cannot settle: no valid assessment found")

        logger.info("settlement_started", case_id=case.case_id, payout=assessment.net_payout)

        # Process payment (in production, calls UiPath API Workflow → payment gateway)
        payment_result = self._process_payment(
            claim_id=claim.claim_id,
            amount=assessment.net_payout,
            recipient=claim.claimant.full_name,
            policy_number=claim.claimant.policy_number,
        )

        result = SettlementResult(
            claim_id=claim.claim_id,
            settlement_amount=assessment.net_payout,
            payment_method=payment_result["method"],
            payment_reference=payment_result["reference"],
            confirmation_sent=True,
        )

        # Update case
        case.settlement = result
        case.status = ClaimStatus.SETTLED
        case.transition_to(CaseStage.CLOSED, actor="settlement_agent")
        case.closed_at = datetime.utcnow()
        case.add_audit_entry(
            "settlement_processed", "settlement_agent",
            f"Payment of ${result.settlement_amount:,.2f} processed. Ref: {result.payment_reference}"
        )

        duration_ms = (time.time() - start) * 1000
        log_agent_action(logger, case.case_id, "settlement_complete", "paid", duration_ms,
                         amount=result.settlement_amount, ref=result.payment_reference)
        return result

    def _process_payment(self, claim_id: str, amount: float, recipient: str, policy_number: str) -> dict:
        """
        Simulate payment processing via UiPath API Workflow.
        In production, this triggers the API Workflow connected to the payment gateway.
        """
        import uuid
        logger.info("processing_payment", claim_id=claim_id, amount=amount, recipient=recipient)
        return {
            "reference": f"PAY-{str(uuid.uuid4())[:8].upper()}",
            "method": "bank_transfer",
            "status": "completed",
            "amount": amount,
        }

    def generate_rejection_notice(self, case: CaseRecord, reason: str) -> dict:
        """Generate a rejection notice for denied claims (triggered by RPA bot)."""
        case.status = ClaimStatus.REJECTED
        case.transition_to(CaseStage.CLOSED, actor="settlement_agent")
        case.closed_at = datetime.utcnow()
        case.add_audit_entry("claim_rejected", "settlement_agent", f"Rejection reason: {reason}")

        return {
            "claim_id": case.claim.claim_id,
            "recipient": case.claim.claimant.full_name,
            "email": case.claim.claimant.email,
            "subject": f"Claim {case.claim.claim_id} — Decision Notice",
            "reason": reason,
            "appeal_deadline": "30 days from notice date",
        }
