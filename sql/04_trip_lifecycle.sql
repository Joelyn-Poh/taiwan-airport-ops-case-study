CREATE OR REPLACE TABLE int_trip_event_pivot AS
SELECT
  trip_id,
  min(event_at) FILTER (WHERE event_type = 'requested') AS requested_event_at,
  min(event_at) FILTER (WHERE event_type = 'accepted') AS accepted_at,
  min(event_at) FILTER (WHERE event_type = 'driver_arrived') AS driver_arrived_at,
  min(event_at) FILTER (WHERE event_type = 'picked_up') AS picked_up_at,
  min(event_at) FILTER (WHERE event_type = 'completed') AS completed_at,
  min(event_at) FILTER (WHERE event_type = 'cancelled') AS cancelled_at
FROM stg_trip_events_dedup
WHERE record_disposition = 'kept'
GROUP BY trip_id;

CREATE OR REPLACE TABLE int_trip_event_sequence AS
WITH numbered_events AS (
  SELECT
    trip_id,
    event_type,
    event_at,
    ingested_at,
    event_id,
    CASE event_type
      WHEN 'requested' THEN 1 WHEN 'accepted' THEN 2 WHEN 'driver_arrived' THEN 3
      WHEN 'picked_up' THEN 4 WHEN 'completed' THEN 5 WHEN 'cancelled' THEN 5 ELSE 99
    END AS event_step
  FROM stg_trip_events_dedup
  WHERE record_disposition = 'kept'
)
SELECT
  trip_id,
  event_type,
  event_at,
  event_step,
  lag(event_type) OVER (PARTITION BY trip_id ORDER BY event_at, ingested_at, event_id) AS previous_event_type,
  lag(event_at) OVER (PARTITION BY trip_id ORDER BY event_at, ingested_at, event_id) AS previous_event_at,
  lag(event_step) OVER (PARTITION BY trip_id ORDER BY event_at, ingested_at, event_id) AS previous_event_step
FROM numbered_events;

INSERT INTO trip_quality_issues
SELECT o.trip_id, 'invalid_event_sequence', 'hard_invalid', 'quarantined'
FROM stg_trip_orders_dedup o
LEFT JOIN int_trip_event_pivot e USING (trip_id)
WHERE o.record_disposition = 'kept'
  AND (
    e.requested_event_at IS NULL
    OR (e.accepted_at IS NOT NULL AND e.accepted_at < e.requested_event_at)
    OR (e.picked_up_at IS NOT NULL AND (e.accepted_at IS NULL OR e.picked_up_at < e.accepted_at))
    OR (e.completed_at IS NOT NULL AND (e.picked_up_at IS NULL OR e.completed_at < e.picked_up_at))
    OR (e.cancelled_at IS NOT NULL AND (
      e.cancelled_at < e.requested_event_at
      OR (e.accepted_at IS NOT NULL AND e.cancelled_at < e.accepted_at)
      OR e.picked_up_at IS NOT NULL
    ))
  );

INSERT INTO trip_quality_issues
SELECT DISTINCT trip_id, 'non_monotonic_event_steps', 'hard_invalid', 'quarantined'
FROM int_trip_event_sequence
WHERE previous_event_step IS NOT NULL AND event_step < previous_event_step;

INSERT INTO trip_quality_issues
SELECT o.trip_id, 'implausible_speed', 'hard_invalid', 'quarantined'
FROM stg_trip_orders_dedup o
JOIN int_trip_event_pivot e USING (trip_id)
WHERE o.record_disposition = 'kept'
  AND e.completed_at IS NOT NULL
  AND date_diff('second', e.picked_up_at, e.completed_at) > 0
  AND o.estimated_distance_km / (date_diff('second', e.picked_up_at, e.completed_at) / 3600.0) > 130;

CREATE OR REPLACE TABLE fct_trip_lifecycle AS
WITH hard_invalid AS (
  SELECT DISTINCT trip_id FROM trip_quality_issues WHERE severity = 'hard_invalid'
)
SELECT
  o.trip_id, o.user_id, o.driver_id, o.requested_at,
  e.accepted_at, e.driver_arrived_at, e.picked_up_at, e.completed_at, e.cancelled_at,
  CASE WHEN e.completed_at IS NOT NULL THEN 'completed'
       WHEN e.cancelled_at IS NOT NULL THEN 'cancelled'
       ELSE 'incomplete' END AS lifecycle_status,
  o.cancel_reason, o.origin_zone, o.destination_zone, o.is_airport_trip,
  o.estimated_distance_km, o.gross_fare_twd, o.campaign_arm_at_request,
  date_diff('second', o.requested_at, e.picked_up_at) / 60.0 AS pickup_eta_min,
  CASE WHEN hi.trip_id IS NULL THEN true ELSE false END AS valid_for_trip_kpi,
  CASE WHEN hi.trip_id IS NULL THEN 'kept' ELSE 'quarantined' END AS record_disposition
