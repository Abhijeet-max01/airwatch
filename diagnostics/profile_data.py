import os
import psycopg2
import pandas as pd
from dotenv import load_dotenv

load_dotenv()
conn = psycopg2.connect(os.getenv("SUPABASE_DB_URL"), connect_timeout=15)
pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 20)

def q(sql):
    return pd.read_sql(sql, conn)

print("=== 1. Per city overview ===")
print(q("""
select s.city, count(distinct h.location_id) as stations, count(*) as readings,
       round(avg(h.value)::numeric,1) as avg_pm25,
       round(percentile_cont(0.5) within group (order by h.value)::numeric,1) as median,
       max(h.value) as max_val, min(h.value) as min_val
from pm25_hourly h join stations s using (location_id)
group by s.city order by avg_pm25 desc
""").to_string(index=False))

print("\n=== 2. Impossible or suspicious values ===")
print(q("""
select count(*) filter (where value < 0)    as negative,
       count(*) filter (where value = 0)    as exactly_zero,
       count(*) filter (where value > 500)  as over_500,
       count(*) filter (where value > 1000) as over_1000
from pm25_hourly
""").to_string(index=False))

print("\n=== 3. Stuck sensors (same value repeated a lot) ===")
print(q("""
select s.name, count(*) as readings, count(distinct h.value) as distinct_values,
       round(100.0 * count(distinct h.value) / count(*), 1) as pct_distinct
from pm25_hourly h join stations s using (location_id)
group by s.name
having count(*) > 500
order by pct_distinct asc limit 5
""").to_string(index=False))

print("\n=== 4. Coverage (90 days = 2160 hours possible) ===")
print(q("""
select s.name, count(*) as hours_present,
       round(100.0 * count(*) / 2160, 1) as pct_coverage
from pm25_hourly h join stations s using (location_id)
group by s.name order by pct_coverage asc limit 5
""").to_string(index=False))

print("\n=== 5. Biggest hour-to-hour jumps ===")
print(q("""
select s.name, h.ts, h.value, h.prev_value, round((h.value - h.prev_value)::numeric,1) as jump
from (
    select location_id, ts, value,
           lag(value) over (partition by location_id, sensor_id order by ts) as prev_value
    from pm25_hourly
) h join stations s using (location_id)
where h.prev_value is not null
order by abs(h.value - h.prev_value) desc limit 5
""").to_string(index=False))

conn.close()
