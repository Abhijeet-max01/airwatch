import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

# Connect to local Postgres
local_conn = psycopg2.connect(
    host="localhost",
    database="airwatch",
    user="postgres"
)
local_cur = local_conn.cursor()

# Connect to Supabase
supabase_conn = psycopg2.connect(os.getenv("SUPABASE_DB_URL"))
supabase_cur = supabase_conn.cursor()

# Migrate raw_air_quality
print("Migrating raw_air_quality...")
local_cur.execute("SELECT city, location_id, value, recorded_at FROM raw_air_quality")
rows = local_cur.fetchall()
for row in rows:
    supabase_cur.execute(
        "INSERT INTO raw_air_quality (city, location_id, value, recorded_at) VALUES (%s, %s, %s, %s)",
        row
    )
print(f"Inserted {len(rows)} rows into raw_air_quality")

# Migrate raw_weather
print("Migrating raw_weather...")
local_cur.execute("SELECT city, temperature, humidity, wind_speed, weather_description, recorded_at FROM raw_weather")
rows = local_cur.fetchall()
for row in rows:
    supabase_cur.execute(
        "INSERT INTO raw_weather (city, temperature, humidity, wind_speed, weather_description, recorded_at) VALUES (%s, %s, %s, %s, %s, %s)",
        row
    )
print(f"Inserted {len(rows)} rows into raw_weather")

supabase_conn.commit()
local_cur.close()
local_conn.close()
supabase_cur.close()
supabase_conn.close()
print("Migration complete!")