FROM stg_trip_orders_dedup o
LEFT JOIN int_trip_event_pivot e USING (trip_id)
LEFT JOIN hard_invalid hi USING (trip_id)
WHERE o.record_disposition = 'kept';

CREATE OR REPLACE TABLE fct_valid_redemptions AS
WITH eligible_bookings AS (
  SELECT
    b.*,
    row_number() OVER (PARTITION BY b.user_id ORDER BY b.arrival_at, b.booking_id) AS booking_rank
  FROM stg_partner_bookings b
  WHERE b.booking_status = 'confirmed'
    AND b.arrival_at BETWEEN TIMESTAMPTZ '{{CAMPAIGN_START}} 00:00:00+08' AND TIMESTAMPTZ '{{CAMPAIGN_END}} 23:59:59+08'
), first_airport AS (
  SELECT
    b.user_id,
    min(f.requested_at) AS first_airport_requested_at
  FROM eligible_bookings b
  JOIN fct_trip_lifecycle f ON f.user_id = b.user_id
  WHERE b.booking_rank = 1
    AND f.valid_for_trip_kpi
    AND f.lifecycle_status = 'completed'
    AND f.is_airport_trip
    AND f.requested_at BETWEEN b.arrival_at AND b.arrival_at + INTERVAL '{{ATTRIBUTION_WINDOW_DAYS}} days'
  GROUP BY b.user_id
)
SELECT
  r.redemption_id,
  r.trip_id,
  r.user_id,
  r.promo_code,
  r.discount_twd,
  r.redeemed_at,
  a.experiment_arm,
  a.assigned_at,
  CASE
    WHEN f.trip_id IS NULL OR NOT f.valid_for_trip_kpi OR f.lifecycle_status <> 'completed' THEN 'rejected_invalid_trip'
    WHEN f.user_id <> r.user_id THEN 'rejected_trip_user_mismatch'
    WHEN a.user_id IS NULL OR a.assignment_conflict THEN 'rejected_assignment'
    WHEN b.booking_id IS NULL THEN 'rejected_booking'
    WHEN a.assigned_at NOT BETWEEN TIMESTAMPTZ '{{CAMPAIGN_START}} 00:00:00+08' AND TIMESTAMPTZ '{{CAMPAIGN_END}} 23:59:59+08' THEN 'rejected_assignment_outside_campaign'
    WHEN a.assigned_at > b.arrival_at THEN 'rejected_assignment_after_arrival'
    WHEN a.assigned_at > f.requested_at THEN 'rejected_assignment_after_trip_request'
    WHEN r.redeemed_at < a.assigned_at THEN 'rejected_before_assignment'
    WHEN r.discount_twd <= 0 OR r.discount_twd > f.gross_fare_twd THEN 'rejected_discount_amount'
    WHEN a.experiment_arm = 'control' THEN 'rejected_control_reward'
    WHEN a.experiment_arm = 'airport_150' AND r.promo_code <> 'TPE150' THEN 'rejected_promo_arm_mismatch'
    WHEN a.experiment_arm = 'bundle_100_100' AND r.promo_code NOT IN ('TPE100', 'LOCAL100') THEN 'rejected_promo_arm_mismatch'
    WHEN r.promo_code IN ('TPE150', 'TPE100') AND (
      NOT f.is_airport_trip
      OR f.requested_at < b.arrival_at
      OR f.requested_at > b.arrival_at + INTERVAL '{{ATTRIBUTION_WINDOW_DAYS}} days'
      OR EXISTS (
        SELECT 1
        FROM fct_trip_lifecycle previous_airport
        WHERE previous_airport.user_id = f.user_id
          AND previous_airport.valid_for_trip_kpi
          AND previous_airport.lifecycle_status = 'completed'
          AND previous_airport.is_airport_trip
          AND previous_airport.requested_at >= b.arrival_at
          AND previous_airport.requested_at < f.requested_at
      )
    ) THEN 'rejected_airport_reward_ineligible'
    WHEN r.promo_code = 'LOCAL100' AND (
      a.experiment_arm <> 'bundle_100_100'
      OR f.is_airport_trip
      OR fa.first_airport_requested_at IS NULL
      OR f.requested_at <= fa.first_airport_requested_at
      OR f.requested_at > fa.first_airport_requested_at + INTERVAL '{{ATTRIBUTION_WINDOW_DAYS}} days'
    ) THEN 'rejected_local_reward_ineligible'
    ELSE 'valid'
  END AS redemption_disposition
FROM stg_promo_redemptions r
LEFT JOIN fct_trip_lifecycle f USING (trip_id)
LEFT JOIN stg_campaign_assignments_dedup a ON r.user_id = a.user_id AND a.campaign_name = '{{CAMPAIGN_NAME}}'
LEFT JOIN eligible_bookings b ON r.user_id = b.user_id AND b.booking_rank = 1
LEFT JOIN first_airport fa ON r.user_id = fa.user_id;
