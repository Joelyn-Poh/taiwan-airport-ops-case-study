CREATE OR REPLACE TABLE mart_marketplace_hourly AS
WITH trip_hourly AS (
  SELECT
    date_trunc('hour', requested_at) AS snapshot_hour,
    origin_zone AS service_zone,
    count(*) AS observed_requests,
    count(*) FILTER (WHERE accepted_at IS NOT NULL) AS accepted_requests,
    count(*) FILTER (WHERE lifecycle_status = 'completed') AS completed_trips,
    count(*) FILTER (WHERE lifecycle_status = 'cancelled') AS cancelled_trips,
    quantile_cont(pickup_eta_min, 0.90) FILTER (WHERE lifecycle_status = 'completed') AS p90_pickup_eta_min
  FROM fct_trip_lifecycle
  WHERE valid_for_trip_kpi
  GROUP BY 1, 2
)
SELECT
  s.snapshot_hour, s.service_zone, s.available_drivers,
  s.source_requests,
  t.observed_requests,
  t.accepted_requests,
  coalesce(t.completed_trips, s.source_completed_trips) AS completed_trips,
  t.cancelled_trips,
  t.p90_pickup_eta_min,
  CASE WHEN t.observed_requests IS NULL THEN 'source_only_no_observed_trip' ELSE 'observed' END AS metric_observation_status,
  CASE WHEN t.observed_requests > 0 THEN t.accepted_requests::DOUBLE / t.observed_requests END AS acceptance_rate,
  CASE WHEN t.observed_requests > 0 THEN t.cancelled_trips::DOUBLE / t.observed_requests END AS cancellation_rate,
  s.source_requests - s.available_drivers AS demand_supply_gap,
  s.snapshot_hour BETWEEN TIMESTAMPTZ '{{CAMPAIGN_START}} 00:00:00+08' AND TIMESTAMPTZ '{{CAMPAIGN_END}} 23:59:59+08' AS is_campaign_period,
  CASE
    WHEN t.observed_requests IS NULL THEN 'monitor_source_only'
    WHEN s.source_requests - s.available_drivers > 20 THEN 'increase_supply_or_pause_send'
    WHEN t.p90_pickup_eta_min > 20 THEN 'review_pickup_reliability'
    ELSE 'monitor'
  END AS operational_action
FROM stg_supply_hourly s
LEFT JOIN trip_hourly t USING (snapshot_hour, service_zone)
ORDER BY s.snapshot_hour, s.service_zone;

CREATE OR REPLACE TABLE mart_marketplace_summary AS
SELECT
  service_zone,
  count(*) AS zone_hours,
  count(*) FILTER (WHERE metric_observation_status = 'observed') AS observed_metric_hours,
  count(*) FILTER (WHERE metric_observation_status = 'source_only_no_observed_trip') AS source_only_hours,
  avg(acceptance_rate) AS acceptance_rate,
  avg(cancellation_rate) AS cancellation_rate,
  quantile_cont(p90_pickup_eta_min, 0.90) AS p90_of_p90_pickup_eta_min,
  avg(demand_supply_gap) AS avg_demand_supply_gap,
  count(*) FILTER (WHERE operational_action IN ('increase_supply_or_pause_send', 'review_pickup_reliability')) AS intervention_hours
FROM mart_marketplace_hourly
WHERE is_campaign_period
GROUP BY service_zone;

CREATE OR REPLACE TABLE mart_marketplace_guardrails AS
WITH period_metrics AS (
  SELECT
    service_zone,
    avg(p90_pickup_eta_min) FILTER (WHERE NOT is_campaign_period AND metric_observation_status = 'observed') AS baseline_avg_p90_pickup_eta_min,
    avg(cancellation_rate) FILTER (WHERE NOT is_campaign_period AND metric_observation_status = 'observed') AS baseline_cancellation_rate,
    avg(p90_pickup_eta_min) FILTER (WHERE is_campaign_period AND metric_observation_status = 'observed') AS campaign_avg_p90_pickup_eta_min,
    avg(cancellation_rate) FILTER (WHERE is_campaign_period AND metric_observation_status = 'observed') AS campaign_cancellation_rate,
    count(*) FILTER (WHERE is_campaign_period AND metric_observation_status = 'observed') AS campaign_observed_hours
  FROM mart_marketplace_hourly
  GROUP BY service_zone
)
SELECT
  *,
  campaign_avg_p90_pickup_eta_min / nullif(baseline_avg_p90_pickup_eta_min, 0) - 1 AS p90_eta_pct_change_vs_baseline,
  campaign_cancellation_rate - baseline_cancellation_rate AS cancellation_rate_pp_change_vs_baseline,
  CASE
    WHEN baseline_avg_p90_pickup_eta_min IS NULL OR campaign_avg_p90_pickup_eta_min IS NULL THEN 'not_evaluable'
    WHEN campaign_avg_p90_pickup_eta_min / nullif(baseline_avg_p90_pickup_eta_min, 0) - 1 > 0.10
      OR campaign_cancellation_rate - baseline_cancellation_rate > 0.01 THEN 'guardrail_breach'
    ELSE 'pass'
  END AS guardrail_status
FROM period_metrics;
