import os
from collections import Counter
import psycopg2
from dotenv import load_dotenv

load_dotenv()
conn = psycopg2.connect(os.getenv("SUPABASE_DB_URL"), connect_timeout=15)
cur = conn.cursor()
cur.execute("""
with r as (
  select location_id, sensor_id, ts, value,
         row_number() over (partition by location_id, sensor_id order by ts) as rn,
         row_number() over (partition by location_id, sensor_id, value order by ts) as rnv
  from pm25_hourly
), runs as (
  select location_id, sensor_id, value, count(*) as run_len,
         min(ts) as start_ts, max(ts) as end_ts
  from r
  group by location_id, sensor_id, value, (rn - rnv)
  having count(*) >= 12
)
select s.name, runs.value, runs.run_len, runs.start_ts, runs.end_ts
from runs join stations s using (location_id)
order by runs.run_len desc
""")
rows = cur.fetchall()
print(f"Runs of 12+ identical readings: {len(rows)}")

buckets = Counter()
for _, _, n, _, _ in rows:
    key = "12-15" if n <= 15 else "16-24" if n <= 24 else "25-48" if n <= 48 else "49+"
    buckets[key] += 1
print("Run lengths:", {k: buckets[k] for k in ["12-15", "16-24", "25-48", "49+"]})

print("\nLongest runs:")
for name, val, n, a, b in rows[:12]:
    print(f"  {name[:34]:<34} value={val:<7} {n:>4} readings  {str(a)[:10]} -> {str(b)[:10]}")

per_station = Counter()
for name, _, n, _, _ in rows:
    per_station[name] += n
print("\nStations with the most stuck readings:")
for name, n in per_station.most_common(8):
    print(f"  {name[:40]:<40} {n}")

vals = Counter()
for _, val, n, _, _ in rows:
    vals[val] += n
print("\nMost common repeated values (value: readings):")
for val, n in vals.most_common(8):
    print(f"  {val}: {n}")
conn.close()
