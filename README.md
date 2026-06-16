<div align="center">

# 🛡️ ClaimPilot

### AI-Powered Insurance Claims Orchestration

*Multi-agent system that orchestrates insurance claims from intake to settlement — coordinating fraud detection, document extraction, and human adjusters through UiPath Maestro Case Management.*

[![UiPath AgentHack 2026](https://img.shields.io/badge/UiPath-AgentHack%202026-FF6A00?style=for-the-badge&logo=uipath&logoColor=white)](https://uipath-agenthack.devpost.com/)
[![Track](https://img.shields.io/badge/Track%201-Maestro%20Case-0078D4?style=for-the-badge)](https://uipath-agenthack.devpost.com/details/tracks)
[![License: MIT](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](./LICENSE)
[![Coding Agent](https://img.shields.io/badge/Coding%20Agent-Gemini%20CLI-4285F4?style=for-the-badge&logo=google&logoColor=white)]()

</div>

---

## 📋 Table of Contents

- [Problem Statement](#-problem-statement)
- [Solution Overview](#-solution-overview)
- [Architecture](#-architecture)
- [UiPath Components Used](#-uipath-components-used)
- [Agent Types](#-agent-types)
- [Case Lifecycle](#-case-lifecycle)
- [Setup Instructions](#-setup-instructions)
- [Demo Video](#-demo-video)
- [Coding Agent Usage](#-coding-agent-usage)
- [Project Structure](#-project-structure)
- [License](#-license)

---

## 🔍 Problem Statement

Insurance claims processing is one of the most complex, exception-heavy workflows in enterprise operations:

- **$308 billion** lost annually to insurance fraud globally
- **Average claim** takes **30+ days** to resolve through manual processes
- **60% of adjuster time** is spent on routine claims that could be automated
- Claims get **stuck between departments**, exceptions pile up, and there's **no single source of truth** for case status
- **Audit trails are fragmented** across email, spreadsheets, and legacy systems

The result: slow resolutions, frustrated policyholders, missed fraud, and compliance risk.

---

## 💡 Solution Overview

**ClaimPilot** is a multi-agent orchestration system built on **UiPath Maestro Case Management** that transforms insurance claims processing from a fragmented, manual workflow into a coordinated, intelligent pipeline.

### Key Capabilities

| Capability | Description |
|---|---|
| **🤖 Multi-Agent Coordination** | 4 specialized AI agents handle intake, fraud detection, assessment, and settlement |
| **👤 Human-in-the-Loop** | Adjusters review high-risk claims via UiPath Action Center at critical decision points |
| **📄 Document Intelligence** | Automatic extraction of claim data from PDFs, photos, and forms using Document Understanding |
| **🔍 Fraud Detection** | Real-time pattern analysis using a coded Python agent with anomaly detection |
| **🔄 Exception Handling** | Graceful handling of rejections, escalations, re-routing, and retries |
| **📊 Full Auditability** | Complete visibility into case status, ownership, decisions, and outcomes |
| **⏱️ SLA Management** | Automated escalation when cases exceed time thresholds |

---

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                     UiPath Maestro Case Management                  │
│                    (Orchestration & Governance Layer)                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────┐  ┌──────────────┐  ┌────────────┐  ┌──────────────┐ │
│  │  Intake   │  │    Fraud     │  │ Assessment │  │  Settlement  │ │
│  │  Agent    │→ │  Detection   │→ │   Agent    │→ │    Agent     │ │
│  │(AgentBldr)│  │   Agent      │  │(AgentBldr) │  │ (AgentBldr)  │ │
│  │          │  │ (Coded/Python)│  │            │  │              │ │
│  └────┬─────┘  └──────┬───────┘  └─────┬──────┘  └──────┬───────┘ │
│       │               │                │                 │         │
│  ┌────▼─────┐  ┌──────▼───────┐  ┌─────▼──────┐  ┌──────▼───────┐ │
│  │ Document │  │   Pattern    │  │  Policy    │  │   Payment    │ │
│  │Understanding│ │  Analysis   │  │  Lookup   │  │     API      │ │
│  │  (IDP)   │  │   Engine    │  │(API Wrkflw)│  │ (API Wrkflw) │ │
│  └──────────┘  └─────────────┘  └────────────┘  └──────────────┘ │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │              Human-in-the-Loop (Action Center)               │   │
│  │   • Adjuster Review  • Manager Escalation  • Final Approval  │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                    RPA Robots                                │   │
│  │   • Email Notifications  • Legacy System Entry  • Reporting  │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Data Flow

```
Claim Submitted → Intake Agent (extract data) → Case Created in Maestro
    → Triage (simple/complex routing)
    → Fraud Detection Agent (risk scoring)
        → Low Risk → Auto-Assessment Agent → Settlement Agent → Case Closed
        → High Risk → Human Adjuster (Action Center)
            → Approve → Settlement Agent → Case Closed
            → Reject → Rejection Notice (RPA) → Case Closed
            → Escalate → Senior Manager → Re-review
```

---

## 🧩 UiPath Components Used

| Component | How It's Used |
|---|---|
| **UiPath Maestro Case Management** | Core orchestration layer — manages claim lifecycle through 6 stages with SLA tracking, case assignments, and audit logging |
| **UiPath Agent Builder** | Low-code agents for Intake, Assessment, and Settlement workflows |
| **UiPath Coded Agents (Python SDK)** | Custom fraud detection agent with ML-based anomaly scoring |
| **UiPath Document Understanding** | Extracts structured data from claim forms, medical reports, photos, and invoices |
| **UiPath API Workflows** | Integrates with external policy database, payment gateway, and notification services |
| **UiPath RPA (Robots)** | Handles email notifications, legacy system data entry, and report generation |
| **UiPath Action Center** | Human-in-the-loop interface for adjuster reviews and manager escalations |
| **UiPath Automation Cloud** | Runtime environment for all agents, workflows, and orchestration |

---

## 🤖 Agent Types

This solution uses **both Coded Agents and Low-Code Agents**:

### Low-Code Agents (Agent Builder)
- **Intake Agent** — Receives claims, triggers Document Understanding, creates Maestro case
- **Assessment Agent** — Validates claim against policy terms, calculates coverage
- **Settlement Agent** — Processes approved claims, triggers payment API, generates confirmation

### Coded Agent (Python SDK)
- **Fraud Detection Agent** — Custom Python agent that analyzes claim patterns, checks for anomalies (duplicate claims, velocity checks, amount outliers), and returns a risk score

### Coding Agent (Development Tool)
- **Gemini CLI** — Used as AI-assisted development tool to scaffold agents, generate workflow logic, and write integration code (see [Coding Agent Usage](#-coding-agent-usage))

---

## 📊 Case Lifecycle

ClaimPilot manages claims through **6 Maestro Case stages**:

```
Stage 1: INTAKE          → Document extraction, data validation, case creation
Stage 2: TRIAGE          → Claim classification (simple/complex), routing decision
Stage 3: INVESTIGATION   → Fraud detection, evidence collection, risk scoring
Stage 4: ASSESSMENT      → Policy validation, coverage calculation, liability check
Stage 5: SETTLEMENT      → Payment processing, confirmation generation
Stage 6: CLOSED          → Audit trail finalized, case archived
```

### Exception Paths
- **Incomplete Documents** → Case paused, request sent to claimant, SLA timer starts
- **Fraud Detected** → Case escalated to human adjuster via Action Center
- **Amount > Threshold** → Automatic escalation to senior manager for approval
- **Rejection** → Rejection notice sent via RPA, case closed with reason code
- **SLA Breach** → Automatic escalation to next-level supervisor

---

## ⚙️ Setup Instructions

### Prerequisites

- Python 3.10+ installed
- UiPath Automation Cloud account with Maestro enabled
- UiPath Studio Web access
- Git

### Step 1: Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/claimpilot.git
cd claimpilot
```

### Step 2: Set Up the Python Environment

```bash
cd src
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Step 3: Configure Environment Variables

```bash
cp .env.example .env
# Edit .env with your UiPath credentials and API keys
```

### Step 4: Deploy to UiPath Automation Cloud

1. Log in to your UiPath Automation Cloud instance
2. Navigate to **Maestro** → **Case Definitions**
3. Import the case definition from `uipath/case-definition.json`
4. Navigate to **Agent Builder** → Import agents from `uipath/workflows/`
5. Configure Document Understanding models in **AI Center**
6. Set up API Workflow connections in **Integration Service**

### Step 5: Run the Solution

```bash
# Start the fraud detection coded agent
python src/agents/fraud_detection/agent.py

# The remaining agents run within UiPath Automation Cloud
# Trigger a test claim through the Maestro portal or API
```

See [docs/setup-guide.md](docs/setup-guide.md) for detailed configuration instructions.

---

## 🎬 Demo Video

> 📺 [Watch the demo on YouTube](YOUR_YOUTUBE_LINK_HERE)

The 5-minute demo walks through:
1. **0:00-0:30** — Problem overview and solution introduction
2. **0:30-1:30** — Claim submission and Intake Agent processing
3. **1:30-2:30** — Fraud Detection Agent analysis and case routing
4. **2:30-3:30** — Human adjuster review in Action Center
5. **3:30-4:30** — Settlement processing and case closure
6. **4:30-5:00** — Architecture overview and Maestro dashboard

---

## 🛠️ Coding Agent Usage

> **Coding Agent Used: Gemini CLI (Google)**

This project was developed with AI-assisted development using **Gemini CLI** as the primary coding agent. Below is documentation of how it was used:

### What Gemini CLI Built

| Component | Contribution |
|---|---|
| **Fraud Detection Agent** | Scaffolded the Python agent structure, anomaly detection algorithms, and UiPath SDK integration |
| **API Integration Code** | Generated API workflow connectors for policy lookup and payment processing |
| **Test Suite** | Created unit tests for fraud scoring logic and agent communication |
| **Documentation** | Generated README, architecture docs, and setup instructions |
| **Workflow Logic** | Assisted in designing Maestro Case stage transitions and exception paths |

### Evidence

- Development session logs are available in `docs/coding-agent-logs/`
- Screenshots of Gemini CLI interactions in `docs/coding-agent-screenshots/`
- All generated code was reviewed, modified, and integrated by the team

---

## 📁 Project Structure

```
claimpilot/
├── README.md                          # This file
├── LICENSE                            # MIT License
├── .gitignore
├── .env.example                       # Environment variable template
│
├── src/                               # Source code
│   ├── requirements.txt               # Python dependencies
│   ├── agents/
│   │   ├── fraud_detection/           # Coded Agent (Python SDK)
│   │   │   ├── __init__.py
│   │   │   ├── agent.py               # Main fraud detection agent
│   │   │   ├── scoring.py             # Risk scoring engine
│   │   │   ├── patterns.py            # Fraud pattern definitions
│   │   │   └── config.py              # Agent configuration
│   │   ├── intake/
│   │   │   ├── __init__.py
│   │   │   └── processor.py           # Intake processing logic
│   │   ├── assessment/
│   │   │   ├── __init__.py
│   │   │   └── evaluator.py           # Claim assessment logic
│   │   └── settlement/
│   │       ├── __init__.py
│   │       └── processor.py           # Settlement processing logic
│   └── utils/
│       ├── __init__.py
│       ├── uipath_client.py           # UiPath API client
│       ├── logger.py                  # Structured logging
│       └── models.py                  # Data models
│
├── uipath/                            # UiPath platform artifacts
│   ├── case-definition.json           # Maestro Case definition
│   ├── workflows/                     # Agent Builder workflow exports
│   └── forms/                         # Action Center form definitions
│
├── docs/                              # Documentation
│   ├── architecture.md                # Detailed architecture document
│   ├── setup-guide.md                 # Step-by-step setup instructions
│   ├── coding-agent-logs/             # Gemini CLI session evidence
│   └── coding-agent-screenshots/      # Development screenshots
│
├── tests/                             # Test suite
│   ├── test_fraud_detection.py
│   ├── test_scoring.py
│   └── test_models.py
│
└── assets/                            # Images and media
    └── claimpilot_thumbnail.png
```

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

> **Note:** This open-source license applies solely to the participant's original solution code. UiPath proprietary tools, activities, SDK packages, and platform components referenced or used within the solution remain subject to their own license terms.

---

<div align="center">

**Built for [UiPath AgentHack 2026](https://uipath-agenthack.devpost.com/) — Track 1: Maestro Case**

🛡️ ClaimPilot — Because every claim deserves intelligent orchestration.

</div>
