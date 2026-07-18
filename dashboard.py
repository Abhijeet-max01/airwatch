import os
import psycopg2
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# Page config
st.set_page_config(
    page_title="AirWatch — India Air Quality",
    page_icon="🌬️",
    layout="wide"
)

# Connect to Supabase and load data
@st.cache_data(ttl=3600)
def load_data():
    try:
        conn = psycopg2.connect(os.getenv("SUPABASE_DB_URL"))
        df = pd.read_sql("""
            SELECT
                city,
                reading_date,
                ROUND(avg_pm25::numeric, 2) as avg_pm25,
                ROUND(max_pm25::numeric, 2) as max_pm25,
                num_readings,
                likely_sensor_error
            FROM mart_city_pollution_trends
            ORDER BY city, reading_date
        """, conn)
        conn.close()
        return df
    except Exception as e:
        st.warning(f"Using sample data — database connection unavailable: {e}")
        return pd.DataFrame({
            'city': ['Delhi', 'Mumbai', 'Bengaluru', 'Kolkata', 'Chennai'],
            'reading_date': ['2026-07-18'] * 5,
            'avg_pm25': [44.0, 26.0, 33.02, 65.1, 23.0],
            'max_pm25': [44.0, 26.0, 33.02, 65.1, 23.0],
            'num_readings': [3, 2, 3, 4, 3],
            'likely_sensor_error': [False, False, False, False, False]
        })

df = load_data()

# Header
st.title("🌬️ AirWatch — India Air Quality Monitor")
st.markdown("Real-time PM2.5 pollution tracking across 5 major Indian cities, powered by OpenAQ.")
st.markdown("---")

# Top metrics row
st.subheader("Latest Clean Readings")
clean_df = df[df["likely_sensor_error"] == False]
latest = clean_df.sort_values("reading_date").groupby("city").last().reset_index()

cols = st.columns(5)
for i, row in latest.iterrows():
    with cols[i % 5]:
        st.metric(
            label=row["city"],
            value=f"{row['avg_pm25']} µg/m³",
            delta=None
        )

st.markdown("---")

# City filter
st.subheader("Pollution Trends by City")
cities = df["city"].unique().tolist()
selected_cities = st.multiselect(
    "Select cities to compare:",
    options=cities,
    default=cities
)

filtered = df[
    (df["city"].isin(selected_cities)) &
    (df["likely_sensor_error"] == False)
]

# Line chart
if not filtered.empty:
    pivot = filtered.pivot(index="reading_date", columns="city", values="avg_pm25")
    st.line_chart(pivot)
else:
    st.info("No clean data available for selected cities.")

st.markdown("---")

# Raw data table
st.subheader("Full Data Table")
show_flagged = st.checkbox("Show flagged sensor readings too", value=False)
if show_flagged:
    st.dataframe(df, use_container_width=True)
else:
    st.dataframe(clean_df, use_container_width=True)

# Footer
st.markdown("---")
st.caption("Data source: OpenAQ | Built by Abhijeet Sirohi | AirWatch v1.0")