import os
import requests
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

for city_name, location_id in cities.items():
    # Step 1: ask this station which of its sensors is the PM2.5 one
    loc_url = f"https://api.openaq.org/v3/locations/{location_id}"
    loc_data = requests.get(loc_url, headers=headers).json()

    pm25_sensor_id = None
    for sensor in loc_data["results"][0]["sensors"]:
        if sensor["parameter"]["name"] == "pm25":
            pm25_sensor_id = sensor["id"]
            break

    if pm25_sensor_id is None:
        print(f"\n--- {city_name} --- no PM2.5 sensor found here")
        continue

    # Step 2: get the latest readings, then keep only the PM2.5 one
    latest_url = f"https://api.openaq.org/v3/locations/{location_id}/latest"
    latest_data = requests.get(latest_url, headers=headers).json()

    for reading in latest_data["results"]:
        if reading["sensorsId"] == pm25_sensor_id:
            print(f"\n--- {city_name} ---")
            print(f"PM2.5: {reading['value']} µg/m³  (recorded: {reading['datetime']['local']})")
            break