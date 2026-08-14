"""Generate deterministic, intentionally imperfect ride-hailing data for this case study."""

from __future__ import annotations

import argparse
import csv
import json
import math
import random
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TZ_TAIPEI = timezone(timedelta(hours=8))

ZONES = {
    "TPE_AIRPORT": (25.0797, 121.2342),
    "TAIPEI_MAIN": (25.0478, 121.5170),
    "XIMENDING": (25.0422, 121.5063),
    "TAIPEI_101": (25.0339, 121.5654),
    "ZHONGSHAN": (25.0520, 121.5220),
    "SONGSHAN": (25.0635, 121.5520),
    "BANQIAO": (25.0143, 121.4610),
    "TAOYUAN_HSR": (25.0143, 121.2140),
    "TAMSUI": (25.1676, 121.4450),
}
CITY_ZONES = [zone for zone in ZONES if zone != "TPE_AIRPORT"]
MARKETS = ["Japan", "Korea", "Hong Kong", "Singapore", "USA", "Thailand"]


def iso(value: datetime) -> str:
    return value.astimezone(TZ_TAIPEI).isoformat(timespec="seconds")


def random_dt(rng: random.Random, start: datetime, end: datetime) -> datetime:
    return start + timedelta(seconds=rng.randrange(int((end - start).total_seconds())))


def jitter(rng: random.Random, point: tuple[float, float]) -> tuple[float, float]:
    return (round(point[0] + rng.uniform(-0.012, 0.012), 6), round(point[1] + rng.uniform(-0.012, 0.012), 6))


def haversine_km(a: tuple[float, float], b: tuple[float, float]) -> float:
    radius = 6371
    lat1, lon1, lat2, lon2 = map(math.radians, [a[0], a[1], b[0], b[1]])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return radius * 2 * math.asin(math.sqrt(h))


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def build_users(rng: random.Random, count: int, start: datetime) -> list[dict]:
    users = []
    for i in range(1, count + 1):
        signup = random_dt(rng, start - timedelta(days=540), start - timedelta(days=3))
        users.append(
            {
                "user_id": f"U{i:06d}",
                "signup_at": iso(signup),
                "home_market": rng.choice(MARKETS),
                "language": rng.choice(["en", "zh-TW", "ja", "ko"]),
                "crm_opt_in": rng.choices(["true", "false"], weights=[86, 14])[0],
                "fraud_exclusion": rng.choices(["false", "true"], weights=[99, 1])[0],
                "ingested_at": iso(signup + timedelta(minutes=rng.randint(1, 40))),
            }
        )
    return users


def build_drivers(rng: random.Random, count: int, start: datetime) -> list[dict]:
    rows = []
    for i in range(1, count + 1):
        joined = random_dt(rng, start - timedelta(days=720), start - timedelta(days=30))
        rows.append(
            {
                "driver_id": f"D{i:05d}",
                "join_at": iso(joined),
                "service_tier": rng.choices(["Taxi", "Comfort", "XL"], weights=[75, 20, 5])[0],
                "airport_eligible": rng.choices(["true", "false"], weights=[70, 30])[0],
                "ingested_at": iso(joined + timedelta(minutes=5)),
            }
        )
    return rows


def choose_hour(rng: random.Random, airport: bool = False) -> int:
    weights = [3] * 24
    for hour in ([5, 6, 7, 8, 9, 20, 21, 22, 23] if airport else [7, 8, 9, 17, 18, 19, 20]):
        weights[hour] = 9 if airport else 7
    return rng.choices(range(24), weights=weights)[0]


