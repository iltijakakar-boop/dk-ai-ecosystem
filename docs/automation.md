# AI Automation & Task Execution Framework

This document outlines the design and operational procedures of the AI Automation & Task Execution framework inside the DK AI Ecosystem.

## Architectural Overview

The automation framework consists of:
1. **Automation Service**: Central facade coordinating job life-cycle states, registration, and run executions.
2. **Priority Task Queue**: Background thread queue orchestrating execution tasks based on normal/priority weights.
3. **Scheduler Service**: Abstraction wrapper utilizing APScheduler for time-based triggers.
4. **Event Listener**: Ecosystem pub-sub coordinator matching event signals to active jobs.
5. **Rules Engine**: Conditional IF-THEN-ELSE evaluator for branching executions.

```mermaid
graph TD
    A[Trigger Source] -->|Manual/Scheduler/Event| B[Automation Service]
    B -->|Check Dependencies| C{Satisfied?}
    C -->|No| D[Wait status]
    C -->|Yes| E[Enqueue in Task Queue]
    E -->|Priority worker thread| F[Rules Engine / Target Actions]
    F -->|Run| G[Workflows / Agents]
    G -->|Transition logs| H[Execution History]
```

## REST API Endpoints

- `GET /api/v1/automation/jobs`: List registered jobs.
- `POST /api/v1/automation/jobs`: Register a new job.
- `GET /api/v1/automation/jobs/{id}/progress`: Query live percent progress.
- `GET /api/v1/automation/dashboard`: Retrieve dashboard metrics.
- `POST /api/v1/automation/webhook`: Receive incoming trigger webhooks.
