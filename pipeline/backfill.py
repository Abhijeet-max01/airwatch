import os, time
import requests
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

load_dotenv()

DAYS = 90
TOP_CITIES = 10
PER_CITY = 3
PAUSE = 1.2  # seconds between API calls (OpenAQ free limit is ~60/min)

HEADERS = {"X-API-Key": os.getenv("OPENAQ_API_KEY")}
conn = psycopg2.connect(os.getenv("SUPABASE_DB_URL"), connect_timeout=15)
cur = conn.cursor()

cur.execute("select count(*) from stations")
if cur.fetchone()[0] == 0:
    raise SystemExit("stations table is empty - run load_stations.py first")

cur.execute("""
with ranked as (
    select location_id, name, city, pm25_sensor_ids,
           row_number() over (partition by city order by last_utc desc) as rn,
           count(*) over (partition by city) as n_city
    from stations
    where active and city is not null
), top_cities as (
    select distinct city, n_city from ranked order by n_city desc limit %s
)
select r.location_id, r.name, r.city, r.pm25_sensor_ids
from ranked r join top_cities t on r.city = t.city
where r.rn <= %s
order by t.n_city desc, r.city, r.rn
""", (TOP_CITIES, PER_CITY))
targets = cur.fetchall()
print(f"Backfilling {len(targets)} stations, last {DAYS} days\n")

end = datetime.now(timezone.utc)
start = end - timedelta(days=DAYS)

def get(url, params):
    for attempt in range(5):
        try:
            r = requests.get(url, headers=HEADERS, params=params, timeout=30)
        except requests.RequestException as e:
            print("   network error, retrying:", e)
            time.sleep(5)
            continue
        if r.status_code == 429:
            print("   rate limited, waiting 60s")
            time.sleep(60)
            continue
        if r.status_code >= 500:
            time.sleep(5)
            continue
        return r
    return None

total_new = 0
for location_id, name, city, sensor_ids in targets:
    station_rows = 0
    for sensor_id in sensor_ids:
        page = 1
        while True:
            time.sleep(PAUSE)
            r = get(f"https://api.openaq.org/v3/sensors/{sensor_id}/hours",
                    {"datetime_from": start.isoformat(), "datetime_to": end.isoformat(),
                     "limit": 1000, "page": page})
            if r is None or r.status_code != 200:
                print(f"   sensor {sensor_id}: HTTP {getattr(r, 'status_code', 'none')}, skipping")
                break
            results = r.json().get("results", [])
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
            if rows:
                execute_values(cur,
                    "insert into pm25_hourly (location_id, sensor_id, ts, value) values %s "
                    "on conflict do nothing", rows)
                conn.commit()
                station_rows += len(rows)
            if len(results) < 1000:
                break
            page += 1
    total_new += station_rows
    print(f"{city:<14} {name[:40]:<40} {station_rows} rows")

print(f"\nFetched {total_new} readings.")
cur.execute("select count(*), min(ts), max(ts), count(distinct location_id) from pm25_hourly")
n, lo, hi, st = cur.fetchone()
print(f"pm25_hourly now holds {n} rows from {st} stations, {lo} to {hi}")
conn.close()
