# Executive Summary

## From Dirty Ride Data to Operations Decisions

An independent, synthetic-data university portfolio project about ride-hailing platform operations.

### Decision

Do not fully scale either current reward. Keep a Control holdout, reduce the subsidy or obtain partner co-funding, and pace CRM sends against airport marketplace guardrails.

### Evidence

- SQL cleaning reduced 52,222 raw order rows to 48,347 trusted trip records.
- Airport 150 produced the strongest first-airport-trip lift: 8.7%, with a 95% CI of 5.5% to 11.9%.
- Bundle 100+100 delivered the highest D7 repeat rate at 8.3%, but both treatments had negative full seven-day incremental contribution after valid reward cost.
- Valid reward spend reached NT$208,900 against a NT$150,000 budget; the operating dashboard exposes pace alerts and service-quality guardrails.

### Repository guide

- `sql/`: DuckDB transformations, cohort logic, experiment measurement, marketplace and budget marts.
- `tests/`: lifecycle, promotion-integrity, and mart assertions.
- `dashboard/`: Excel operating dashboard.
- `report/`: Traditional Chinese closeout report and PDF.
- `docs/`: campaign brief, launch checklist, monitoring playbook, source notes, and definitions.

All operational records are synthetic and do not represent any real ride-hailing platform.
