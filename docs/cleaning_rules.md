# Data Cleaning Rules

## Operating principle

Raw source tables are immutable. SQL adds standard fields and issue codes; it does not silently delete rows. A record can have more than one issue.

| Issue class | Detection | Treatment | KPI inclusion |
|---|---|---|---|
| Duplicate trip order | Same `trip_id`, later ingestion | Keep earliest source receipt | Earliest only |
| Duplicate event | Same trip, event type, event time | Keep earliest event receipt | Earliest only |
| Timestamp parsing | Source timestamp parsed with explicit `TIMESTAMPTZ` cast | Retain only when parse succeeds; otherwise quarantine through the downstream lifecycle check | Included only after valid parse |
| Late-arriving event | Ingested over 24 hours after event | Keep, mark `late_arrival` | Included after sequence check |
| Impossible event sequence | Completion before pickup; pickup before accept; cancellation before request/accept; or event steps reverse | Quarantine trip | Excluded |
| Invalid coordinates | 0,0; outside Taiwan bounds | Quarantine trip | Excluded from trip KPIs |
| Orphan relation | Missing user, driver, trip, or assignment | Quarantine affected record | Excluded from affected KPI |
| Financial integrity | Negative fare; refund exceeds charge | Quarantine payment or trip | Excluded from financial KPI |
| Promotion integrity | Discount exceeds fare, trip-user mismatch, wrong experiment code, or invalid airport/local-trip window | Keep trip, reject reward | Trip included; reward excluded |
| Plausible outlier | Long ETA, high fare, high speed near threshold | Retain with warning | Included in primary view and sensitivity check |

## Thresholds

- Taiwan coordinate bounds: latitude 21.5-25.5, longitude 119.0-122.5.
- Completion requires `requested <= accepted <= picked_up <= completed`.
- A cancellation must occur after request and before pickup.
- Maximum plausible average speed is 130 km/h; values above it are quarantined.
- Promotion discount must be positive, must not exceed fare, must match the assigned experiment arm, and must be redeemed by the same user as the trip.
- Airport rewards apply only to the first completed airport trip after the booked arrival; the Bundle second reward applies only to a later local trip within 7 days.
- A CRM send requires `crm_opt_in = true` at send time.

## Quality disposition

`record_disposition` is one of `kept`, `duplicate_excluded`, `quarantined`, or `kept_with_warning`. The current pipeline does not silently repair source values; it standardizes types, keeps the earliest duplicate receipt, and records every hard-invalid or warning issue separately.
