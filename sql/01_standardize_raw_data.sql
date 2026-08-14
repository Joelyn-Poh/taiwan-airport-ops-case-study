CREATE OR REPLACE TABLE stg_users AS
SELECT
  trim(user_id) AS user_id,
  try_cast(signup_at AS TIMESTAMPTZ) AS signup_at,
  trim(home_market) AS home_market,
  trim(language) AS language,
  lower(trim(CAST(crm_opt_in AS VARCHAR))) = 'true' AS crm_opt_in,
  lower(trim(CAST(fraud_exclusion AS VARCHAR))) = 'true' AS fraud_exclusion,
  try_cast(ingested_at AS TIMESTAMPTZ) AS ingested_at
FROM raw_users;

CREATE OR REPLACE TABLE stg_drivers AS
SELECT trim(driver_id) AS driver_id, try_cast(join_at AS TIMESTAMPTZ) AS join_at,
       trim(service_tier) AS service_tier, lower(trim(CAST(airport_eligible AS VARCHAR))) = 'true' AS airport_eligible,
       try_cast(ingested_at AS TIMESTAMPTZ) AS ingested_at
FROM raw_drivers;

CREATE OR REPLACE TABLE stg_partner_bookings AS
SELECT trim(booking_id) AS booking_id, trim(user_id) AS user_id, trim(partner_name) AS partner_name,
       try_cast(arrival_at AS TIMESTAMPTZ) AS arrival_at, trim(origin_market) AS origin_market,
       trim(arrival_terminal) AS arrival_terminal, trim(booking_status) AS booking_status,
       try_cast(ingested_at AS TIMESTAMPTZ) AS ingested_at
FROM raw_partner_bookings;

CREATE OR REPLACE TABLE stg_trip_orders AS
SELECT trim(trip_id) AS trip_id, trim(user_id) AS user_id, nullif(trim(driver_id), '') AS driver_id,
       try_cast(requested_at AS TIMESTAMPTZ) AS requested_at,
       try_cast(pickup_lat AS DOUBLE) AS pickup_lat, try_cast(pickup_lng AS DOUBLE) AS pickup_lng,
       try_cast(dropoff_lat AS DOUBLE) AS dropoff_lat, try_cast(dropoff_lng AS DOUBLE) AS dropoff_lng,
       trim(origin_zone) AS origin_zone, trim(destination_zone) AS destination_zone,
       lower(trim(is_airport_trip)) = 'true' AS is_airport_trip,
       try_cast(estimated_distance_km AS DOUBLE) AS estimated_distance_km,
       try_cast(gross_fare_twd AS DOUBLE) AS gross_fare_twd,
       lower(trim(terminal_status)) AS terminal_status, nullif(trim(cancel_reason), '') AS cancel_reason,
       trim(campaign_arm_at_request) AS campaign_arm_at_request,
       try_cast(ingested_at AS TIMESTAMPTZ) AS ingested_at
FROM raw_trip_orders;

CREATE OR REPLACE TABLE stg_trip_events AS
SELECT trim(event_id) AS event_id, trim(trip_id) AS trip_id, lower(trim(event_type)) AS event_type,
       try_cast(event_at AS TIMESTAMPTZ) AS event_at, try_cast(ingested_at AS TIMESTAMPTZ) AS ingested_at,
       trim(source) AS source
FROM raw_trip_events;

CREATE OR REPLACE TABLE stg_payments AS
SELECT trim(payment_id) AS payment_id, trim(trip_id) AS trip_id, lower(trim(payment_type)) AS payment_type,
       try_cast(amount_twd AS DOUBLE) AS amount_twd, lower(trim(payment_status)) AS payment_status,
       try_cast(paid_at AS TIMESTAMPTZ) AS paid_at, try_cast(ingested_at AS TIMESTAMPTZ) AS ingested_at
FROM raw_payments;

CREATE OR REPLACE TABLE stg_campaign_assignments AS
SELECT trim(assignment_id) AS assignment_id, trim(user_id) AS user_id, trim(campaign_name) AS campaign_name,
       lower(trim(experiment_arm)) AS experiment_arm, try_cast(assigned_at AS TIMESTAMPTZ) AS assigned_at,
       lower(trim(assignment_status)) AS assignment_status, try_cast(ingested_at AS TIMESTAMPTZ) AS ingested_at
FROM raw_campaign_assignments;

CREATE OR REPLACE TABLE stg_promo_redemptions AS
SELECT trim(redemption_id) AS redemption_id, trim(trip_id) AS trip_id, trim(user_id) AS user_id,
       trim(promo_code) AS promo_code, try_cast(discount_twd AS DOUBLE) AS discount_twd,
       try_cast(redeemed_at AS TIMESTAMPTZ) AS redeemed_at, try_cast(ingested_at AS TIMESTAMPTZ) AS ingested_at
FROM raw_promo_redemptions;

CREATE OR REPLACE TABLE stg_crm_events AS
SELECT trim(crm_event_id) AS crm_event_id, trim(user_id) AS user_id, trim(campaign_name) AS campaign_name,
       lower(trim(crm_event_type)) AS crm_event_type, try_cast(event_at AS TIMESTAMPTZ) AS event_at,
       try_cast(ingested_at AS TIMESTAMPTZ) AS ingested_at
FROM raw_crm_events;

CREATE OR REPLACE TABLE stg_supply_hourly AS
SELECT try_cast(snapshot_hour AS TIMESTAMPTZ) AS snapshot_hour, trim(service_zone) AS service_zone,
       try_cast(available_drivers AS INTEGER) AS available_drivers, try_cast(requests AS INTEGER) AS source_requests,
       try_cast(completed_trips AS INTEGER) AS source_completed_trips, try_cast(ingested_at AS TIMESTAMPTZ) AS ingested_at
FROM raw_supply_hourly;
