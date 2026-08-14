CREATE OR REPLACE TABLE mart_experiment_results AS
WITH group_metrics AS (
  SELECT
    experiment_arm,
    count(*) AS assigned_users,
    sum(completed_airport_trip::INTEGER) AS airport_completed_users,
    sum(completed_repeat_trip::INTEGER) AS repeat_trip_users,
    sum(completed_7d_trips) AS completed_7d_trips,
    sum(reward_cost_twd) AS reward_cost_twd,
    sum(net_contribution_twd) AS observed_net_contribution_twd,
    avg(net_contribution_twd) AS net_contribution_per_assigned_twd
  FROM int_campaign_user
  GROUP BY experiment_arm
), control AS (
  SELECT assigned_users AS n0,
         airport_completed_users::DOUBLE / nullif(assigned_users, 0) AS p0,
         repeat_trip_users::DOUBLE / nullif(assigned_users, 0) AS repeat_rate_0,
         completed_7d_trips::DOUBLE / nullif(assigned_users, 0) AS completed_7d_trips_per_assigned,
         net_contribution_per_assigned_twd AS contribution_per_assigned_twd
  FROM group_metrics WHERE experiment_arm = 'control'
)
SELECT
  g.experiment_arm,
  g.assigned_users,
  g.airport_completed_users,
  g.repeat_trip_users,
  g.completed_7d_trips,
  g.airport_completed_users::DOUBLE / nullif(g.assigned_users, 0) AS airport_conversion_rate,
  g.repeat_trip_users::DOUBLE / nullif(g.assigned_users, 0) AS d7_repeat_rate,
  g.reward_cost_twd,
  g.observed_net_contribution_twd,
  g.airport_completed_users::DOUBLE / nullif(g.assigned_users, 0) - c.p0 AS incremental_conversion_rate,
  (g.airport_completed_users::DOUBLE / nullif(g.assigned_users, 0) - c.p0) * g.assigned_users AS incremental_completed_trips,
  (g.repeat_trip_users::DOUBLE / nullif(g.assigned_users, 0) - c.repeat_rate_0) AS incremental_repeat_rate,
  (g.repeat_trip_users::DOUBLE / nullif(g.assigned_users, 0) - c.repeat_rate_0) * g.assigned_users AS incremental_repeat_users,
  (g.completed_7d_trips::DOUBLE / nullif(g.assigned_users, 0) - c.completed_7d_trips_per_assigned) * g.assigned_users AS incremental_7d_completed_trips,
  (g.airport_completed_users::DOUBLE / nullif(g.assigned_users, 0) - c.p0)
    - 1.96 * sqrt((g.airport_completed_users::DOUBLE / nullif(g.assigned_users, 0)) * (1 - g.airport_completed_users::DOUBLE / nullif(g.assigned_users, 0)) / nullif(g.assigned_users, 0) + c.p0 * (1 - c.p0) / c.n0) AS incremental_conversion_ci_low,
  (g.airport_completed_users::DOUBLE / nullif(g.assigned_users, 0) - c.p0)
    + 1.96 * sqrt((g.airport_completed_users::DOUBLE / nullif(g.assigned_users, 0)) * (1 - g.airport_completed_users::DOUBLE / nullif(g.assigned_users, 0)) / nullif(g.assigned_users, 0) + c.p0 * (1 - c.p0) / c.n0) AS incremental_conversion_ci_high,
  (g.net_contribution_per_assigned_twd - c.contribution_per_assigned_twd) * g.assigned_users AS incremental_contribution_twd,
  g.net_contribution_per_assigned_twd - c.contribution_per_assigned_twd AS incremental_contribution_per_assigned_twd,
  g.reward_cost_twd / nullif((g.airport_completed_users::DOUBLE / nullif(g.assigned_users, 0) - c.p0) * g.assigned_users, 0) AS cost_per_incremental_trip_twd,
  CASE
    WHEN g.experiment_arm = 'control' THEN 'baseline'
    WHEN (g.airport_completed_users::DOUBLE / nullif(g.assigned_users, 0) - c.p0) > 0
      AND ((g.airport_completed_users::DOUBLE / nullif(g.assigned_users, 0) - c.p0)
        - 1.96 * sqrt((g.airport_completed_users::DOUBLE / nullif(g.assigned_users, 0)) * (1 - g.airport_completed_users::DOUBLE / nullif(g.assigned_users, 0)) / nullif(g.assigned_users, 0) + c.p0 * (1 - c.p0) / c.n0)) > 0
      AND ((g.net_contribution_per_assigned_twd - c.contribution_per_assigned_twd) * g.assigned_users) > 0
    THEN 'candidate_rollout'
    ELSE 'hold_or_redesign'
  END AS experiment_decision
FROM group_metrics g CROSS JOIN control c
ORDER BY CASE g.experiment_arm WHEN 'control' THEN 1 WHEN 'airport_150' THEN 2 ELSE 3 END;
