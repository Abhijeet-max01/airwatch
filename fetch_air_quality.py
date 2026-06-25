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

    pm25_sensor_id = None
    for sensor in loc_data["results"][0]["sensors"]:
        if sensor["parameter"]["name"] == "pm25":
            pm25_sensor_id = sensor["id"]
            break

    if pm25_sensor_id is None:
        print(f"{city_name}: no PM2.5 sensor found")
        continue

    latest_url = f"https://api.openaq.org/v3/locations/{location_id}/latest"
    latest_data = requests.get(latest_url, headers=headers).json()

    for reading in latest_data["results"]:
        if reading["sensorsId"] == pm25_sensor_id:
            value = reading["value"]
            recorded_at = reading["datetime"]["local"]

            cur.execute(
                "INSERT INTO raw_air_quality (city, location_id, value, recorded_at) VALUES (%s, %s, %s, %s)",
                (city_name, location_id, value, recorded_at)
            )
            print(f"Inserted {city_name}: {value} µg/m³")
            break

conn.commit()
cur.close()
conn.close()
print("Done — all rows saved.")