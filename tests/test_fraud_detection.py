"""
ClaimPilot — Tests for Fraud Detection Agent
"""

import pytest
from datetime import datetime, timedelta
from src.utils.models import *
from src.agents.fraud_detection.agent import FraudDetectionAgent
from src.agents.fraud_detection.scoring import FraudScorer
from src.agents.fraud_detection.patterns import PatternAnalyzer


def make_claim(**kwargs) -> Claim:
    """Helper to create test claims."""
    defaults = {
        "claim_type": ClaimType.AUTO,
        "claimant": ClaimantInfo(
            full_name="Test User", email="test@test.com",
            phone="555-0000", policy_number="POL-TEST-001",
        ),
        "description": "Test claim",
        "incident_date": datetime.utcnow() - timedelta(days=5),
        "claimed_amount": 5000.0,
    }
    defaults.update(kwargs)
    return Claim(**defaults)


class TestFraudScorer:
    def test_no_signals_returns_zero(self):
        scorer = FraudScorer()
        assert scorer.calculate_risk_score([]) == 0.0

    def test_single_low_signal(self):
        scorer = FraudScorer()
        signals = [FraudSignal(signal_type="timing_anomaly", description="Late filing", severity=0.3)]
        score = scorer.calculate_risk_score(signals)
        assert 0.0 < score < 0.5

    def test_multiple_signals_compound(self):
        scorer = FraudScorer()
        signals = [
            FraudSignal(signal_type="duplicate_claim", description="Duplicate", severity=0.8),
            FraudSignal(signal_type="velocity_check", description="High velocity", severity=0.7),
            FraudSignal(signal_type="amount_outlier", description="High amount", severity=0.9),
        ]
        score = scorer.calculate_risk_score(signals)
        assert score > 0.3  # Multiple signals should produce meaningful score

    def test_risk_level_classification(self):
        scorer = FraudScorer()
        assert scorer.classify_risk_level(0.1) == RiskLevel.LOW
        assert scorer.classify_risk_level(0.5) == RiskLevel.MEDIUM
        assert scorer.classify_risk_level(0.8) == RiskLevel.HIGH
        assert scorer.classify_risk_level(0.95) == RiskLevel.CRITICAL


class TestPatternAnalyzer:
    def test_no_history_no_duplicates(self):
        analyzer = PatternAnalyzer(claim_history=[])
        claim = make_claim()
        assert analyzer.check_duplicate_claim(claim) is None

    def test_duplicate_claim_detected(self):
        history = [{
            "claim_id": "OLD-001", "claim_type": "auto",
            "incident_date": (datetime.utcnow() - timedelta(days=30)).isoformat(),
            "submitted_at": (datetime.utcnow() - timedelta(days=29)).isoformat(),
            "claimed_amount": 3000,
        }]
        analyzer = PatternAnalyzer(claim_history=history)
        claim = make_claim()
        signal = analyzer.check_duplicate_claim(claim)
        assert signal is not None
        assert signal.signal_type == "duplicate_claim"

    def test_amount_outlier_detected(self):
        analyzer = PatternAnalyzer()
        claim = make_claim(claimed_amount=100000)  # Way above auto threshold
        signal = analyzer.check_amount_outlier(claim)
        assert signal is not None
        assert signal.signal_type == "amount_outlier"

    def test_normal_amount_not_flagged(self):
        analyzer = PatternAnalyzer()
        claim = make_claim(claimed_amount=5000)
        signal = analyzer.check_amount_outlier(claim)
        assert signal is None

    def test_low_confidence_doc_flagged(self):
        analyzer = PatternAnalyzer()
        claim = make_claim(documents=[
            ClaimDocument(filename="bad_scan.pdf", document_type="form", confidence_score=0.30),
        ])
        signal = analyzer.check_document_anomaly(claim)
        assert signal is not None
        assert signal.signal_type == "document_anomaly"


class TestFraudDetectionAgent:
    def test_clean_claim_low_risk(self):
        agent = FraudDetectionAgent()
        claim = make_claim(claimed_amount=2000)
        result = agent.analyze_claim(claim)
        assert result.risk_level == RiskLevel.LOW
        assert result.risk_score < 0.45

    def test_suspicious_claim_flagged(self):
        agent = FraudDetectionAgent()
        claim = make_claim(
            claimed_amount=100000,
            documents=[
                ClaimDocument(filename="fake.pdf", document_type="form", confidence_score=0.2),
            ],
        )
        history = [
            {"claim_id": f"OLD-{i}", "claim_type": "auto",
             "incident_date": (datetime.utcnow() - timedelta(days=10*i)).isoformat(),
             "submitted_at": (datetime.utcnow() - timedelta(days=10*i-1)).isoformat(),
             "claimed_amount": 5000}
            for i in range(1, 5)
        ]
        result = agent.analyze_claim(claim, history)
        assert result.risk_level in (RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL)
        assert len(result.signals) >= 2

    def test_maestro_format_output(self):
        agent = FraudDetectionAgent()
        claim = make_claim()
        result = agent.analyze_claim(claim)
        formatted = agent.format_for_maestro(result)
        assert "FraudRiskScore" in formatted
        assert "FraudRiskLevel" in formatted
        assert "RequiresHumanReview" in formatted
        assert isinstance(formatted["FraudSignals"], list)
