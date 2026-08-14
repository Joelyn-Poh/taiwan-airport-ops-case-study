# Postmortem

## Decision

Do not fully scale either current reward. Retain a Control holdout, reduce the subsidy or obtain partner co-funding, and pace CRM sends against Marketplace and budget guardrails.

## What changed after analysis

The first version over-simplified Marketplace hours without observed trips and calculated contribution from first-trip conversion only. The final pipeline labels non-observed hours explicitly, validates reward eligibility end to end, and compares full seven-day net contribution per assigned user against Control.

## Next experiment

Test a lower second-trip reward with partner funding, pre-register the causal and service-quality decision gates, and add customer-support, refund, and supply-incentive data.
