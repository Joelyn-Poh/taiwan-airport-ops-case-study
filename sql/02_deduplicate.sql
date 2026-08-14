CREATE OR REPLACE TABLE stg_trip_orders_dedup AS
SELECT * EXCLUDE (row_num),
       CASE WHEN row_num = 1 THEN 'kept' ELSE 'duplicate_excluded' END AS record_disposition
FROM (
  SELECT *, row_number() OVER (PARTITION BY trip_id ORDER BY ingested_at NULLS LAST) AS row_num
  FROM stg_trip_orders
);

CREATE OR REPLACE TABLE stg_trip_events_dedup AS
SELECT * EXCLUDE (row_num),
       CASE WHEN row_num = 1 THEN 'kept' ELSE 'duplicate_excluded' END AS record_disposition
FROM (
  SELECT *, row_number() OVER (PARTITION BY trip_id, event_type, event_at ORDER BY ingested_at NULLS LAST, event_id) AS row_num
  FROM stg_trip_events
);

CREATE OR REPLACE TABLE stg_assignments_ranked AS
SELECT *,
  row_number() OVER (PARTITION BY user_id, campaign_name ORDER BY assigned_at NULLS LAST, ingested_at NULLS LAST) AS assignment_rank,
  count(DISTINCT experiment_arm) OVER (PARTITION BY user_id, campaign_name) > 1 AS assignment_conflict
FROM stg_campaign_assignments;

CREATE OR REPLACE TABLE stg_campaign_assignments_dedup AS
SELECT * EXCLUDE (assignment_rank)
FROM stg_assignments_ranked
WHERE assignment_rank = 1;
