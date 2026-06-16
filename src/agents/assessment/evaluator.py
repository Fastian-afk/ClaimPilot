"""
ClaimPilot — Assessment Agent (Evaluator)
Validates claims against policy terms, calculates coverage, and determines payout.
Runs as a low-code agent in UiPath Agent Builder.
"""

from __future__ import annotations
import os, sys, time
from datetime import datetime
from typing import Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))
from src.utils.models import *
from src.utils.logger import setup_logger, log_agent_action

logger = setup_logger("assessment_agent")


class ClaimEvaluator:
    """Evaluates claims against policy terms and calculates coverage."""

    def lookup_policy(self, policy_number: str) -> Optional[PolicyInfo]:
        """
        Look up policy details from the external policy database.
        In production, this calls the UiPath API Workflow connected to the policy DB.
        Here we simulate with sample data.
        """
        # Simulated policy database
        policies = {
            "POL-2024-78901": PolicyInfo(
                policy_number="POL-2024-78901",
                holder_name="John Doe",
                policy_type="auto_comprehensive",
                coverage_limit=50000.0,
                deductible=1000.0,
                effective_date=datetime(2024, 1, 1),
                expiry_date=datetime(2027, 1, 1),
                is_active=True,
                exclusions=["racing", "intentional_damage"],
            ),
            "POL-2024-45678": PolicyInfo(
                policy_number="POL-2024-45678",
                holder_name="Jane Smith",
                policy_type="property_standard",
                coverage_limit=200000.0,
                deductible=2500.0,
                effective_date=datetime(2024, 6, 1),
                expiry_date=datetime(2026, 6, 1),
                is_active=True,
                exclusions=["flood", "earthquake"],
            ),
        }
        policy = policies.get(policy_number)
        if policy:
            logger.info("policy_found", policy_number=policy_number, policy_type=policy.policy_type)
        else:
            logger.warning("policy_not_found", policy_number=policy_number)
        return policy

    def evaluate_claim(self, case: CaseRecord) -> AssessmentResult:
        """
        Main assessment logic:
        1. Look up the policy
        2. Check if claim is covered
        3. Calculate net payout (claimed amount - deductible, capped at coverage limit)
        4. Flag for human review if needed
        """
        start = time.time()
        claim = case.claim
        logger.info("assessment_started", claim_id=claim.claim_id, amount=claim.claimed_amount)

        # Look up policy
        policy = self.lookup_policy(claim.claimant.policy_number)
        if not policy:
            return AssessmentResult(
                claim_id=claim.claim_id,
                policy=PolicyInfo(
                    policy_number=claim.claimant.policy_number,
                    holder_name=claim.claimant.full_name,
                    policy_type="unknown", coverage_limit=0, deductible=0,
                    effective_date=datetime.utcnow(), expiry_date=datetime.utcnow(),
                    is_active=False,
                ),
                is_covered=False, coverage_amount=0, deductible_applied=0, net_payout=0,
                assessment_notes="Policy not found in database. Manual verification required.",
                requires_human_review=True,
            )

        # Check coverage
        is_covered = policy.is_active and claim.incident_date >= policy.effective_date and claim.incident_date <= policy.expiry_date

        if not is_covered:
            return AssessmentResult(
                claim_id=claim.claim_id, policy=policy,
                is_covered=False, coverage_amount=0, deductible_applied=0, net_payout=0,
                assessment_notes="Claim is outside policy coverage period.",
                requires_human_review=True,
            )

        # Calculate payout
        coverage_amount = min(claim.claimed_amount, policy.coverage_limit)
        deductible = policy.deductible
        net_payout = max(0, coverage_amount - deductible)

        # Determine if human review needed
        needs_review = (
            claim.claimed_amount > policy.coverage_limit * 0.8  # >80% of limit
            or net_payout > 20000  # High-value payout
            or (case.fraud_analysis and case.fraud_analysis.risk_level in (RiskLevel.MEDIUM, RiskLevel.HIGH))
        )

        notes = (
            f"Claim covered under {policy.policy_type}. "
            f"Coverage: ${coverage_amount:,.2f}, Deductible: ${deductible:,.2f}, "
            f"Net payout: ${net_payout:,.2f}."
        )
        if needs_review:
            notes += " Flagged for human adjuster review due to high value or risk."

        result = AssessmentResult(
            claim_id=claim.claim_id, policy=policy,
            is_covered=True, coverage_amount=coverage_amount,
            deductible_applied=deductible, net_payout=net_payout,
            assessment_notes=notes, requires_human_review=needs_review,
        )

        duration_ms = (time.time() - start) * 1000
        log_agent_action(logger, case.case_id, "assessment_complete", "evaluated", duration_ms,
                         net_payout=net_payout, needs_review=needs_review)
        return result
