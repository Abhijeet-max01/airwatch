# Mock Interview Q&A — AirWatch

**5 questions a 3rd year internship interviewer would ask**

---

**Q1: Walk me through your project end to end.**

I built a data pipeline called AirWatch that ingests real PM2.5 air quality readings from OpenAQ's government sensor network across Delhi, Mumbai, Bengaluru, Kolkata, and Chennai. The pipeline runs hourly — a Python script calls OpenAQ's REST API, selects the correct PM2.5 sensor for each city by picking the one with the most recent timestamp, and inserts one row per city into a PostgreSQL raw table. dbt then rebuilds six transformation models on top: a staging layer that cleans column names, an intermediate layer that computes daily averages and peaks per city, and three mart layers — pollution trends with sensor error flags, city rankings, AQI categories, and a weather-pollution correlation model that joins OpenWeather data with the pollution readings. The output is served on a live Streamlit dashboard at airwatch-india01.streamlit.app, deployed on Streamlit Cloud with Supabase as the cloud Postgres warehouse.

---

**Q2: You mentioned a sensor bug. Tell me exactly what happened and how you fixed it.**

Mumbai's Sion station has two PM2.5 sensors — one active since 2016, one that stopped reporting in October 2022. My original ingestion script grabbed the first PM2.5 sensor match in the API response, which happened to be the dead 2022 one. The symptom was subtle: Mumbai was showing a reading dated 2022-10-31 while every other city showed 2026 data. I traced it back by querying the raw table, noticed the timestamp anomaly, then looked at the API response structure and found two sensors both labeled PM2.5. The fix was to collect all PM2.5 sensors at each station and select the one with the most recent datetime.utc field — so it can never accidentally pick a dead sensor regardless of list ordering. I also found that even the active sensor consistently reports 900+ µg/m³, which is physically impossible for PM2.5. I preserved that raw data but flagged it in the mart layer with a likely_sensor_error boolean, backed by a custom dbt test that verifies the flagging logic is internally consistent.

---

**Q3: Why did you choose dbt over just writing SQL queries directly?**

Three reasons. First, dependency management — dbt knows that mart_city_pollution_trends depends on int_daily_city_pm25, which depends on stg_air_quality. One dbt run command executes everything in the correct order automatically. If I was running raw SQL scripts, I'd have to manage that order manually. Second, testing — dbt lets me define data quality rules declaratively and run them with one command. My two custom tests (no negative PM2.5, flag consistency check) run automatically every time. Third, documentation — dbt generates a browseable documentation site from the models automatically. For a graded project where explaining decisions matters, having the transformation logic documented in the tool itself is significantly better than having it in comments in a SQL file.

---

**Q4: Your dashboard says "updated hourly" but you're using a 30-minute cache. Explain that decision.**

The cache and the update frequency are solving different problems. The pipeline updates hourly — meaning new rows land in Postgres every hour when the ingestion script runs. The 30-minute cache (ttl=1800) on the Streamlit side is about database connection management, not data freshness. Without a cache, every person who opens the dashboard URL triggers a new psycopg2 connection to Supabase, runs the query, and closes the connection. At low traffic that's fine, but it's not good practice and Supabase's free tier has connection limits. The cache means the query runs once, the result is held in memory, and subsequent visitors get the same result without a new connection until the cache expires. In practice, the data is never more than 90 minutes stale — 60 minutes maximum pipeline lag plus 30 minutes maximum cache lag — which is completely acceptable for hourly air quality data.

---

**Q5: What would you do differently if you had another month?**

Three things. First, replace the hourly polling with OpenAQ's WebSocket feed for event-driven ingestion instead of scheduled polling — the data would be fresher and the pipeline would be more efficient. Second, fix the Docker Compose containerization that I had to substitute with a native Postgres install due to a WSL2 virtualization conflict on my Windows machine. The pipeline works correctly but the containerization deliverable is incomplete. Third, add a proper multi-feature forecasting model once I have three or more months of weather and pollution data overlapping — the current linear regression on the pollution trend alone is honest about its limitations, but a model using wind speed and humidity as features would be genuinely more predictive and the data to train it properly will exist by October 2026.