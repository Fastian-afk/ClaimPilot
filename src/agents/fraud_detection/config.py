"""
ClaimPilot — Fraud Detection Agent Configuration
Thresholds, patterns, and rules for fraud analysis.
"""

import os
from dotenv import load_dotenv

load_dotenv()


# ──────────────────────────────────────────────
# Risk Scoring Thresholds
# ──────────────────────────────────────────────

HIGH_RISK_THRESHOLD = float(os.getenv("FRAUD_HIGH_RISK_THRESHOLD", "0.75"))
MEDIUM_RISK_THRESHOLD = float(os.getenv("FRAUD_MEDIUM_RISK_THRESHOLD", "0.45"))
AUTO_APPROVE_MAX_AMOUNT = float(os.getenv("AUTO_APPROVE_MAX_AMOUNT", "5000"))


# ──────────────────────────────────────────────
# Fraud Pattern Weights
# Weight assigned to each fraud signal type.
# Higher weight = stronger influence on final score.
# ──────────────────────────────────────────────

PATTERN_WEIGHTS = {
    "duplicate_claim": 0.30,         # Same claimant, similar incident within 90 days
    "velocity_check": 0.20,          # Too many claims in a short period
    "amount_outlier": 0.15,          # Claimed amount is an outlier for claim type
    "document_anomaly": 0.15,        # Suspicious or low-confidence document extraction
    "timing_anomaly": 0.10,          # Claim filed at unusual time relative to incident
    "address_mismatch": 0.05,        # Address inconsistencies across documents
    "known_fraud_ring": 0.05,        # Claimant matches known fraud ring patterns
}


# ──────────────────────────────────────────────
# Velocity Check Parameters
# ──────────────────────────────────────────────

# Max claims a claimant can file before flagging
MAX_CLAIMS_PER_90_DAYS = 3
MAX_CLAIMS_PER_365_DAYS = 5

# ──────────────────────────────────────────────
# Amount Outlier Parameters (by claim type)
# Values represent the 95th percentile of normal claims
# ──────────────────────────────────────────────

AMOUNT_THRESHOLDS = {
    "auto": 25000,
    "property": 75000,
    "health": 50000,
    "liability": 100000,
    "life": 500000,
}

# ──────────────────────────────────────────────
# Timing Anomaly Parameters
# ──────────────────────────────────────────────

# Claims filed more than this many days after incident are suspicious
MAX_DAYS_SINCE_INCIDENT = 30

# Claims filed within this many hours of incident are suspicious (too fast)
MIN_HOURS_SINCE_INCIDENT = 1

# ──────────────────────────────────────────────
# Document Confidence Threshold
# ──────────────────────────────────────────────

# Below this confidence, document extraction is flagged as suspicious
MIN_DOCUMENT_CONFIDENCE = 0.70
