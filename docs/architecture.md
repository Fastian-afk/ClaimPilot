# ClaimPilot — Architecture

## System Architecture

ClaimPilot uses a multi-agent architecture orchestrated through UiPath Maestro Case Management.

### Agent Inventory

| Agent | Type | Runtime | Responsibility |
|---|---|---|---|
| **Intake Agent** | Low-code (Agent Builder) | UiPath Cloud | Receives claims, triggers Doc Understanding, creates case |
| **Fraud Detection Agent** | Coded (Python SDK) | UiPath Cloud | Analyzes fraud patterns, produces risk score |
| **Assessment Agent** | Low-code (Agent Builder) | UiPath Cloud | Validates policy coverage, calculates payout |
| **Settlement Agent** | Low-code (Agent Builder) | UiPath Cloud | Processes payment, generates confirmation |
| **Notification Bot** | RPA Robot | UiPath Cloud | Sends email notifications (approval, rejection, status) |

### Maestro Case Stages

```
INTAKE → TRIAGE → INVESTIGATION → ASSESSMENT → SETTLEMENT → CLOSED
```

### Exception Handling

1. **Fraud Escalation**: High-risk claims → Action Center → Human adjuster
2. **High-Value Review**: Claims >$20K → Senior adjuster approval
3. **SLA Breach**: Any stage exceeding SLA → Manager escalation
4. **Missing Documents**: Incomplete submissions → Pause + claimant notification

### Integration Points

- **Document Understanding**: Extracts data from PDFs, forms, photos
- **Policy Database**: API Workflow to external policy DB
- **Payment Gateway**: API Workflow to process settlements
- **Email Service**: RPA bot for notifications
- **Action Center**: Human-in-the-loop task management

### Data Flow

1. Claim arrives (email/portal/API)
2. Intake Agent extracts docs, validates, creates Maestro Case
3. Triage routes based on complexity
4. Fraud Detection Agent scores risk (0.0–1.0)
5. If high risk → Human adjuster via Action Center
6. If low risk → Assessment Agent evaluates coverage
7. Settlement Agent processes payment
8. Case closed with full audit trail
