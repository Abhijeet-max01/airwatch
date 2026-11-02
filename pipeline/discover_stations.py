import os, json, time
import requests
from collections import Counter
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

load_dotenv()
HEADERS = {"X-API-Key": os.getenv("OPENAQ_API_KEY")}
URL = "https://api.openaq.org/v3/locations"

def fetch_all():
    results, page = [], 1
    while True:
        r = requests.get(URL, headers=HEADERS, timeout=30,
                         params={"iso": "IN", "parameters_id": 2, "limit": 1000, "page": page})
        if r.status_code == 429:
            print("rate limited, waiting 30s...")
            time.sleep(30)
            continue
        r.raise_for_status()
        batch = r.json()["results"]
        results.extend(batch)
        print(f"page {page}: {len(batch)} locations")
        if len(batch) < 1000:
            break
        page += 1
        time.sleep(1)
    return results

def parse(ts):
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))

locations = fetch_all()
cutoff = datetime.now(timezone.utc) - timedelta(days=3)

stations = []
for loc in locations:
    last = (loc.get("datetimeLast") or {}).get("utc")
    if not last:
        continue
    pm25_sensors = [s["id"] for s in loc["sensors"] if s["parameter"]["name"] == "pm25"]
    if not pm25_sensors:
        continue
    stations.append({
        "location_id": loc["id"],
        "name": loc["name"],
        "locality": loc.get("locality"),
        "lat": loc["coordinates"]["latitude"],
        "lon": loc["coordinates"]["longitude"],
        "provider": (loc.get("provider") or {}).get("name"),
        "pm25_sensor_ids": pm25_sensors,
        "last_utc": last,
        "active": parse(last) >= cutoff,
    })

active = [s for s in stations if s["active"]]
print(f"\nTotal PM2.5 locations in India: {len(stations)}")
print(f"Active in the last 3 days:      {len(active)}")
print(f"Stale (dead or paused):         {len(stations) - len(active)}")
print("\nTop providers among active stations:")
for name, n in Counter(s["provider"] for s in active).most_common(5):
    print(f"  {name}: {n}")
print("\nSample active stations:")
for s in active[:8]:
    print(f"  {s['location_id']:<9} {s['name'][:38]:<38} {s['locality']}")

json.dump(stations, open("stations_raw.json", "w"), indent=2)
print("\nSaved to stations_raw.json")
