# Design Doc — AirWatch

**Author:** Abhijeet Sirohi
**Segment:** Foundations of Data Engineering
**Problem Statement:** H1 — APIs to Warehouse (official catalog problem)
**Date:** 24 June 2026

---

## 1. One-Line Description

A scheduled pipeline that ingests real air quality data (PM2.5, PM10, NO2, O3) from OpenAQ for five major Indian cities, lands it in a Postgres warehouse, transforms it with dbt into pollution-trend models, and surfaces it on a dashboard — with weather data added as a second source to explore what drives pollution spikes.

## 2. Problem Statement (why this, why me)

Air quality is a real, ongoing public health issue in Indian cities, and I wanted my first data engineering project to work with genuine, meaningful data rather than a toy dataset. Pairing pollution data with weather data lets me ask a real analytical question — does humidity, wind speed, or temperature correlate with pollution spikes the next day — instead of just moving numbers from one place to another. This project is also the foundation I plan to build on in 3rd year, eventually adding a forecasting layer once I'm ready to bring AI/ML into it.

## 3. Data Source

- **Primary API:** OpenAQ — real government/sensor-network air quality data (free, registration required)
  - Pollutants tracked: PM2.5, PM10, NO2, O3
  - Cities tracked: Delhi, Mumbai, Bengaluru, Kolkata, Chennai
- **Second source (mini-extension, Week 3):** OpenWeather — temperature, humidity, wind speed for the same five cities
- **Auth:** both require a free API key via registration
- **Call frequency (Week 1):** manual / on-demand → moves to scheduled (hourly) by Week 2

## 4. Architecture (Week 1 → Week 4 view)
[OpenAQ API]                    [OpenWeather API]  <-- added Week 3 (mini-extension)

|                                |

(Python script, requests, handles pagination + auth + rate limits)

|________________________________|

|

v

[raw_air_quality / raw_weather tables in Postgres]   <-- Week 1 target (OpenAQ only)

|

(dbt: staging -> intermediate -> marts)

|

v

[marts: city pollution trends, AQI summaries, pollution-weather correlation]

|

v

[Metabase / Streamlit dashboard]

|

(Airflow schedules the whole flow automatically) <-- added Week 2

(Docker Compose runs Postgres + Airflow + Metabase together)