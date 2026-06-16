"""
ClaimPilot — Fraud Pattern Definitions
Defines the fraud detection patterns and their analysis logic.
Each pattern analyzer returns a FraudSignal if the pattern is detected.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from ...utils.models import Claim, ClaimDocument, FraudSignal
from . import config


class PatternAnalyzer:
    """
    Analyzes insurance claims for fraud patterns.
    Each method checks for a specific fraud indicator and returns
    a FraudSignal if detected, or None if clean.
    """

    def __init__(self, claim_history: list[dict] | None = None):
        """
        Args:
            claim_history: Historical claims for the same claimant.
                           Each dict has: claim_id, claimed_amount, incident_date,
                           claim_type, submitted_at
        """
        self.claim_history = claim_history or []

    def check_duplicate_claim(self, claim: Claim) -> Optional[FraudSignal]:
        """
        Check if the claimant has filed a similar claim recently.
        Looks for claims with same type within 90 days of each other.
        """
        cutoff = claim.incident_date - timedelta(days=90)

        duplicates = [
            h for h in self.claim_history
            if (
                h.get("claim_type") == claim.claim_type.value
                and datetime.fromisoformat(h["incident_date"]) >= cutoff
                and h.get("claim_id") != claim.claim_id
            )
        ]

        if duplicates:
            return FraudSignal(
                signal_type="duplicate_claim",
                description=(
                    f"Claimant has {len(duplicates)} similar "
                    f"{claim.claim_type.value} claim(s) within the last 90 days"
                ),
                severity=min(1.0, 0.5 + (len(duplicates) * 0.25)),
                evidence={
                    "duplicate_count": len(duplicates),
                    "duplicate_claim_ids": [d["claim_id"] for d in duplicates],
                },
            )
        return None

    def check_velocity(self, claim: Claim) -> Optional[FraudSignal]:
        """
        Check if the claimant is filing claims at an unusually high rate.
        """
        now = claim.submitted_at
        claims_90d = [
            h for h in self.claim_history
            if datetime.fromisoformat(h["submitted_at"]) >= (now - timedelta(days=90))
        ]
        claims_365d = [
            h for h in self.claim_history
            if datetime.fromisoformat(h["submitted_at"]) >= (now - timedelta(days=365))
        ]

        if len(claims_90d) >= config.MAX_CLAIMS_PER_90_DAYS:
            return FraudSignal(
                signal_type="velocity_check",
                description=(
                    f"Claimant has filed {len(claims_90d)} claims in the last 90 days "
                    f"(threshold: {config.MAX_CLAIMS_PER_90_DAYS})"
                ),
                severity=min(1.0, len(claims_90d) / config.MAX_CLAIMS_PER_90_DAYS * 0.6),
                evidence={
                    "claims_90d": len(claims_90d),
                    "claims_365d": len(claims_365d),
                    "threshold_90d": config.MAX_CLAIMS_PER_90_DAYS,
                },
            )

        if len(claims_365d) >= config.MAX_CLAIMS_PER_365_DAYS:
            return FraudSignal(
                signal_type="velocity_check",
                description=(
                    f"Claimant has filed {len(claims_365d)} claims in the last year "
                    f"(threshold: {config.MAX_CLAIMS_PER_365_DAYS})"
                ),
                severity=min(1.0, len(claims_365d) / config.MAX_CLAIMS_PER_365_DAYS * 0.5),
                evidence={
                    "claims_365d": len(claims_365d),
                    "threshold_365d": config.MAX_CLAIMS_PER_365_DAYS,
                },
            )
        return None

    def check_amount_outlier(self, claim: Claim) -> Optional[FraudSignal]:
        """
        Check if the claimed amount is an outlier for the claim type.
        """
        threshold = config.AMOUNT_THRESHOLDS.get(
            claim.claim_type.value,
            50000,  # default threshold
        )

        if claim.claimed_amount > threshold:
            ratio = claim.claimed_amount / threshold
            return FraudSignal(
                signal_type="amount_outlier",
                description=(
                    f"Claimed amount ${claim.claimed_amount:,.2f} exceeds the "
                    f"95th percentile (${threshold:,.2f}) for {claim.claim_type.value} "
                    f"claims by {ratio:.1f}x"
                ),
                severity=min(1.0, (ratio - 1.0) * 0.4),
                evidence={
                    "claimed_amount": claim.claimed_amount,
                    "threshold": threshold,
                    "ratio": round(ratio, 2),
                },
            )
        return None

    def check_document_anomaly(self, claim: Claim) -> Optional[FraudSignal]:
        """
        Check for suspicious or low-confidence document extractions.
        """
        suspicious_docs = [
            doc for doc in claim.documents
            if (
                doc.confidence_score is not None
                and doc.confidence_score < config.MIN_DOCUMENT_CONFIDENCE
            )
        ]

        if suspicious_docs:
            avg_confidence = sum(d.confidence_score for d in suspicious_docs) / len(suspicious_docs)
            return FraudSignal(
                signal_type="document_anomaly",
                description=(
                    f"{len(suspicious_docs)} document(s) have low extraction confidence "
                    f"(avg: {avg_confidence:.0%}, threshold: {config.MIN_DOCUMENT_CONFIDENCE:.0%})"
                ),
                severity=min(1.0, (config.MIN_DOCUMENT_CONFIDENCE - avg_confidence) * 2),
                evidence={
                    "suspicious_doc_count": len(suspicious_docs),
                    "avg_confidence": round(avg_confidence, 3),
                    "documents": [
                        {"filename": d.filename, "confidence": d.confidence_score}
                        for d in suspicious_docs
                    ],
                },
            )
        return None

    def check_timing_anomaly(self, claim: Claim) -> Optional[FraudSignal]:
        """
        Check if the claim was filed suspiciously fast or slow
        relative to the incident date.
        """
        time_diff = claim.submitted_at - claim.incident_date
        hours_since = time_diff.total_seconds() / 3600
        days_since = time_diff.days

        if hours_since < config.MIN_HOURS_SINCE_INCIDENT and hours_since >= 0:
            return FraudSignal(
                signal_type="timing_anomaly",
                description=(
                    f"Claim filed only {hours_since:.1f} hours after incident "
                    f"(minimum expected: {config.MIN_HOURS_SINCE_INCIDENT}h)"
                ),
                severity=0.6,
                evidence={
                    "hours_since_incident": round(hours_since, 1),
                    "min_expected_hours": config.MIN_HOURS_SINCE_INCIDENT,
                },
            )

        if days_since > config.MAX_DAYS_SINCE_INCIDENT:
            return FraudSignal(
                signal_type="timing_anomaly",
                description=(
                    f"Claim filed {days_since} days after incident "
                    f"(maximum expected: {config.MAX_DAYS_SINCE_INCIDENT} days)"
                ),
                severity=min(1.0, (days_since - config.MAX_DAYS_SINCE_INCIDENT) / 60 * 0.5),
                evidence={
                    "days_since_incident": days_since,
                    "max_expected_days": config.MAX_DAYS_SINCE_INCIDENT,
                },
            )
        return None

    def run_all_checks(self, claim: Claim) -> list[FraudSignal]:
        """
        Run all fraud pattern checks on a claim.

        Returns:
            List of detected FraudSignals (empty if claim is clean).
        """
        checks = [
            self.check_duplicate_claim,
            self.check_velocity,
            self.check_amount_outlier,
            self.check_document_anomaly,
            self.check_timing_anomaly,
        ]

        signals = []
        for check in checks:
            signal = check(claim)
            if signal is not None:
                signals.append(signal)

        return signals
