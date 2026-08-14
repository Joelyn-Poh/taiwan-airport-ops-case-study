"""Run the SQL transformations, export compact marts, and execute SQL assertions."""

from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path

import duckdb


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw_sample"
OUTPUT_DIR = ROOT / "outputs"
DB_PATH = OUTPUT_DIR / "airport_ops_case.duckdb"


def sql_path(path: Path) -> str:
    return path.as_posix().replace("'", "''")


def main() -> None:
    if not RAW_DIR.exists() or not list(RAW_DIR.glob("*.csv")):
        raise FileNotFoundError("Synthetic raw data not found. Run src/generate_synthetic_data.py first.")
    OUTPUT_DIR.mkdir(exist_ok=True)
    (OUTPUT_DIR / "data").mkdir(exist_ok=True)
    if DB_PATH.exists():
        DB_PATH.unlink()
    con = duckdb.connect(DB_PATH.as_posix())
    try:
        config = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
        campaign = config["campaign"]
        campaign_start = date.fromisoformat(campaign["start_date"])
        replacements = {
            "{{RAW_DIR}}": sql_path(RAW_DIR),
            "{{CAMPAIGN_START}}": campaign["start_date"],
            "{{CAMPAIGN_END}}": campaign["end_date"],
            "{{CAMPAIGN_NAME}}": campaign["name"],
            "{{BASELINE_START}}": (campaign_start - timedelta(days=int(campaign["baseline_window_days"]))).isoformat(),
            "{{ATTRIBUTION_WINDOW_DAYS}}": str(campaign["attribution_window_days"]),
            "{{PRIOR_TRIP_EXCLUSION_DAYS}}": str(campaign["prior_trip_exclusion_days"]),
            "{{BUDGET_TWD}}": str(campaign["budget_twd"]),
            "{{BUDGET_ALERT_PCT}}": str(campaign["budget_alert_pct"]),
        }
        for script in sorted((ROOT / "sql").glob("[0-9][0-9]_*.sql")):
            sql = script.read_text(encoding="utf-8")
            for token, value in replacements.items():
                sql = sql.replace(token, value)
            con.execute(sql)
            print(f"Executed {script.name}")

        test_results = []
        for script in sorted((ROOT / "tests").glob("*.sql")):
            sql = script.read_text(encoding="utf-8")
            for token, value in replacements.items():
                sql = sql.replace(token, value)
            cursor = con.execute(sql)
            columns = [item[0] for item in cursor.description]
            for row in cursor.fetchall():
                result = dict(zip(columns, row))
                result["source"] = script.name
                test_results.append(result)
        (OUTPUT_DIR / "test_results.json").write_text(json.dumps(test_results, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        failures = [row for row in test_results if int(row["failed_rows"]) > 0]
        if failures:
            raise AssertionError(f"SQL quality tests failed: {failures}")

        tables = [
            "mart_campaign_funnel",
            "mart_experiment_results",
            "mart_marketplace_hourly",
            "mart_marketplace_summary",
            "mart_marketplace_guardrails",
            "mart_campaign_budget_daily",
            "mart_data_quality_report",
            "mart_raw_vs_clean_kpi",
            "mart_pipeline_row_counts",
            "int_campaign_user",
        ]
        for table in tables:
            destination = OUTPUT_DIR / "data" / f"{table}.csv"
            con.execute(f"COPY {table} TO '{sql_path(destination)}' (HEADER, DELIMITER ',')")
        summary_tables = [
            "mart_pipeline_row_counts",
            "mart_data_quality_report",
            "mart_campaign_funnel",
            "mart_experiment_results",
            "mart_marketplace_summary",
            "mart_marketplace_guardrails",
            "mart_campaign_budget_daily",
            "mart_raw_vs_clean_kpi",
        ]
        summary = {}
        for table in summary_tables:
            cursor = con.execute(f"SELECT * FROM {table}")
            columns = [item[0] for item in cursor.description]
            summary[table] = [dict(zip(columns, row)) for row in cursor.fetchall()]
        (OUTPUT_DIR / "summary.json").write_text(
            json.dumps(summary, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
        )
        print(f"Pipeline completed. DuckDB database: {DB_PATH}")
    finally:
        con.close()


if __name__ == "__main__":
    main()
