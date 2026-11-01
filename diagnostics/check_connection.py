import os
import psycopg2
import requests
from dotenv import load_dotenv

load_dotenv()

for key in ["OPENAQ_API_KEY", "OPENWEATHER_API_KEY", "SUPABASE_DB_URL"]:
    print(key, "->", "found" if os.getenv(key) else "MISSING")

print("\n--- Supabase ---")
try:
    conn = psycopg2.connect(os.getenv("SUPABASE_DB_URL"), connect_timeout=15)
    cur = conn.cursor()
    cur.execute("select count(*), count(distinct (location_id, recorded_at)), min(inserted_at), max(inserted_at) from raw_air_quality")
    total, unique, first, last = cur.fetchone()
    print(f"raw_air_quality: {total} rows, {unique} unique readings, {first} to {last}")
    cur.execute("select count(*) from raw_weather")
    print("raw_weather:", cur.fetchone()[0], "rows")
    conn.close()
    print("Supabase OK")
except Exception as e:
    print("Supabase FAILED:", e)

print("\n--- OpenAQ ---")
try:
    r = requests.get("https://api.openaq.org/v3/locations/8118", headers={"X-API-Key": os.getenv("OPENAQ_API_KEY")}, timeout=15)
    print("OpenAQ status:", r.status_code, "(200 = OK)")
except Exception as e:
    print("OpenAQ FAILED:", e)
