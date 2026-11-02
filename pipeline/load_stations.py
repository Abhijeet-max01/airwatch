import os, json
import psycopg2
from psycopg2.extras import execute_values
from collections import Counter
from dotenv import load_dotenv

load_dotenv()

CITY_FIX = {"new delhi": "Delhi", "bangalore": "Bengaluru", "bengaluru": "Bengaluru"}

def parse_city_agency(name):
    if "," not in name:
        return None, None
    tail = name.rsplit(",", 1)[1].strip()
    parts = tail.split(" - ")
    city = parts[0].strip()
    agency = parts[1].strip() if len(parts) > 1 else None
    return CITY_FIX.get(city.lower(), city), agency

stations = json.load(open("stations_raw.json"))

conn = psycopg2.connect(os.getenv("SUPABASE_DB_URL"), connect_timeout=15)
cur = conn.cursor()

cur.execute("""
create table if not exists stations (
    location_id     integer primary key,
    name            text not null,
    city            text,
    agency          text,
    provider        text,
    lat             double precision,
    lon             double precision,
    pm25_sensor_ids integer[],
    last_utc        timestamptz,
    active          boolean,
    updated_at      timestamptz default now()
)
""")

cur.execute("""
create table if not exists pm25_hourly (
    location_id integer not null,
    sensor_id   integer not null,
    ts          timestamptz not null,
    value       double precision,
    loaded_at   timestamptz default now(),
    primary key (location_id, sensor_id, ts)
)
""")

rows = []
for s in stations:
    city, agency = parse_city_agency(s["name"])
    rows.append((s["location_id"], s["name"], city, agency, s["provider"],
                 s["lat"], s["lon"], s["pm25_sensor_ids"], s["last_utc"], s["active"]))

execute_values(cur, """
insert into stations (location_id, name, city, agency, provider, lat, lon, pm25_sensor_ids, last_utc, active)
values %s
on conflict (location_id) do update set
    name = excluded.name, city = excluded.city, agency = excluded.agency,
    provider = excluded.provider, lat = excluded.lat, lon = excluded.lon,
    pm25_sensor_ids = excluded.pm25_sensor_ids, last_utc = excluded.last_utc,
    active = excluded.active, updated_at = now()
""", rows)
conn.commit()

cur.execute("select count(*), count(*) filter (where active), count(*) filter (where city is null) from stations")
total, active, nocity = cur.fetchone()
print(f"stations loaded: {total} | active: {active} | no city parsed: {nocity}")

cur.execute("""
select city, count(*) from stations
where active and city is not null
group by city order by count(*) desc limit 15
""")
print("\nTop cities by active stations:")
for city, n in cur.fetchall():
    print(f"  {city:<22} {n}")

conn.close()
print("\nDone. Tables 'stations' and 'pm25_hourly' are ready.")
