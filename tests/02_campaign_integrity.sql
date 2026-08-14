SELECT 'cohort_has_crm_consent' AS test_name, count(*) AS failed_rows
FROM mart_campaign_cohort WHERE NOT crm_opt_in
UNION ALL
SELECT 'cohort_has_one_row_per_user', count(*)
FROM (SELECT user_id FROM mart_campaign_cohort GROUP BY user_id HAVING count(*) > 1)
UNION ALL
SELECT 'cohort_assignment_and_crm_precede_arrival', count(*)
FROM mart_campaign_cohort c
WHERE c.assigned_at > c.arrival_at
   OR NOT EXISTS (
     SELECT 1
     FROM stg_crm_events crm
     WHERE crm.user_id = c.user_id
       AND crm.campaign_name = '{{CAMPAIGN_NAME}}'
       AND crm.crm_event_type = 'sent'
       AND crm.event_at BETWEEN c.assigned_at AND c.arrival_at
   )
UNION ALL
SELECT 'valid_rewards_do_not_exceed_fare', count(*)
FROM fct_valid_redemptions r JOIN fct_trip_lifecycle f USING (trip_id)
WHERE redemption_disposition = 'valid' AND r.discount_twd > f.gross_fare_twd
UNION ALL
SELECT 'control_has_no_valid_reward', count(*)
FROM fct_valid_redemptions WHERE redemption_disposition = 'valid' AND experiment_arm = 'control'
UNION ALL
SELECT 'valid_reward_trip_user_matches', count(*)
FROM fct_valid_redemptions r
JOIN fct_trip_lifecycle f USING (trip_id)
WHERE r.redemption_disposition = 'valid' AND r.user_id <> f.user_id
UNION ALL
SELECT 'valid_reward_assignment_precedes_trip_request', count(*)
FROM fct_valid_redemptions r
JOIN fct_trip_lifecycle f USING (trip_id)
WHERE r.redemption_disposition = 'valid' AND r.assigned_at > f.requested_at
UNION ALL
SELECT 'valid_reward_matches_experiment_arm', count(*)
FROM fct_valid_redemptions
WHERE redemption_disposition = 'valid'
  AND ((experiment_arm = 'airport_150' AND promo_code <> 'TPE150')
    OR (experiment_arm = 'bundle_100_100' AND promo_code NOT IN ('TPE100', 'LOCAL100')))
UNION ALL
SELECT 'local_reward_follows_first_airport_trip', count(*)
FROM fct_valid_redemptions r
JOIN fct_trip_lifecycle f USING (trip_id)
WHERE r.redemption_disposition = 'valid'
  AND r.promo_code = 'LOCAL100'
  AND NOT EXISTS (
    SELECT 1
    FROM fct_trip_lifecycle first_airport
    WHERE first_airport.user_id = r.user_id
      AND first_airport.valid_for_trip_kpi
      AND first_airport.lifecycle_status = 'completed'
      AND first_airport.is_airport_trip
      AND first_airport.requested_at < f.requested_at
      AND f.requested_at <= first_airport.requested_at + INTERVAL '{{ATTRIBUTION_WINDOW_DAYS}} days'
  )
UNION ALL
SELECT 'd7_repeat_is_local_trip', count(*)
FROM int_campaign_user c
WHERE c.completed_repeat_trip
  AND NOT EXISTS (
    SELECT 1
    FROM fct_trip_lifecycle local_trip
    WHERE local_trip.user_id = c.user_id
      AND local_trip.valid_for_trip_kpi
      AND local_trip.lifecycle_status = 'completed'
      AND NOT local_trip.is_airport_trip
      AND local_trip.requested_at > c.first_airport_requested_at
      AND local_trip.requested_at <= c.first_airport_requested_at + INTERVAL '{{ATTRIBUTION_WINDOW_DAYS}} days'
  );
