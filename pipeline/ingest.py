"""Hourly PM2.5 ingestion: backfills new stations, then only fetches new hours.

Run from the project root:   python pipeline/ingest.py
Safe to run as often as you like - the primary key on pm25_hourly rules out duplicates.
"""
import logging
import os
import time
from datetime import datetime, timedelta, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path

import psycopg2
import requests
import yaml
from dotenv import load_dotenv
from psycopg2.extras import execute_values

ROOT = Path(__file__).resolve().parent.parent
CFG = yaml.safe_load((Path(__file__).parent / "config.yaml").read_text(encoding="utf-8"))
API = "https://api.openaq.org/v3"
log = logging.getLogger("airwatch.ingest")

SELECT_TARGETS_SQL = """
with frozen as (
    select p.location_id
    from pm25_hourly p
    left join pm25_anomalies a using (location_id, sensor_id, ts)
    group by p.location_id
    having count(*) filter (where a.stuck) > %(frozen)s * count(*)
),
history as (select distinct location_id from pm25_hourly),
cand as (
    select s.location_id, s.name, s.city, s.pm25_sensor_ids,
           row_number() over (partition by s.city
                              order by (h.location_id is not null) desc, s.location_id) as rn,
           count(*) over (partition by s.city) as n_city
    from stations s
    left join history h on h.location_id = s.location_id
    where s.active and s.city is not null
      and s.location_id not in (select location_id from frozen)
),
top_cities as (
    select distinct city, n_city from cand order by n_city desc, city limit %(cities)s
)
select c.location_id, c.name, c.city, c.pm25_sensor_ids
from cand c join top_cities t on t.city = c.city
where c.rn <= %(per_city)s
order by c.city, c.rn
"""


def setup_logging():
    (ROOT / "logs").mkdir(exist_ok=True)
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    if not root.handlers:
        handlers = [
            logging.StreamHandler(),
            RotatingFileHandler(ROOT / "logs" / "pipeline.log", maxBytes=1_000_000,
                                backupCount=3, encoding="utf-8"),
        ]
        for h in handlers:
            h.setFormatter(fmt)
            root.addHandler(h)


def api_get(url, params, headers):
    """GET with retries for network errors, rate limits (429) and server errors (5xx)."""
    cfg = CFG["ingest"]
    for attempt in range(1, cfg["max_retries"] + 1):
        try:
            r = requests.get(url, headers=headers, params=params, timeout=cfg["timeout_seconds"])
        except requests.RequestException as e:
            log.warning("network error (attempt %d): %s", attempt, e)
            time.sleep(5 * attempt)
            continue
        if r.status_code == 429:
            log.warning("rate limited, waiting 60s")
            time.sleep(60)
            continue
        if r.status_code >= 500:
            log.warning("server error %d (attempt %d)", r.status_code, attempt)
            time.sleep(5 * attempt)
            continue
        return r
    return None


def parse_hours(location_id, sensor_id, results):
    """Turn an OpenAQ /hours payload into DB rows; skips malformed or empty values."""
    rows = []
    for item in results:
        try:
            ts = item["period"]["datetimeFrom"]["utc"]
            val = item["value"]
        except (KeyError, TypeError):
            continue
        if val is None:
            continue
        rows.append((location_id, sensor_id, ts, val))
    return rows


def fetch_sensor(cur, conn, headers, location_id, sensor_id, start, end):
    """Download [start, end] for one sensor, page by page. Returns (rows_written, ok)."""
    cfg = CFG["ingest"]
    written, page = 0, 1
    while True:
        time.sleep(cfg["pause_seconds"])
        r = api_get(f"{API}/sensors/{sensor_id}/hours", {
            "datetime_from": start.isoformat(), "datetime_to": end.isoformat(),
            "limit": cfg["page_size"], "page": page}, headers)
        if r is None or r.status_code != 200:
            log.error("sensor %s: giving up (HTTP %s)", sensor_id, getattr(r, "status_code", "none"))
            return written, False
        results = r.json().get("results", [])
        rows = parse_hours(location_id, sensor_id, results)
        if rows:
            execute_values(cur, "insert into pm25_hourly (location_id, sensor_id, ts, value) "
                                "values %s on conflict do nothing", rows)
            conn.commit()
            written += len(rows)
        if len(results) < cfg["page_size"]:
            return written, True
        page += 1


def main():
    load_dotenv(ROOT / ".env")
    setup_logging()
    headers = {"X-API-Key": os.getenv("OPENAQ_API_KEY")}
    conn = psycopg2.connect(os.getenv(CFG["database_url_env"]), connect_timeout=15)
    cur = conn.cursor()

    sel = CFG["selection"]
    cur.execute(SELECT_TARGETS_SQL, {"frozen": sel["max_frozen_share"],
                                     "cities": sel["top_cities"], "per_city": sel["stations_per_city"]})
    targets = cur.fetchall()
    log.info("monitoring %d stations in %d cities", len(targets), len({t[2] for t in targets}))

    end = datetime.now(timezone.utc)
    backfill_start = end - timedelta(days=CFG["ingest"]["backfill_days"])
    total, sensors_ok, sensors_failed = 0, 0, 0

    for location_id, name, city, sensor_ids in targets:
        cur.execute("select sensor_id, max(ts) from pm25_hourly where location_id = %s group by sensor_id",
                    (location_id,))
        latest = dict(cur.fetchall())
        station_rows = 0
        for sensor_id in sensor_ids:
            if sensor_id in latest:
                start = latest[sensor_id] + timedelta(seconds=1)
            else:
                start = backfill_start
            if start >= end - timedelta(hours=1):
                sensors_ok += 1
                continue
            n, ok = fetch_sensor(cur, conn, headers, location_id, sensor_id, start, end)
            station_rows += n
            sensors_ok += ok
            sensors_failed += (not ok)
        total += station_rows
        log.info("%-12s %-38s +%d rows", city, name[:38], station_rows)

    cur.execute("select count(*), max(ts) from pm25_hourly")
    n, newest = cur.fetchone()
    conn.close()
    log.info("done: +%d new rows | table now %d rows, newest %s | sensors ok=%d failed=%d",
             total, n, newest, sensors_ok, sensors_failed)
    if sensors_failed and sensors_failed >= sensors_ok:
        raise SystemExit("most sensors failed - marking run as failed")


if __name__ == "__main__":
    main()
