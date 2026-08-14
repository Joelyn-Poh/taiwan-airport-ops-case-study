# Metric Definitions

| Metric | Formula | Decision use |
|---|---|---|
| Eligible users | Unique users meeting partner, consent, history, and fraud exclusions | Campaign addressable audience |
| Airport conversion | Users with a completed airport trip / assigned users | First-trip activation |
| D7 repeat rate | Users with a second completed trip within 7 days / assigned users | Local habit formation |
| Incremental conversion | Treatment conversion - control conversion | Causal campaign effect |
| Incremental completed trips | Incremental conversion x treatment population | Extra completed trips estimate |
| Reward cost | Sum of valid promotion discounts | Budget control |
| Cost per incremental trip | Reward cost / incremental completed trips | Scheme efficiency |
| Incremental contribution | (Treatment average 7-day net contribution per assigned user - Control equivalent) x treatment assigned users | Primary commercial outcome; includes first and repeat trips plus valid rewards |
| P90 pickup ETA | 90th percentile of minutes from request to pickup | Rider reliability guardrail |
| Cancellation rate | Cancelled trips / requested trips | Marketplace guardrail |
| Acceptance rate | Accepted requests / requested trips | Driver-supply guardrail |
| Demand-supply gap | Requests - available drivers | Hourly intervention trigger |
| ETA change vs baseline | Campaign-period average hourly P90 ETA / pre-period equivalent - 1 | Rollout guardrail; breach above +10% |
| Cancellation change vs baseline | Campaign cancellation rate - pre-period equivalent | Rollout guardrail; breach above +1 percentage point |
| Budget spend rate | Cumulative valid reward spend / campaign budget, through campaign end plus the valid reward window | Budget pacing and alerting |

For Marketplace rates, a zone-hour with no observed cleaned trip is explicitly labelled `source_only_no_observed_trip`; it is not treated as a 0% acceptance or cancellation outcome. Baseline comparisons use the configured pre-campaign window.

All experiment metrics use intent-to-treat denominators: every allocated user stays in their assigned group even if they never redeem a reward.
