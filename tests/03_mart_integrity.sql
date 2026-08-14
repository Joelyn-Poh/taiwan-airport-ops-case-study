SELECT 'experiment_has_exactly_one_control_row' AS test_name,
       abs(count(*) FILTER (WHERE experiment_arm = 'control') - 1) AS failed_rows
FROM mart_experiment_results
UNION ALL
SELECT 'marketplace_rates_in_bounds', count(*)
FROM mart_marketplace_hourly
WHERE (acceptance_rate IS NOT NULL AND acceptance_rate NOT BETWEEN 0 AND 1)
   OR (cancellation_rate IS NOT NULL AND cancellation_rate NOT BETWEEN 0 AND 1)
UNION ALL
SELECT 'quality_report_has_hard_invalid_records',
       CASE WHEN count(*) FILTER (WHERE severity = 'hard_invalid') > 0 THEN 0 ELSE 1 END
FROM mart_data_quality_report
UNION ALL
SELECT 'marketplace_guardrails_have_valid_status', count(*)
FROM mart_marketplace_guardrails
WHERE guardrail_status NOT IN ('pass', 'guardrail_breach', 'not_evaluable')
UNION ALL
SELECT 'budget_status_is_explicit', count(*)
FROM mart_campaign_budget_daily
WHERE budget_status NOT IN ('on_track', 'alert_over_pace', 'alert_over_budget');
