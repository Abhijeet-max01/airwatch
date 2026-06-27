import os
import requests
import psycopg2
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("OPENAQ_API_KEY")
headers = {"X-API-Key": api_key}

cities = {
    "Delhi": 8118,
    "Mumbai": 6967,
    "Bengaluru": 3409434,
    "Kolkata": 1236037,
    "Chennai": 8558,
}

# connect to your local Postgres database
conn = psycopg2.connect(host="localhost", database="airwatch", user="postgres")
cur = conn.cursor()

for city_name, location_id in cities.items():
    loc_url = f"https://api.openaq.org/v3/locations/{location_id}"
    loc_data = requests.get(loc_url, headers=headers).json()

    # collect ALL sensors that measure pm25 at this station — there can be more than one
    pm25_sensor_ids = [
        sensor["id"] for sensor in loc_data["results"][0]["sensors"]
        if sensor["parameter"]["name"] == "pm25"
    ]

    if not pm25_sensor_ids:
        print(f"{city_name}: no PM2.5 sensor found")
        continue

    latest_url = f"https://api.openaq.org/v3/locations/{location_id}/latest"
    latest_data = requests.get(latest_url, headers=headers).json()

    # of all matching pm25 sensors, keep only the one with the MOST RECENT reading
    pm25_readings = [r for r in latest_data["results"] if r["sensorsId"] in pm25_sensor_ids]

    if not pm25_readings:
        print(f"{city_name}: no recent PM2.5 reading found")
        continue

    best_reading = max(pm25_readings, key=lambda r: r["datetime"]["utc"])
    value = best_reading["value"]
    recorded_at = best_reading["datetime"]["local"]

    cur.execute(
        "INSERT INTO raw_air_quality (city, location_id, value, recorded_at) VALUES (%s, %s, %s, %s)",
        (city_name, location_id, value, recorded_at)
    )
    print(f"Inserted {city_name}: {value} µg/m³ (recorded {recorded_at})")

conn.commit()
cur.close()
conn.close()
print("Done — all rows saved.")