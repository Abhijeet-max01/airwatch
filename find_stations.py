import os
import requests
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("OPENAQ_API_KEY")
headers = {"X-API-Key": api_key}

cities = {
    "Bengaluru": "12.9716,77.5946",
    "Kolkata": "22.5726,88.3639",
    "Chennai": "13.0827,80.2707",
}

url = "https://api.openaq.org/v3/locations"

for city_name, coords in cities.items():
    print(f"\n--- {city_name} ---")
    params = {
        "coordinates": coords,
        "radius": 25000,
        "parameters_id": 2,
        "limit": 20
    }
    response = requests.get(url, headers=headers, params=params)
    data = response.json()
    for loc in data["results"]:
        print(f"ID: {loc['id']:<8} Name: {loc['name']:<35} Last reading: {loc['datetimeLast']}")