def make_trip(
    rng: random.Random,
    trip_no: int,
    user_id: str,
    driver_ids: list[str],
    requested_at: datetime,
    airport: bool,
    campaign_arm: str | None,
    campaign_end: datetime,
    attribution_window_days: int,
    event_rows: list[dict],
    payment_rows: list[dict],
    redemption_rows: list[dict],
) -> dict:
    trip_id = f"T{trip_no:07d}"
    origin_zone = "TPE_AIRPORT" if airport else rng.choice(CITY_ZONES)
    destination_zone = rng.choice(CITY_ZONES) if airport else rng.choice([zone for zone in CITY_ZONES if zone != origin_zone])
    pickup = jitter(rng, ZONES[origin_zone])
    dropoff = jitter(rng, ZONES[destination_zone])
    distance_km = max(1.1, haversine_km(pickup, dropoff) * rng.uniform(1.12, 1.35))
    peak_multiplier = 1.0 + (0.35 if requested_at.hour in [5, 6, 7, 8, 20, 21, 22, 23] else 0) + rng.uniform(0, 0.2)
    gross_fare = round((85 + distance_km * 15.5) * peak_multiplier, 0)
    request_roll = rng.random()
    terminal_status = "completed"
    driver_id = rng.choice(driver_ids)
    accepted_at = None
    pickup_at = None
    completed_at = None
    cancelled_at = None
    cancel_reason = None

    if request_roll < 0.055:
        terminal_status = "cancelled"
        driver_id = ""
        cancelled_at = requested_at + timedelta(minutes=rng.randint(2, 8))
        cancel_reason = "no_driver_available"
    else:
        accepted_at = requested_at + timedelta(minutes=rng.randint(1, 7))
        if request_roll < 0.125:
            terminal_status = "cancelled"
            cancelled_at = accepted_at + timedelta(minutes=rng.randint(1, 6))
            cancel_reason = rng.choice(["rider_cancelled", "driver_cancelled"])
        else:
            pickup_at = accepted_at + timedelta(minutes=rng.randint(4, 17))
            completed_at = pickup_at + timedelta(minutes=max(5, int(distance_km * rng.uniform(2.0, 3.5))))

    event_specs = [("requested", requested_at)]
    if accepted_at:
        event_specs.append(("accepted", accepted_at))
    if pickup_at:
        event_specs.extend([("driver_arrived", pickup_at - timedelta(minutes=1)), ("picked_up", pickup_at)])
    if completed_at:
        event_specs.append(("completed", completed_at))
    if cancelled_at:
        event_specs.append(("cancelled", cancelled_at))
    for event_type, event_at in event_specs:
        event_rows.append(
            {
                "event_id": f"E{len(event_rows) + 1:08d}",
                "trip_id": trip_id,
                "event_type": event_type,
                "event_at": iso(event_at),
                "ingested_at": iso(event_at + timedelta(minutes=rng.randint(0, 8))),
                "source": rng.choice(["rider_app", "driver_app", "dispatch"]),
            }
        )

    promo_amount = 0.0
    promo_code = ""
    if terminal_status == "completed" and campaign_arm in {"airport_150", "bundle_100_100"}:
        is_first_airport = airport
        if campaign_arm == "airport_150" and is_first_airport:
            promo_amount, promo_code = 150.0, "TPE150"
        elif campaign_arm == "bundle_100_100" and is_first_airport:
            promo_amount, promo_code = 100.0, "TPE100"
        elif campaign_arm == "bundle_100_100" and not airport and requested_at <= campaign_end + timedelta(days=attribution_window_days):
            promo_amount, promo_code = 100.0, "LOCAL100"
    if promo_amount:
        redemption_rows.append(
            {
                "redemption_id": f"R{len(redemption_rows) + 1:07d}",
                "trip_id": trip_id,
                "user_id": user_id,
                "promo_code": promo_code,
                "discount_twd": promo_amount,
                "redeemed_at": iso(completed_at),
                "ingested_at": iso(completed_at + timedelta(minutes=rng.randint(0, 15))),
            }
        )
    if terminal_status == "completed":
        payment_rows.append(
            {
                "payment_id": f"P{len(payment_rows) + 1:07d}",
                "trip_id": trip_id,
                "payment_type": "charge",
                "amount_twd": gross_fare - promo_amount,
                "payment_status": "succeeded",
                "paid_at": iso(completed_at + timedelta(minutes=1)),
                "ingested_at": iso(completed_at + timedelta(minutes=rng.randint(1, 12))),
            }
        )

    return {
        "trip_id": trip_id,
        "user_id": user_id,
        "driver_id": driver_id,
        "requested_at": iso(requested_at),
        "pickup_lat": pickup[0],
        "pickup_lng": pickup[1],
        "dropoff_lat": dropoff[0],
        "dropoff_lng": dropoff[1],
        "origin_zone": origin_zone,
        "destination_zone": destination_zone,
        "is_airport_trip": str(airport).lower(),
        "estimated_distance_km": round(distance_km, 2),
        "gross_fare_twd": gross_fare,
        "terminal_status": terminal_status,
        "cancel_reason": cancel_reason or "",
        "campaign_arm_at_request": campaign_arm or "unassigned",
        "ingested_at": iso(requested_at + timedelta(minutes=rng.randint(0, 10))),
    }


