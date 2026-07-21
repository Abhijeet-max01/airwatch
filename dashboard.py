import os
import psycopg2
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="AirWatch — India Air Quality",
    layout="wide"
)

@st.cache_data(ttl=1800)
def load_data():
    try:
        db_url = st.secrets.get("SUPABASE_DB_URL") or os.getenv("SUPABASE_DB_URL")
        conn = psycopg2.connect(db_url)
        df = pd.read_sql("""
            SELECT
                city,
                reading_date,
                avg_pm25,
                max_pm25,
                num_readings,
                likely_sensor_error
            FROM mart_city_pollution_trends
            WHERE reading_date >= '2026-06-01'
            ORDER BY city, reading_date
        """, conn)
        conn.close()
        df['reading_date'] = pd.to_datetime(df['reading_date'])
        return df
    except Exception as e:
        st.warning(f"Database unavailable — showing sample data. Error: {e}")
        return pd.DataFrame({
            'city': ['Delhi', 'Mumbai', 'Bengaluru', 'Kolkata', 'Chennai'] * 3,
            'reading_date': pd.to_datetime(
                ['2026-06-25', '2026-07-10', '2026-07-18'] * 5
            ),
            'avg_pm25': [53.0, 44.0, 47.0, 26.0, 8.0, 26.0,
                        21.6, 33.0, 21.0, 65.1, 65.1, 65.1, 16.0, 23.0, 34.0],
            'max_pm25': [53.0, 44.0, 47.0, 26.0, 8.0, 26.0,
                        21.6, 33.0, 21.0, 65.1, 65.1, 65.1, 16.0, 23.0, 34.0],
            'num_readings': [1, 3, 2] * 5,
            'likely_sensor_error': [False] * 15
        })

df = load_data()
clean_df = df[df["likely_sensor_error"] == False]

# Header
st.title("AirWatch — India Air Quality Monitor")
st.caption("PM2.5 pollution tracking across 5 Indian cities · Source: OpenAQ government sensor network · Updated hourly")
st.divider()

# Latest readings
st.subheader("Latest Readings")
latest = clean_df.sort_values("reading_date").groupby("city").last().reset_index()
cols = st.columns(5)
for i, row in latest.iterrows():
    with cols[i % 5]:
        st.metric(
            label=row["city"],
            value=f"{row['avg_pm25']} µg/m³"
        )

st.divider()

# Trend chart
st.subheader("PM2.5 Trends by City")
cities = sorted(clean_df["city"].unique().tolist())
selected_cities = st.multiselect(
    "Cities",
    options=cities,
    default=cities
)

filtered = clean_df[clean_df["city"].isin(selected_cities)]

if not filtered.empty:
    fig = px.line(
        filtered,
        x="reading_date",
        y="avg_pm25",
        color="city",
        markers=True,
        labels={
            "reading_date": "Date",
            "avg_pm25": "Average PM2.5 (µg/m³)",
            "city": "City"
        }
    )
    fig.add_hline(
        y=15,
        line_dash="dot",
        line_color="#6b7280",
        annotation_text="WHO 24hr guideline — 15 µg/m³",
        annotation_position="top left",
        annotation_font_color="#6b7280"
    )
    fig.update_layout(
        height=420,
        margin=dict(t=20, b=20),
        xaxis_title="Date",
        yaxis_title="PM2.5 (µg/m³)",
        legend_title="City",
        hovermode="x unified"
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Select at least one city.")

st.divider()

# City ranking
st.subheader("City Rankings — Average PM2.5 (All Time)")
ranking = clean_df.groupby("city")["avg_pm25"].mean().round(2).sort_values(ascending=False).reset_index()
ranking.columns = ["City", "Average PM2.5 (µg/m³)"]
ranking.index = ranking.index + 1
st.dataframe(ranking, use_container_width=True)

st.divider()

# Full data table
st.subheader("Raw Data")
show_flagged = st.checkbox("Include flagged sensor readings", value=False)
display_df = df if show_flagged else clean_df
st.dataframe(
    display_df.sort_values(["reading_date", "city"], ascending=[False, True]),
    use_container_width=True
)

st.divider()
st.caption("Built by Abhijeet Sirohi · B.Tech CSE-AIDE · AirWatch v1.0 · Data: OpenAQ (government sensors)")