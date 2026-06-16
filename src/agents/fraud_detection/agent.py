"""
ClaimPilot — Fraud Detection Agent (Coded Agent)
=================================================
This is the primary CODED AGENT built with the UiPath Python SDK.
It analyzes insurance claims for fraud patterns and returns a risk assessment
that determines how the claim is routed through Maestro Case Management.

Architecture:
    - Receives claim data from UiPath Maestro (via case trigger)
    - Runs 5 fraud pattern checks in parallel
    - Produces a weighted composite risk score (0.0–1.0)
    - Returns routing recommendation (auto-process / human review / escalate)
    - Logs all decisions for full auditability

UiPath Integration:
    - Registered as a Coded Agent in UiPath Automation Cloud
    - Triggered by Maestro during the INVESTIGATION case stage
    - Results stored back into the Maestro case custom fields
"""

from __future__ import annotations

import os
import sys
import time
from datetime import datetime
from typing import Any

from dotenv import load_dotenv

# Add project root to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from src.utils.models import (
    Claim,
    ClaimantInfo,
    ClaimDocument,
    ClaimType,
    FraudAnalysisResult,
    FraudSignal,
    RiskLevel,
)
from src.utils.logger import setup_logger, log_agent_action
from .patterns import PatternAnalyzer
from .scoring import FraudScorer

load_dotenv()

# Initialize logger
logger = setup_logger("fraud_detection_agent")


class FraudDetectionAgent:
    """
    AI-powered fraud detection agent for insurance claims.

    This coded agent analyzes incoming claims against multiple fraud patterns,
    produces a composite risk score, and recommends case routing decisions.
    Designed to run as a UiPath Coded Agent within the Maestro Case pipeline.
    """

    def __init__(self):
        self.scorer = FraudScorer()
        self.model_version = "1.0.0"
        logger.info(
            "agent_initialized",
            model_version=self.model_version,
            patterns_loaded=len(self.scorer.weights),
        )

    def analyze_claim(
        self,
        claim: Claim,
        claim_history: list[dict] | None = None,
    ) -> FraudAnalysisResult:
        """
        Perform comprehensive fraud analysis on an insurance claim.

        This is the main entry point called by UiPath Maestro during
        the INVESTIGATION stage of a case.

        Args:
            claim: The claim to analyze.
            claim_history: Historical claims from the same claimant
                           for velocity and duplicate checks.

        Returns:
            FraudAnalysisResult with risk score, signals, and recommendation.
        """
        start_time = time.time()
        logger.info(
            "analysis_started",
            claim_id=claim.claim_id,
            claim_type=claim.claim_type.value,
            claimed_amount=claim.claimed_amount,
        )

        # Step 1: Run all pattern checks
        analyzer = PatternAnalyzer(claim_history=claim_history)
        signals = analyzer.run_all_checks(claim)

        # Step 2: Calculate composite risk score
        risk_score = self.scorer.calculate_risk_score(signals)
        risk_level = self.scorer.classify_risk_level(risk_score)

        # Step 3: Generate routing recommendation
        recommendation = self.scorer.generate_recommendation(
            risk_score=risk_score,
            risk_level=risk_level,
            claimed_amount=claim.claimed_amount,
        )

        # Step 4: Build result
        result = FraudAnalysisResult(
            claim_id=claim.claim_id,
            risk_score=round(risk_score, 4),
            risk_level=risk_level,
            signals=signals,
            recommendation=recommendation,
            model_version=self.model_version,
        )

        # Step 5: Log the analysis
        duration_ms = (time.time() - start_time) * 1000
        log_agent_action(
            logger=logger,
            case_id=claim.claim_id,
            action="fraud_analysis_complete",
            result=risk_level.value,
            duration_ms=duration_ms,
            risk_score=risk_score,
            signals_detected=len(signals),
            recommendation=recommendation[:100],
        )

        return result

    def should_escalate_to_human(self, result: FraudAnalysisResult) -> bool:
        """
        Determine if this claim should be routed to a human adjuster.

        Args:
            result: The fraud analysis result.

        Returns:
            True if human review is required.
        """
        return result.risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL)

    def should_auto_process(self, result: FraudAnalysisResult, claimed_amount: float) -> bool:
        """
        Determine if this claim can be auto-processed without human review.

        Args:
            result: The fraud analysis result.
            claimed_amount: The amount being claimed.

        Returns:
            True if the claim can proceed to automated assessment.
        """
        auto_approve_max = float(os.getenv("AUTO_APPROVE_MAX_AMOUNT", "5000"))
        return (
            result.risk_level == RiskLevel.LOW
            and claimed_amount <= auto_approve_max
        )

    def format_for_maestro(self, result: FraudAnalysisResult) -> dict[str, Any]:
        """
        Format the analysis result for storage in Maestro case custom fields.

        Args:
            result: The fraud analysis result.

        Returns:
            Dictionary ready to be sent to UiPath Maestro API.
        """
        return {
            "FraudRiskScore": result.risk_score,
            "FraudRiskLevel": result.risk_level.value,
            "FraudSignalCount": len(result.signals),
            "FraudRecommendation": result.recommendation,
            "FraudModelVersion": result.model_version,
            "FraudAnalyzedAt": result.analyzed_at.isoformat(),
            "FraudSignals": [
                {
                    "type": s.signal_type,
                    "description": s.description,
                    "severity": s.severity,
                }
                for s in result.signals
            ],
            "RequiresHumanReview": self.should_escalate_to_human(result),
        }


