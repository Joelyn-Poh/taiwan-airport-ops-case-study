CREATE OR REPLACE TABLE trip_quality_issues AS
SELECT trip_id, 'invalid_coordinates' AS issue_code, 'hard_invalid' AS severity, 'quarantined' AS disposition
FROM stg_trip_orders_dedup
WHERE record_disposition = 'kept'
  AND (pickup_lat IS NULL OR pickup_lng IS NULL OR dropoff_lat IS NULL OR dropoff_lng IS NULL
       OR pickup_lat NOT BETWEEN 21.5 AND 25.5 OR pickup_lng NOT BETWEEN 119.0 AND 122.5
       OR dropoff_lat NOT BETWEEN 21.5 AND 25.5 OR dropoff_lng NOT BETWEEN 119.0 AND 122.5)
UNION ALL
SELECT trip_id, 'missing_requested_at', 'hard_invalid', 'quarantined'
FROM stg_trip_orders_dedup
WHERE record_disposition = 'kept' AND requested_at IS NULL
UNION ALL
SELECT o.trip_id, 'orphan_user', 'hard_invalid', 'quarantined'
FROM stg_trip_orders_dedup o LEFT JOIN stg_users u ON o.user_id = u.user_id
WHERE o.record_disposition = 'kept' AND u.user_id IS NULL
UNION ALL
SELECT o.trip_id, 'orphan_driver', 'hard_invalid', 'quarantined'
FROM stg_trip_orders_dedup o LEFT JOIN stg_drivers d ON o.driver_id = d.driver_id
WHERE o.record_disposition = 'kept' AND o.driver_id IS NOT NULL AND d.driver_id IS NULL
UNION ALL
SELECT trip_id, 'negative_fare', 'hard_invalid', 'quarantined'
FROM stg_trip_orders_dedup
WHERE record_disposition = 'kept' AND (gross_fare_twd IS NULL OR gross_fare_twd < 0)
UNION ALL
SELECT e.trip_id, 'future_or_unparseable_event_time', 'hard_invalid', 'quarantined'
FROM stg_trip_events_dedup e
WHERE e.record_disposition = 'kept' AND (e.event_at IS NULL OR e.event_at > TIMESTAMPTZ '2025-12-31 23:59:59+08')
UNION ALL
SELECT trip_id, 'late_arriving_event', 'warning', 'kept_with_warning'
FROM stg_trip_events_dedup
WHERE record_disposition = 'kept' AND ingested_at - event_at > INTERVAL '24 hours'
UNION ALL
SELECT o.trip_id, 'payment_exceeds_gross_fare', 'hard_invalid', 'quarantined'
FROM stg_trip_orders_dedup o
JOIN stg_payments p ON o.trip_id = p.trip_id
WHERE o.record_disposition = 'kept' AND p.payment_type = 'charge' AND p.payment_status = 'succeeded'
GROUP BY o.trip_id, o.gross_fare_twd
HAVING sum(p.amount_twd) > o.gross_fare_twd + 0.01;
