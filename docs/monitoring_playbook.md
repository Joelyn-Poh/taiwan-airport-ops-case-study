# Monitoring Playbook

## Daily view

Review eligible users, delivered CRM, airport requests, completed airport trips, reward spend, P90 pickup ETA, cancellations, acceptance, and support contacts.

## Escalation rules

| Signal | Trigger | Action |
|---|---|---|
| Service quality | P90 pickup ETA > baseline +10% for 2 hours | Pause new sends; assess driver incentive / zone restriction. |
| Cancellations | +1 percentage point versus control | Inspect supply, pickup instructions, and payment failures. |
| Budget pace | Spend exceeds pro-rata plan by 15% | Cap the reward or narrow the target cohort. |
| Reward defect | Invalid redemption rate > 0.5% | Disable offer; reconcile assignment and expiration logic. |
| Data pipeline | Quality check fails | Freeze dashboard decision; investigate raw data and rerun pipeline. |

## Weekly business review

Use intent-to-treat results, not redemption-only results. Record a single decision: expand, modify, hold, or stop; then name an owner and due date.