# ──────────────────────────────────────────────
# Entry Point — UiPath Coded Agent Execution
# ──────────────────────────────────────────────

def run_agent(claim_data: dict, claim_history: list[dict] | None = None) -> dict:
    """
    Main entry point for UiPath Coded Agent execution.

    This function is called by the UiPath runtime when the agent is triggered
    during the INVESTIGATION stage of a Maestro Case.

    Args:
        claim_data: Raw claim data from Maestro case custom fields.
        claim_history: Historical claims for the claimant.

    Returns:
        Dictionary with fraud analysis results for Maestro.
    """
    # Parse claim data into Claim model
    claim = Claim(
        claim_id=claim_data.get("ClaimId", "UNKNOWN"),
        claim_type=ClaimType(claim_data.get("ClaimType", "auto")),
        claimant=ClaimantInfo(
            full_name=claim_data.get("ClaimantName", ""),
            email=claim_data.get("ClaimantEmail", ""),
            phone=claim_data.get("ClaimantPhone", ""),
            policy_number=claim_data.get("PolicyNumber", ""),
        ),
        description=claim_data.get("Description", ""),
        incident_date=datetime.fromisoformat(
            claim_data.get("IncidentDate", datetime.utcnow().isoformat())
        ),
        claimed_amount=float(claim_data.get("ClaimedAmount", 0)),
        documents=[
            ClaimDocument(
                filename=doc.get("filename", "unknown"),
                document_type=doc.get("type", "unknown"),
                confidence_score=doc.get("confidence"),
            )
            for doc in claim_data.get("Documents", [])
        ],
    )

    # Run analysis
    agent = FraudDetectionAgent()
    result = agent.analyze_claim(claim, claim_history)

    # Return formatted result for Maestro
    return agent.format_for_maestro(result)


# ──────────────────────────────────────────────
# Standalone execution for testing
# ──────────────────────────────────────────────

if __name__ == "__main__":
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel

    console = Console()

    # Create a sample claim for testing
    sample_claim_data = {
        "ClaimId": "CLM-TEST-001",
        "ClaimType": "auto",
        "ClaimantName": "John Doe",
        "ClaimantEmail": "john.doe@example.com",
        "ClaimantPhone": "+1-555-0123",
        "PolicyNumber": "POL-2024-78901",
        "Description": "Rear-end collision on Highway 101. Other driver ran red light.",
        "IncidentDate": "2026-06-10T14:30:00",
        "ClaimedAmount": 15000.00,
        "Documents": [
            {"filename": "claim_form.pdf", "type": "claim_form", "confidence": 0.92},
            {"filename": "accident_photo_1.jpg", "type": "photo", "confidence": 0.88},
            {"filename": "police_report.pdf", "type": "police_report", "confidence": 0.95},
        ],
    }

    # Simulate some claim history (claimant filed 2 claims before)
    sample_history = [
        {
            "claim_id": "CLM-PREV-001",
            "claim_type": "auto",
            "incident_date": "2026-03-15T10:00:00",
            "submitted_at": "2026-03-16T09:00:00",
            "claimed_amount": 8000,
        },
        {
            "claim_id": "CLM-PREV-002",
            "claim_type": "property",
            "incident_date": "2026-01-20T16:00:00",
            "submitted_at": "2026-01-22T11:00:00",
            "claimed_amount": 12000,
        },
    ]

    console.print(Panel("🛡️ ClaimPilot — Fraud Detection Agent", style="bold cyan"))
    console.print(f"\n[bold]Analyzing claim:[/bold] {sample_claim_data['ClaimId']}")
    console.print(f"[bold]Claim type:[/bold] {sample_claim_data['ClaimType']}")
    console.print(f"[bold]Amount:[/bold] ${sample_claim_data['ClaimedAmount']:,.2f}")
    console.print(f"[bold]Claimant:[/bold] {sample_claim_data['ClaimantName']}")
    console.print(f"[bold]History:[/bold] {len(sample_history)} previous claims\n")

    # Run the agent
    result = run_agent(sample_claim_data, sample_history)

    # Display results
    risk_color = {
        "low": "green",
        "medium": "yellow",
        "high": "red",
        "critical": "bold red",
    }.get(result["FraudRiskLevel"], "white")

    console.print(f"\n[bold]═══ FRAUD ANALYSIS RESULTS ═══[/bold]\n")
    console.print(f"Risk Score: [{risk_color}]{result['FraudRiskScore']:.1%}[/{risk_color}]")
    console.print(f"Risk Level: [{risk_color}]{result['FraudRiskLevel'].upper()}[/{risk_color}]")
    console.print(f"Signals Detected: {result['FraudSignalCount']}")
    console.print(f"Human Review Required: {'✅ YES' if result['RequiresHumanReview'] else '❌ No'}")

    if result["FraudSignals"]:
        table = Table(title="Detected Fraud Signals")
        table.add_column("Type", style="bold")
        table.add_column("Description")
        table.add_column("Severity", justify="right")

        for signal in result["FraudSignals"]:
            sev = signal["severity"]
            sev_color = "green" if sev < 0.4 else "yellow" if sev < 0.7 else "red"
            table.add_row(
                signal["type"],
                signal["description"],
                f"[{sev_color}]{sev:.0%}[/{sev_color}]",
            )
        console.print(table)

    console.print(f"\n[bold]Recommendation:[/bold] {result['FraudRecommendation']}")
