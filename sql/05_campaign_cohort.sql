CREATE OR REPLACE TABLE mart_campaign_cohort AS
WITH eligible_bookings AS (
  SELECT
    b.*,
    row_number() OVER (PARTITION BY b.user_id ORDER BY b.arrival_at, b.booking_id) AS booking_rank
  FROM stg_partner_bookings b
  WHERE b.booking_status = 'confirmed'
    AND b.arrival_at BETWEEN TIMESTAMPTZ '{{CAMPAIGN_START}} 00:00:00+08' AND TIMESTAMPTZ '{{CAMPAIGN_END}} 23:59:59+08'
)
SELECT
  a.user_id, a.experiment_arm, a.assigned_at, b.booking_id, b.arrival_at, b.origin_market, b.arrival_terminal,
  u.language, u.crm_opt_in
FROM stg_campaign_assignments_dedup a
JOIN eligible_bookings b ON a.user_id = b.user_id AND b.booking_rank = 1
JOIN stg_users u ON a.user_id = u.user_id
WHERE a.campaign_name = '{{CAMPAIGN_NAME}}'
  AND a.assignment_status = 'eligible'
  AND NOT a.assignment_conflict
  AND a.assigned_at BETWEEN TIMESTAMPTZ '{{CAMPAIGN_START}} 00:00:00+08' AND TIMESTAMPTZ '{{CAMPAIGN_END}} 23:59:59+08'
  AND a.assigned_at <= b.arrival_at
  AND u.crm_opt_in
  AND NOT u.fraud_exclusion
  AND EXISTS (
    SELECT 1
    FROM stg_crm_events crm
    WHERE crm.user_id = a.user_id
      AND crm.campaign_name = '{{CAMPAIGN_NAME}}'
      AND crm.crm_event_type = 'sent'
      AND crm.event_at BETWEEN a.assigned_at AND b.arrival_at
  )
  AND NOT EXISTS (
    SELECT 1
    FROM fct_trip_lifecycle h
    WHERE h.user_id = a.user_id
      AND h.valid_for_trip_kpi
      AND h.lifecycle_status = 'completed'
      AND h.requested_at >= a.assigned_at - INTERVAL '{{PRIOR_TRIP_EXCLUSION_DAYS}} days'
      AND h.requested_at < a.assigned_at
  );

CREATE OR REPLACE TABLE int_campaign_user AS
WITH first_airport AS (
  SELECT c.user_id, min(f.requested_at) AS first_airport_requested_at
  FROM mart_campaign_cohort c
  JOIN fct_trip_lifecycle f ON c.user_id = f.user_id
  WHERE f.valid_for_trip_kpi AND f.lifecycle_status = 'completed' AND f.is_airport_trip
    AND f.requested_at BETWEEN c.arrival_at AND c.arrival_at + INTERVAL '{{ATTRIBUTION_WINDOW_DAYS}} days'
  GROUP BY c.user_id
), rewards AS (
  SELECT trip_id, sum(discount_twd) AS valid_reward_twd
  FROM fct_valid_redemptions WHERE redemption_disposition = 'valid'
  GROUP BY trip_id
)
SELECT
  c.*, fa.first_airport_requested_at,
  fa.first_airport_requested_at IS NOT NULL AS completed_airport_trip,
  EXISTS (
    SELECT 1 FROM fct_trip_lifecycle f
    WHERE f.user_id = c.user_id AND f.valid_for_trip_kpi AND f.lifecycle_status = 'completed'
      AND fa.first_airport_requested_at IS NOT NULL
      AND NOT f.is_airport_trip
      AND f.requested_at > fa.first_airport_requested_at
      AND f.requested_at <= fa.first_airport_requested_at + INTERVAL '{{ATTRIBUTION_WINDOW_DAYS}} days'
  ) AS completed_repeat_trip,
  coalesce((
    SELECT count(*)
    FROM fct_trip_lifecycle f
    WHERE f.user_id = c.user_id AND f.valid_for_trip_kpi AND f.lifecycle_status = 'completed'
      AND f.requested_at BETWEEN c.arrival_at AND c.arrival_at + INTERVAL '{{ATTRIBUTION_WINDOW_DAYS}} days'
  ), 0) AS completed_7d_trips,
  coalesce((
    SELECT sum(f.gross_fare_twd * 0.30 - coalesce(r.valid_reward_twd, 0))
    FROM fct_trip_lifecycle f LEFT JOIN rewards r USING (trip_id)
    WHERE f.user_id = c.user_id AND f.valid_for_trip_kpi AND f.lifecycle_status = 'completed'
      AND f.requested_at BETWEEN c.arrival_at AND c.arrival_at + INTERVAL '{{ATTRIBUTION_WINDOW_DAYS}} days'
  ), 0) AS net_contribution_twd,
  coalesce((
    SELECT sum(r.valid_reward_twd)
    FROM fct_trip_lifecycle f JOIN rewards r USING (trip_id)
    WHERE f.user_id = c.user_id AND f.valid_for_trip_kpi AND f.lifecycle_status = 'completed'
      AND f.requested_at BETWEEN c.arrival_at AND c.arrival_at + INTERVAL '{{ATTRIBUTION_WINDOW_DAYS}} days'
  ), 0) AS reward_cost_twd
FROM mart_campaign_cohort c
LEFT JOIN first_airport fa USING (user_id);
