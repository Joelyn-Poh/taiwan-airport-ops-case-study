CREATE OR REPLACE TABLE mart_campaign_funnel AS
WITH crm AS (
  SELECT c.user_id,
    bool_or(c.crm_event_type = 'sent') AS crm_sent,
    bool_or(c.crm_event_type = 'opened') AS crm_opened,
    bool_or(c.crm_event_type = 'clicked') AS crm_clicked
  FROM stg_crm_events c
  JOIN stg_users u ON c.user_id = u.user_id
  WHERE c.campaign_name = '{{CAMPAIGN_NAME}}' AND u.crm_opt_in
  GROUP BY c.user_id
), trips AS (
  SELECT c.user_id,
    bool_or(f.is_airport_trip AND f.requested_at BETWEEN c.arrival_at AND c.arrival_at + INTERVAL '{{ATTRIBUTION_WINDOW_DAYS}} days') AS airport_requested,
    bool_or(f.is_airport_trip AND f.lifecycle_status = 'completed' AND f.requested_at BETWEEN c.arrival_at AND c.arrival_at + INTERVAL '{{ATTRIBUTION_WINDOW_DAYS}} days') AS airport_completed
  FROM mart_campaign_cohort c
  LEFT JOIN fct_trip_lifecycle f ON c.user_id = f.user_id AND f.valid_for_trip_kpi
  GROUP BY c.user_id
)
SELECT
  c.experiment_arm,
  count(*) AS assigned_users,
  count(*) FILTER (WHERE coalesce(crm.crm_sent, false)) AS crm_sent_users,
  count(*) FILTER (WHERE coalesce(crm.crm_opened, false)) AS crm_opened_users,
  count(*) FILTER (WHERE coalesce(crm.crm_clicked, false)) AS crm_clicked_users,
  count(*) FILTER (WHERE coalesce(trips.airport_requested, false)) AS airport_request_users,
  count(*) FILTER (WHERE coalesce(trips.airport_completed, false)) AS airport_completed_users,
  count(*) FILTER (WHERE i.completed_repeat_trip) AS repeat_trip_users,
  sum(i.reward_cost_twd) AS reward_cost_twd
FROM mart_campaign_cohort c
LEFT JOIN crm ON c.user_id = crm.user_id
LEFT JOIN trips ON c.user_id = trips.user_id
LEFT JOIN int_campaign_user i ON c.user_id = i.user_id
GROUP BY c.experiment_arm
ORDER BY CASE c.experiment_arm WHEN 'control' THEN 1 WHEN 'airport_150' THEN 2 ELSE 3 END;
