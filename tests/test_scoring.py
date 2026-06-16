"""Tests for risk scoring engine."""
import pytest
from src.agents.fraud_detection.scoring import FraudScorer
from src.utils.models import FraudSignal, RiskLevel


class TestScoring:
    def test_empty_signals(self):
        assert FraudScorer().calculate_risk_score([]) == 0.0

    def test_score_bounded(self):
        scorer = FraudScorer()
        signals = [FraudSignal(signal_type=t, description="test", severity=1.0)
                   for t in ["duplicate_claim", "velocity_check", "amount_outlier",
                            "document_anomaly", "timing_anomaly"]]
        score = scorer.calculate_risk_score(signals)
        assert 0.0 <= score <= 1.0

    def test_recommendation_contains_amount(self):
        scorer = FraudScorer()
        rec = scorer.generate_recommendation(0.8, RiskLevel.HIGH, 25000)
        assert "$25,000" in rec
