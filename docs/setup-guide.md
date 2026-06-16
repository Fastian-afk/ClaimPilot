# ClaimPilot — Setup Guide

## Prerequisites

- Python 3.10+
- Git
- UiPath Automation Cloud account with Maestro enabled
- UiPath Studio Web access (provided via Labs)

## Step 1: Clone & Setup Python

```bash
git clone https://github.com/YOUR_USERNAME/claimpilot.git
cd claimpilot/src
python -m venv venv
venv\Scripts\activate   # Windows
pip install -r requirements.txt
```

## Step 2: Environment Configuration

```bash
cp ../.env.example ../.env
# Edit .env with your UiPath credentials
```

## Step 3: UiPath Automation Cloud Setup

1. **Log in** to your UiPath Automation Cloud instance
2. **Import Case Definition**: Go to Maestro → Case Definitions → Import `uipath/case-definition.json`
3. **Create Agents in Agent Builder**:
   - Intake Agent (from `src/agents/intake/`)
   - Assessment Agent (from `src/agents/assessment/`)
   - Settlement Agent (from `src/agents/settlement/`)
4. **Deploy Coded Agent**: Upload fraud detection agent as Coded Agent
5. **Configure Document Understanding**: Set up extraction models in AI Center
6. **Set up API Workflows**: Connect policy DB and payment gateway endpoints
7. **Configure Action Center**: Create task forms for adjuster review

## Step 4: Run Tests

```bash
cd ..
python -m pytest tests/ -v
```

## Step 5: Test End-to-End

1. Submit a test claim through the Maestro portal
2. Watch it flow through: Intake → Triage → Investigation → Assessment → Settlement → Closed
3. Verify fraud detection triggers human review for high-risk claims
4. Confirm audit trail is complete in Maestro
