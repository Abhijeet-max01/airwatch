import os
import requests
import psycopg2
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("OPENWEATHER_API_KEY")

cities = {
    "Delhi": "Delhi,IN",
    "Mumbai": "Mumbai,IN",
    "Bengaluru": "Bangalore,IN",
    "Kolkata": "Kolkata,IN",
    "Chennai": "Chennai,IN",
}

conn = psycopg2.connect(host="localhost", database="airwatch", user="postgres")
cur = conn.cursor()

for city_name, query in cities.items():
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": query,
        "appid": api_key,
        "units": "metric"
    }
    response = requests.get(url, params=params)
    data = response.json()

    if response.status_code != 200:
        print(f"{city_name}: API error — {data.get('message', 'unknown error')}")
        continue

    temperature = data["main"]["temp"]
    humidity = data["main"]["humidity"]
    wind_speed = data["wind"]["speed"]
    description = data["weather"][0]["description"]
    recorded_at = data["dt"]

    cur.execute(
        """INSERT INTO raw_weather 
        (city, temperature, humidity, wind_speed, weather_description, recorded_at) 
        VALUES (%s, %s, %s, %s, %s, to_timestamp(%s))""",
        (city_name, temperature, humidity, wind_speed, description, recorded_at)
    )
    print(f"Inserted {city_name}: {temperature}°C, humidity {humidity}%, wind {wind_speed}m/s, {description}")

conn.commit()
cur.close()
conn.close()
print("Done — all weather rows saved.")