def inject_quality_issues(rng: random.Random, cfg: dict, tables: dict[str, list[dict]]) -> list[dict]:
    rates = cfg["dirty_data_rates"]
    manifest: list[dict] = []

    def register(issue: str, count: int, treatment: str) -> None:
        manifest.append({"issue_type": issue, "injected_rows": count, "expected_treatment": treatment})

    orders = tables["raw_trip_orders"]
    events = tables["raw_trip_events"]
    payments = tables["raw_payments"]
    assignments = tables["raw_campaign_assignments"]
    redemptions = tables["raw_promo_redemptions"]
    crm = tables["raw_crm_events"]

    count = int(len(orders) * rates["duplicate_trip_orders"])
    for row in rng.sample(orders, count):
        duplicate = row.copy()
        duplicate["ingested_at"] = iso(datetime.fromisoformat(row["ingested_at"]) + timedelta(minutes=20))
        orders.append(duplicate)
    register("duplicate_trip_order", count, "keep earliest receipt")

    count = int(len(events) * rates["duplicate_events"])
    for row in rng.sample(events, count):
        duplicate = row.copy()
        duplicate["event_id"] = f"{row['event_id']}-D"
        duplicate["ingested_at"] = iso(datetime.fromisoformat(row["ingested_at"]) + timedelta(minutes=10))
        events.append(duplicate)
    register("duplicate_event", count, "keep earliest receipt")

    completed = [row for row in events if row["event_type"] == "completed"]
    count = int(len(completed) * rates["out_of_order_events"])
    for row in rng.sample(completed, count):
        row["event_at"] = iso(datetime.fromisoformat(row["event_at"]) - timedelta(minutes=45))
    register("out_of_order_lifecycle", count, "quarantine trip")

    count = int(len(events) * rates["invalid_timestamps"])
    for row in rng.sample(events, count):
        row["event_at"] = "2027-01-01T00:00:00+08:00"
    register("invalid_timestamp", count, "quarantine trip")

    count = int(len(orders) * rates["invalid_coordinates"])
    for row in rng.sample(orders, count):
        row["pickup_lat"], row["pickup_lng"] = 0, 0
    register("invalid_coordinate", count, "quarantine trip")

    count = int(len(orders) * rates["orphan_foreign_keys"])
    for index, row in enumerate(rng.sample(orders, count)):
        row["user_id" if index % 2 == 0 else "driver_id"] = "MISSING_REFERENCE"
    register("orphan_foreign_key", count, "quarantine trip")

    count = int(len(orders) * rates["financial_integrity_issues"])
    for index, row in enumerate(rng.sample(orders, count)):
        if index % 2 == 0:
            row["gross_fare_twd"] = -abs(float(row["gross_fare_twd"]))
        else:
            candidates = [payment for payment in payments if payment["trip_id"] == row["trip_id"]]
            if candidates:
                candidates[0]["amount_twd"] = float(row["gross_fare_twd"]) * 2.2
    register("financial_integrity", count, "quarantine financial record")

    count = min(int(len(assignments) * rates["campaign_integrity_issues"]), len(assignments))
    for index, assignment in enumerate(rng.sample(assignments, count)):
        if index % 3 == 0:
            duplicate = assignment.copy()
            duplicate["assignment_id"] = f"{assignment['assignment_id']}-D"
            duplicate["experiment_arm"] = "bundle_100_100" if assignment["experiment_arm"] != "bundle_100_100" else "airport_150"
            assignments.append(duplicate)
        elif index % 3 == 1 and redemptions:
            redemption = rng.choice(redemptions)
            redemption["discount_twd"] = 9999
        else:
            assignment["assigned_at"] = "2025-12-30T12:00:00+08:00"
    register("campaign_integrity", count, "deduplicate or reject reward")

    count = int(len(events) * rates["late_arriving_events"])
    for row in rng.sample(events, count):
        row["ingested_at"] = iso(datetime.fromisoformat(row["event_at"]) + timedelta(hours=36))
    register("late_arriving_event", count, "retain with warning")

    opt_out_users = [row["user_id"] for row in tables["raw_users"] if row["crm_opt_in"] == "false"]
    count = min(max(1, int(len(crm) * 0.003)), len(opt_out_users))
    for user_id in rng.sample(opt_out_users, count):
        sent_at = datetime(2025, 9, 15, 9, 0, tzinfo=TZ_TAIPEI) + timedelta(minutes=rng.randint(0, 2000))
        crm.append(
            {
                "crm_event_id": f"C{len(crm) + 1:07d}",
                "user_id": user_id,
                "campaign_name": "TPE Arrival to Local",
                "crm_event_type": "sent",
                "event_at": iso(sent_at),
                "ingested_at": iso(sent_at + timedelta(minutes=1)),
            }
        )
    register("crm_opt_out_send", count, "exclude from campaign evidence")
    return manifest


