"""
ClaimPilot — Fraud Risk Scoring Engine
Combines individual fraud signals into a weighted composite risk score.
"""

from __future__ import annotations

from ..fraud_detection import config
from ...utils.models import Claim, FraudSignal, RiskLevel


class FraudScorer:
    """
    Calculates a composite fraud risk score from individual fraud signals.
    Uses configurable pattern weights to produce a 0.0–1.0 score.
    """

    def __init__(self, weights: dict[str, float] | None = None):
        """
        Args:
            weights: Override pattern weights. Defaults to config.PATTERN_WEIGHTS.
        """
        self.weights = weights or config.PATTERN_WEIGHTS

    def calculate_risk_score(self, signals: list[FraudSignal]) -> float:
        """
        Calculate a weighted composite risk score from detected signals.

        The score is computed as:
            score = Σ (signal_severity × pattern_weight) / Σ (all pattern_weights)

        Then normalized to account for the fact that not all patterns may fire.
        A bonus multiplier is applied when multiple signals co-occur (compounding risk).

        Args:
            signals: List of detected fraud signals.

        Returns:
            Risk score between 0.0 and 1.0.
        """
        if not signals:
            return 0.0

        # Calculate weighted sum of detected signal severities
        weighted_sum = 0.0
        total_possible_weight = sum(self.weights.values())

        for signal in signals:
            weight = self.weights.get(signal.signal_type, 0.05)
            weighted_sum += signal.severity * weight

        # Base score: weighted sum normalized by total possible weight
        base_score = weighted_sum / total_possible_weight if total_possible_weight > 0 else 0.0

        # Compounding risk: multiple signals co-occurring increases risk
        # Each additional signal beyond the first adds a 10% multiplier
        signal_count_multiplier = 1.0 + (max(0, len(signals) - 1) * 0.10)
        compounded_score = base_score * signal_count_multiplier

        # Clamp to [0.0, 1.0]
        return min(1.0, max(0.0, compounded_score))

    def classify_risk_level(self, risk_score: float) -> RiskLevel:
        """
        Classify a numeric risk score into a risk level.

        Args:
            risk_score: Score between 0.0 and 1.0.

        Returns:
            RiskLevel enum value.
        """
        if risk_score >= 0.90:
            return RiskLevel.CRITICAL
        elif risk_score >= config.HIGH_RISK_THRESHOLD:
            return RiskLevel.HIGH
        elif risk_score >= config.MEDIUM_RISK_THRESHOLD:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW

    def generate_recommendation(
        self,
        risk_score: float,
        risk_level: RiskLevel,
        claimed_amount: float,
    ) -> str:
        """
        Generate a human-readable recommendation based on risk analysis.

        Args:
            risk_score: The computed risk score.
            risk_level: The classified risk level.
            claimed_amount: The amount being claimed.

        Returns:
            Recommendation string for the case routing decision.
        """
        if risk_level == RiskLevel.CRITICAL:
            return (
                f"CRITICAL RISK ({risk_score:.0%}): Immediately escalate to senior "
                f"fraud investigator. Multiple high-severity fraud indicators detected. "
                f"Do NOT auto-process this ${claimed_amount:,.2f} claim."
            )
        elif risk_level == RiskLevel.HIGH:
            return (
                f"HIGH RISK ({risk_score:.0%}): Route to human adjuster for manual "
                f"review via Action Center. Fraud indicators require human judgment "
                f"before proceeding with this ${claimed_amount:,.2f} claim."
            )
        elif risk_level == RiskLevel.MEDIUM:
            if claimed_amount > config.AUTO_APPROVE_MAX_AMOUNT:
                return (
                    f"MEDIUM RISK ({risk_score:.0%}): Some fraud indicators present. "
                    f"Given the claim amount of ${claimed_amount:,.2f} exceeds the "
                    f"auto-approve threshold, route to human adjuster for review."
                )
            return (
                f"MEDIUM RISK ({risk_score:.0%}): Minor fraud indicators detected. "
                f"Claim amount of ${claimed_amount:,.2f} is within auto-approve range. "
                f"Proceed with automated assessment but flag for periodic audit."
            )
        else:
            if claimed_amount <= config.AUTO_APPROVE_MAX_AMOUNT:
                return (
                    f"LOW RISK ({risk_score:.0%}): No significant fraud indicators. "
                    f"Claim amount of ${claimed_amount:,.2f} is within auto-approve "
                    f"range. Proceed with automated assessment and settlement."
                )
            return (
                f"LOW RISK ({risk_score:.0%}): No fraud indicators detected. "
                f"Claim amount of ${claimed_amount:,.2f} exceeds auto-approve threshold. "
                f"Route to human adjuster for standard high-value review."
            )
