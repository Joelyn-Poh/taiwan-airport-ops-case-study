CREATE OR REPLACE TABLE mart_data_quality_report AS
SELECT
  issue_code,
  severity,
  disposition,
  count(*) AS affected_trip_records,
  count(DISTINCT trip_id) AS affected_trips
FROM trip_quality_issues
GROUP BY 1, 2, 3
ORDER BY CASE severity WHEN 'hard_invalid' THEN 1 ELSE 2 END, affected_trips DESC;

CREATE OR REPLACE TABLE mart_raw_vs_clean_kpi AS
WITH raw_metrics AS (
  SELECT
    count(*) AS raw_order_rows,
    count(DISTINCT trip_id) AS raw_distinct_trip_ids,
    avg((terminal_status = 'completed')::INTEGER) AS raw_completion_rate,
    avg((terminal_status = 'cancelled')::INTEGER) AS raw_cancellation_rate,
    sum(try_cast(gross_fare_twd AS DOUBLE)) FILTER (WHERE terminal_status = 'completed') AS raw_gross_fare_twd
  FROM raw_trip_orders
), clean_metrics AS (
  SELECT
    count(*) FILTER (WHERE valid_for_trip_kpi) AS clean_valid_trip_rows,
    avg((lifecycle_status = 'completed')::INTEGER) FILTER (WHERE valid_for_trip_kpi) AS clean_completion_rate,
    avg((lifecycle_status = 'cancelled')::INTEGER) FILTER (WHERE valid_for_trip_kpi) AS clean_cancellation_rate,
    sum(gross_fare_twd) FILTER (WHERE valid_for_trip_kpi AND lifecycle_status = 'completed') AS clean_gross_fare_twd
  FROM fct_trip_lifecycle
)
SELECT 'trip_rows' AS metric, raw_order_rows::DOUBLE AS raw_value, clean_valid_trip_rows::DOUBLE AS clean_value FROM raw_metrics CROSS JOIN clean_metrics
UNION ALL SELECT 'completion_rate', raw_completion_rate, clean_completion_rate FROM raw_metrics CROSS JOIN clean_metrics
UNION ALL SELECT 'cancellation_rate', raw_cancellation_rate, clean_cancellation_rate FROM raw_metrics CROSS JOIN clean_metrics
UNION ALL SELECT 'gross_fare_twd', raw_gross_fare_twd, clean_gross_fare_twd FROM raw_metrics CROSS JOIN clean_metrics;

CREATE OR REPLACE TABLE mart_pipeline_row_counts AS
SELECT 'raw_trip_orders' AS object_name, count(*) AS row_count FROM raw_trip_orders
UNION ALL SELECT 'deduplicated_trip_orders', count(*) FROM stg_trip_orders_dedup WHERE record_disposition = 'kept'
UNION ALL SELECT 'valid_trip_lifecycle', count(*) FROM fct_trip_lifecycle WHERE valid_for_trip_kpi
UNION ALL SELECT 'campaign_cohort', count(*) FROM mart_campaign_cohort;

CREATE OR REPLACE TABLE mart_campaign_budget_daily AS
WITH campaign_calendar AS (
  SELECT campaign_date::DATE AS campaign_date
  FROM generate_series(
    DATE '{{CAMPAIGN_START}}',
    DATE '{{CAMPAIGN_END}}' + INTERVAL '{{ATTRIBUTION_WINDOW_DAYS}} days',
    INTERVAL '1 day'
  ) AS t(campaign_date)
), daily_spend AS (
  SELECT CAST(r.redeemed_at AS DATE) AS campaign_date, sum(r.discount_twd) AS daily_spend_twd
  FROM fct_valid_redemptions r
  JOIN mart_campaign_cohort c ON r.user_id = c.user_id
  WHERE r.redemption_disposition = 'valid'
    AND CAST(r.redeemed_at AS DATE) BETWEEN DATE '{{CAMPAIGN_START}}' AND DATE '{{CAMPAIGN_END}}' + INTERVAL '{{ATTRIBUTION_WINDOW_DAYS}} days'
  GROUP BY 1
), budgeted AS (
  SELECT
    c.campaign_date,
    coalesce(d.daily_spend_twd, 0) AS daily_spend_twd,
    sum(coalesce(d.daily_spend_twd, 0)) OVER (ORDER BY c.campaign_date) AS cumulative_spend_twd,
    {{BUDGET_TWD}}::DOUBLE AS budget_twd,
    least(
      row_number() OVER (ORDER BY c.campaign_date),
      date_diff('day', DATE '{{CAMPAIGN_START}}', DATE '{{CAMPAIGN_END}}') + 1
    ) * ({{BUDGET_TWD}}::DOUBLE / (date_diff('day', DATE '{{CAMPAIGN_START}}', DATE '{{CAMPAIGN_END}}') + 1)) AS planned_cumulative_spend_twd
  FROM campaign_calendar c
  LEFT JOIN daily_spend d USING (campaign_date)
)
SELECT
  *,
  cumulative_spend_twd / nullif(budget_twd, 0) AS budget_spend_rate,
  CASE
    WHEN cumulative_spend_twd > budget_twd THEN 'alert_over_budget'
    WHEN cumulative_spend_twd > planned_cumulative_spend_twd * (1 + {{BUDGET_ALERT_PCT}}) THEN 'alert_over_pace'
    ELSE 'on_track'
  END AS budget_status
FROM budgeted;

CREATE OR REPLACE TABLE mart_campaign_budget_summary AS
SELECT
  max(budget_twd) AS budget_twd,
  max(cumulative_spend_twd) AS cumulative_spend_twd,
  max(budget_spend_rate) AS budget_spend_rate,
  max_by(budget_status, campaign_date) AS latest_budget_status,
  count(*) FILTER (WHERE budget_status <> 'on_track') AS alert_days
FROM mart_campaign_budget_daily;
