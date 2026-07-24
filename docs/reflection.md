# Reflection — AirWatch: Foundations of Data Engineering
**Author:** Abhijeet Sirohi | B.Tech CSE-AIDE, 2nd Year  
**Internship:** June–July 2026 | Problem Statement: H1 — APIs to Warehouse  
**Date:** 25 July 2026

---

## 1. What I Built

AirWatch is an automated data pipeline that ingests real PM2.5 air quality readings from OpenAQ's government sensor network across five Indian cities — Delhi, Mumbai, Bengaluru, Kolkata, and Chennai — stores them permanently in a PostgreSQL warehouse, transforms them through a dbt staging-to-marts layer, and surfaces them on a live Streamlit dashboard at airwatch-india01.streamlit.app.

The pipeline runs hourly. Every run fetches the latest reading from verified, active monitoring stations run by CPCB, MPCB, KSPCB, WBPCB, and TNPCB — real government infrastructure, not synthetic data. The raw readings land in a `raw_air_quality` table, get transformed through six dbt models into daily averages, AQI categories, city rankings, and a sensor-error flagging layer, and are served through a dashboard that answers three questions: what is the air quality in these cities right now, how has it trended over the past month, and does today's weather explain the pollution level?

The mini-extension added OpenWeather as a second source. The same warehouse, same dbt project, one new ingestion connector — pulling temperature, humidity, and wind speed for the same five cities on the same hourly cadence. A `mart_pollution_weather_correlation` model joins both sources by city and date, producing a scatter plot and correlation coefficients that show the relationship between wind speed and PM2.5 across cities. During the monsoon period covered by this project, the pattern is clear: cities with higher wind speeds show lower PM2.5 — physically consistent with monsoon winds dispersing particulate matter.

A next-day PM2.5 forecast was added in the final week using linear regression on the daily trend. The model is intentionally simple and labeled as such — "≈47 µg/m³ ± 3, low confidence" — because the honest representation of a 4-week model is more valuable than a precise-looking number that overstates certainty.

---

## 2. What I Learned About the Tools

**Python and requests:** I knew Python before this internship. What I didn't know was what "knowing Python" actually means in a production context. Writing a script that calls an API once is straightforward. Writing one that handles multiple sensors per station, selects the correct one by recency, handles rate limits, retries on failure, and inserts rows idempotently is a different exercise. The gap between "I can write Python" and "I can write production Python" became very clear in Week 1.

**PostgreSQL:** I understood databases conceptually before this project. Running one, connecting to it from Python, understanding why `trust` vs `scram-sha-256` in `pg_hba.conf` matters, debugging a connection that works locally but fails on a cloud platform — these are things that only make sense when you've actually had to fix them. The Supabase DNS resolution failure taught me more about how database connections actually work than any lecture would have.

**dbt:** dbt's mental model — staging models clean, intermediate models aggregate, marts answer business questions — took about a week to actually internalize. Before that, I was writing it like SQL scripts with extra steps. After that, I understood why the dependency chain matters: when your mart model is wrong, you fix the intermediate model, not the raw data. The separation between "what the sensor said" and "what we believe is true" is not just clean architecture — it's the only defensible approach when dealing with real, imperfect sensor data.

**Streamlit:** faster than I expected for building something that looks real. Slower than I expected for controlling exactly how it looks. The gap between Streamlit's defaults and what a professional dashboard looks like is significant, and closing that gap required more CSS overriding than I anticipated. The 30-minute cache (`ttl=1800`) was a genuine engineering decision, not just a copy-pasted parameter — it prevents hammering the database on every page load.

**Supabase and cloud deployment:** the most frustrating and the most educational part of Week 4. DNS resolution failures, session pooler vs direct connection, the difference between `os.getenv()` and `st.secrets`, the fact that a Streamlit Cloud deployment can reach the pooler hostname but not the direct hostname on a particular network — none of this is in any tutorial. It's the kind of thing you only learn by hitting it and working through it.

---

## 3. What I Learned About Myself

I learned that I handle ambiguity better than I expected. The project had no single correct answer at any stage — which API to use, which station to pick, how to handle anomalous data, whether to delete or flag bad readings. Each of these required a judgment call, and making those calls explicitly (and writing them down in ADRs) turned out to be the part I found most satisfying.

I learned that I consistently underestimate how long debugging takes. Not writing code — debugging. The Mumbai sensor bug, the Supabase DNS failure, the Windows PATH issues with dbt, the Streamlit secret not being read by `os.getenv()` — each of these took longer than the feature it was blocking. In future projects, I will explicitly budget time for debugging rather than treating it as an unexpected interruption.

I learned that I work better when I understand the full picture before starting a piece. The weeks where I built on top of something I genuinely understood (Week 2 dbt after understanding Week 1 ingestion, Week 3 correlation after understanding dbt) went faster and produced cleaner code than the times I was building something I didn't fully grasp yet.

I also learned that pushing code every day is not just a discipline habit — it's a thinking tool. Writing a commit message forces you to articulate what you actually did, which sometimes reveals that you didn't fully understand it yourself.

---

## 4. What I'd Do Differently

If I restarted this project today, I would do three things differently.

First, I would verify station data freshness before committing to any city. I chose Kolkata's Dhopagachi station because it had the most recent `datetimeLast` at the time — and it stopped reporting two days later. A more robust approach would be to track multiple stations per city and failover automatically, rather than treating station selection as a one-time decision.

Second, I would set up Docker from Day 1 on a Linux machine or WSL2, rather than trying to run it on Windows 10. The virtualization conflict consumed real hours that could have gone into the actual pipeline. The native Postgres install worked as a substitute, but it meant the Docker Compose containerization — an explicit deliverable in the spec — stayed as a known gap rather than a completed requirement.

Third, I would start writing ADRs the day I made each decision, not batch them at the end. The ADR for the data quality strategy (ADR-003) was easy to write because I remembered every detail of finding the Mumbai anomaly. If I'd waited another two weeks, I would have written a vaguer, less accurate document.

---

## 5. What's Next — 3rd Year Plan

AirWatch is a foundation, not a finished product. The pipeline collects real data, the transformation layer is defensible, and the dashboard tells a real story. What it doesn't do yet is predict, generalize, or scale.

The 3rd year plan has three stages. First: add a proper next-day forecasting model using weather features as predictors (humidity, wind speed, temperature from OpenWeather) rather than just the PM2.5 trend itself. This requires more overlapping data than currently exists — the correlation between weather and pollution is visible in the scatter plot but not yet statistically robust enough to use as a model input. By October 2026, with three months of joint data, this becomes viable.

Second: replace the hourly polling architecture with OpenAQ's WebSocket feed for real-time event-driven ingestion. This is the streaming upgrade that maps directly to H3 in Segment 2 — the natural next step after mastering batch pipelines.

Third: add data contracts at the source boundary. The Mumbai sensor anomaly and the Dhopagachi station going offline both represent the same underlying problem — no formal agreement on what "valid data" means at the point of ingestion. Great Expectations or dbt's built-in contract features would formalize this.

By the time the 3rd year internship begins, AirWatch should be a multi-source, streaming-capable, forecasting-enabled environmental intelligence platform — not a dashboard that shows yesterday's PM2.5 numbers.

See `docs/roadmap_3rd_year.md` for the full milestone plan.