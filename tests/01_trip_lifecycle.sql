SELECT 'one_row_per_trip' AS test_name, count(*) AS failed_rows
FROM (SELECT trip_id FROM fct_trip_lifecycle GROUP BY trip_id HAVING count(*) > 1)
UNION ALL
SELECT 'valid_trips_have_valid_sequence', count(*)
FROM fct_trip_lifecycle
WHERE valid_for_trip_kpi AND ((accepted_at IS NOT NULL AND accepted_at < requested_at)
  OR (picked_up_at IS NOT NULL AND (accepted_at IS NULL OR picked_up_at < accepted_at))
  OR (completed_at IS NOT NULL AND (picked_up_at IS NULL OR completed_at < picked_up_at))
  OR (cancelled_at IS NOT NULL AND (cancelled_at < requested_at OR (accepted_at IS NOT NULL AND cancelled_at < accepted_at) OR picked_up_at IS NOT NULL)))
UNION ALL
SELECT 'valid_trips_have_positive_fare', count(*)
FROM fct_trip_lifecycle WHERE valid_for_trip_kpi AND gross_fare_twd <= 0;
