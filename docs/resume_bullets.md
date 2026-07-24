# Resume Bullets — AirWatch

**For internship resume / placement CV:**

- Built an end-to-end data pipeline ingesting real PM2.5 air quality data from OpenAQ government sensors across 5 Indian cities into a PostgreSQL warehouse, automated hourly via Task Scheduler and GitHub Actions, with Supabase as the cloud warehouse
- Designed and implemented a 6-model dbt transformation layer (staging → intermediate → marts) with 5 passing data quality tests, including custom sensor-anomaly detection that identified and formally flagged a malfunctioning Mumbai monitoring station reporting physically impossible values (900+ µg/m³)
- Extended the pipeline with OpenWeather as a second data source, built a weather-pollution correlation model (mart_pollution_weather_correlation) and a next-day PM2.5 forecast using linear regression, deployed as a live public dashboard at airwatch-india01.streamlit.app using Streamlit Cloud + Supabase

**For LinkedIn / GitHub profile bio:**

Built AirWatch — a real-time air quality data pipeline (OpenAQ + OpenWeather → PostgreSQL → dbt → Streamlit) tracking PM2.5 across 5 Indian cities, with weather-pollution correlation analysis and next-day forecasting. Live at airwatch-india01.streamlit.app