def generate(cfg: dict, output_dir: Path) -> None:
    rng = random.Random(cfg["seed"])
    scale = cfg["sample_scale"]
    campaign = cfg["campaign"]
    campaign_start = datetime.fromisoformat(f"{campaign['start_date']}T00:00:00+08:00")
    campaign_end = datetime.fromisoformat(f"{campaign['end_date']}T23:59:59+08:00")
    attribution_window_days = int(campaign["attribution_window_days"])
    base_start = datetime(2025, 1, 1, tzinfo=TZ_TAIPEI)
    users = build_users(rng, scale["users"], base_start)
    drivers = build_drivers(rng, scale["drivers"], base_start)
    user_ids = [row["user_id"] for row in users]
    driver_ids = [row["driver_id"] for row in drivers]
    user_by_id = {row["user_id"]: row for row in users}

    target_users = rng.sample(user_ids, min(campaign["target_population"], len(user_ids)))
    bookings, assignments, crm = [], [], []
    for i, user_id in enumerate(target_users, 1):
        arrival = random_dt(rng, campaign_start, campaign_end)
        arrival = arrival.replace(hour=choose_hour(rng, airport=True), minute=rng.randint(0, 59), second=0)
        bookings.append(
            {
                "booking_id": f"B{i:06d}",
                "user_id": user_id,
                "partner_name": "Travel Partner X",
                "arrival_at": iso(arrival),
                "origin_market": user_by_id[user_id]["home_market"],
                "arrival_terminal": rng.choice(["T1", "T2"]),
                "booking_status": "confirmed",
                "ingested_at": iso(arrival - timedelta(days=rng.randint(3, 35))),
            }
        )
        control_share = float(campaign["control_share"])
        treatment_share = (1 - control_share) / 2
        arm = rng.choices(["control", "airport_150", "bundle_100_100"], weights=[control_share, treatment_share, treatment_share])[0]
        assigned_at = arrival - timedelta(days=rng.randint(1, 6))
        assignments.append(
            {
                "assignment_id": f"A{i:06d}",
                "user_id": user_id,
                "campaign_name": campaign["name"],
                "experiment_arm": arm,
                "assigned_at": iso(assigned_at),
                "assignment_status": "eligible",
                "ingested_at": iso(assigned_at + timedelta(minutes=rng.randint(1, 30))),
            }
        )
        if user_by_id[user_id]["crm_opt_in"] == "true":
            sent_at = assigned_at + timedelta(hours=rng.randint(1, 12))
            crm.append({"crm_event_id": f"C{len(crm) + 1:07d}", "user_id": user_id, "campaign_name": campaign["name"], "crm_event_type": "sent", "event_at": iso(sent_at), "ingested_at": iso(sent_at + timedelta(minutes=1))})
            if rng.random() < 0.48:
                opened = sent_at + timedelta(hours=rng.randint(1, 36))
                crm.append({"crm_event_id": f"C{len(crm) + 1:07d}", "user_id": user_id, "campaign_name": campaign["name"], "crm_event_type": "opened", "event_at": iso(opened), "ingested_at": iso(opened + timedelta(minutes=2))})
            if rng.random() < 0.21:
                clicked = sent_at + timedelta(hours=rng.randint(1, 48))
                crm.append({"crm_event_id": f"C{len(crm) + 1:07d}", "user_id": user_id, "campaign_name": campaign["name"], "crm_event_type": "clicked", "event_at": iso(clicked), "ingested_at": iso(clicked + timedelta(minutes=3))})

    event_rows, payment_rows, redemption_rows, trip_rows = [], [], [], []
    trip_no = 0
    for _ in range(scale["baseline_trips"]):
        user_id = rng.choice(user_ids)
        requested = random_dt(rng, base_start, campaign_end)
        requested = requested.replace(hour=choose_hour(rng), minute=rng.randint(0, 59), second=0)
        trip_no += 1
        trip_rows.append(make_trip(rng, trip_no, user_id, driver_ids, requested, rng.random() < 0.09, None, campaign_end, attribution_window_days, event_rows, payment_rows, redemption_rows))

    assignment_by_user = {row["user_id"]: row["experiment_arm"] for row in assignments}
    booking_by_user = {row["user_id"]: row for row in bookings}
    for user_id, arm in assignment_by_user.items():
        arrival = datetime.fromisoformat(booking_by_user[user_id]["arrival_at"])
        conversion_probability = {"control": 0.19, "airport_150": 0.31, "bundle_100_100": 0.29}[arm]
        if rng.random() < conversion_probability:
            trip_no += 1
            airport_trip = make_trip(rng, trip_no, user_id, driver_ids, arrival + timedelta(minutes=rng.randint(20, 120)), True, arm, campaign_end, attribution_window_days, event_rows, payment_rows, redemption_rows)
            trip_rows.append(airport_trip)
            if airport_trip["terminal_status"] == "completed":
                repeat_probability = {"control": 0.16, "airport_150": 0.22, "bundle_100_100": 0.42}[arm]
                if rng.random() < repeat_probability:
                    trip_no += 1
                    trip_rows.append(make_trip(rng, trip_no, user_id, driver_ids, datetime.fromisoformat(airport_trip["requested_at"]) + timedelta(days=rng.randint(1, attribution_window_days - 1), hours=rng.randint(2, 20)), False, arm, campaign_end, attribution_window_days, event_rows, payment_rows, redemption_rows))

    supply = []
    snapshot = campaign_start - timedelta(days=int(campaign["baseline_window_days"]))
    while snapshot <= campaign_end:
        for zone in ["TPE_AIRPORT", "TAIPEI_MAIN", "XIMENDING", "TAIPEI_101"]:
            peak = snapshot.hour in [5, 6, 7, 8, 20, 21, 22, 23]
            base_supply = 110 if zone == "TPE_AIRPORT" else 160
            available = max(20, int(rng.gauss(base_supply - (25 if peak else 0), 18)))
            demand = max(10, int(rng.gauss(base_supply * (1.15 if peak else 0.72), 22)))
            supply.append({"snapshot_hour": iso(snapshot), "service_zone": zone, "available_drivers": available, "requests": demand, "completed_trips": max(0, int(demand * rng.uniform(0.72, 0.91))), "ingested_at": iso(snapshot + timedelta(minutes=5))})
        snapshot += timedelta(hours=1)

    tables = {
        "raw_users": users,
        "raw_drivers": drivers,
        "raw_partner_bookings": bookings,
        "raw_trip_orders": trip_rows,
        "raw_trip_events": event_rows,
        "raw_payments": payment_rows,
        "raw_campaign_assignments": assignments,
        "raw_promo_redemptions": redemption_rows,
        "raw_crm_events": crm,
        "raw_supply_hourly": supply,
    }
    manifest = inject_quality_issues(rng, cfg, tables)
    for table_name, rows in tables.items():
        write_csv(output_dir / f"{table_name}.csv", rows)
    write_csv(output_dir.parent / "metadata" / "dirty_data_manifest.csv", manifest)
    write_csv(
        output_dir.parent / "public" / "market_context_assumptions.csv",
        [
            {"month": f"2025-{month:02d}", "inbound_demand_index": index, "airport_demand_index": round(index * 1.08, 1), "basis": "Synthetic planning index; official source link in docs/sources.md"}
            for month, index in enumerate([78, 74, 82, 85, 88, 91, 94, 98, 104, 102, 93, 86], 1)
        ],
    )
    print(json.dumps({"output_dir": str(output_dir), "rows": {name: len(rows) for name, rows in tables.items()}, "issues": dict(Counter({row['issue_type']: row['injected_rows'] for row in manifest}))}, ensure_ascii=False, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["sample"], default="sample")
    parser.add_argument("--output", type=Path, default=ROOT / "data" / "raw_sample")
    args = parser.parse_args()
    cfg = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
    generate(cfg, args.output)


if __name__ == "__main__":
    main()
