import os
import psycopg2
import pandas as pd
import streamlit as st
import plotly.express as px
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
        st.warning(f"Database unavailable — {e}")
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

@st.cache_data(ttl=1800)
def load_correlation():
    try:
        db_url = st.secrets.get("SUPABASE_DB_URL") or os.getenv("SUPABASE_DB_URL")
        conn = psycopg2.connect(db_url)
        df = pd.read_sql("""
            SELECT
                city,
                reading_date,
                avg_pm25,
                avg_temp,
                avg_humidity,
                avg_wind_speed,
                weather_pollution_pattern
            FROM mart_pollution_weather_correlation
            ORDER BY city, reading_date
        """, conn)
        conn.close()
        df['reading_date'] = pd.to_datetime(df['reading_date'])
        return df
    except Exception as e:
        return pd.DataFrame()

def get_recommendation(pm25):
    if pm25 <= 30:
        return "Good", "Safe for all outdoor activities including exercise.", "#22c55e"
    elif pm25 <= 60:
        return "Satisfactory", "Acceptable. Sensitive individuals should limit prolonged outdoor exertion.", "#84cc16"
    elif pm25 <= 90:
        return "Moderate", "Children and elderly should avoid outdoor exertion.", "#eab308"
    elif pm25 <= 120:
        return "Poor", "Reduce outdoor activities. Wear a mask if going outside.", "#f97316"
    elif pm25 <= 250:
        return "Very Poor", "Avoid going outside. Keep windows closed.", "#ef4444"
    else:
        return "Severe", "Health emergency. Do not go outside.", "#7c3aed"

df = load_data()
clean_df = df[df["likely_sensor_error"] == False]
corr_df = load_correlation()
latest = clean_df.sort_values("reading_date").groupby("city").last().reset_index()

# Header
st.title("AirWatch — India Air Quality Monitor")
st.caption("PM2.5 pollution tracking across 5 Indian cities · Source: OpenAQ government sensor network · Updated hourly")
st.divider()

# Should you go outside
st.subheader("Should You Go Outside Today?")
st.caption("Based on current PM2.5 levels and India's National AQI standards.")

if not latest.empty:
    rec_cols = st.columns(5)
    for i, row in latest.iterrows():
        category, advice, color = get_recommendation(row['avg_pm25'])
        with rec_cols[i % 5]:
            st.markdown(f"""
                <div style="border: 1px solid {color}; border-radius: 8px; padding: 12px; margin-bottom: 8px;">
                    <div style="color: {color}; font-weight: bold; font-size: 14px;">{row['city']}</div>
                    <div style="color: {color}; font-size: 20px; font-weight: bold; margin: 4px 0;">{category}</div>
                    <div style="color: #9ca3af; font-size: 12px;">{row['avg_pm25']} µg/m³</div>
                    <div style="color: #d1d5db; font-size: 12px; margin-top: 8px;">{advice}</div>
                </div>
            """, unsafe_allow_html=True)

st.divider()

# Latest readings
st.subheader("Latest Readings")
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
        yaxis_range=[0, clean_df["avg_pm25"].max() * 1.1],
        legend_title="City",
        hovermode="x unified"
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Select at least one city.")

st.divider()

# City ranking
st.subheader("City Rankings — Average PM2.5")
ranking = clean_df.groupby("city")["avg_pm25"].mean().round(2).sort_values(ascending=False).reset_index()
ranking.columns = ["City", "Average PM2.5 (µg/m³)"]
ranking["Verdict"] = ranking["Average PM2.5 (µg/m³)"].apply(
    lambda x: "Good" if x <= 30 else
              "Satisfactory" if x <= 60 else
              "Moderate" if x <= 90 else
              "Poor" if x <= 120 else "Very Poor"
)
ranking.index = ranking.index + 1
st.dataframe(ranking, use_container_width=True)

st.divider()

# Weather correlation
st.subheader("Weather — Pollution Correlation")
st.caption("Does wind speed or humidity correlate with cleaner or more polluted air? Joined daily from OpenWeather + OpenAQ.")

if not corr_df.empty:
    pattern_counts = corr_df['weather_pollution_pattern'].value_counts().reset_index()
    pattern_counts.columns = ['Pattern', 'Count']

    col1, col2 = st.columns([1, 2])

    with col1:
        st.markdown("**Observed Patterns**")
        st.dataframe(pattern_counts, use_container_width=True, hide_index=True)

    with col2:
        fig2 = px.scatter(
            corr_df,
            x="avg_wind_speed",
            y="avg_pm25",
            color="city",
            size="avg_humidity",
            hover_data=["reading_date", "weather_pollution_pattern"],
            labels={
                "avg_wind_speed": "Wind Speed (m/s)",
                "avg_pm25": "PM2.5 (µg/m³)",
                "avg_humidity": "Humidity (%)",
                "city": "City"
            },
            title="Wind Speed vs PM2.5 — bubble size = humidity"
        )
        fig2.update_layout(
            height=350,
            margin=dict(t=40, b=20),
        )
        st.plotly_chart(fig2, use_container_width=True)
else:
    st.info("Correlation data loading — both pipelines running since 18 July.")

st.divider()

# Raw data
st.subheader("Raw Data")
show_flagged = st.checkbox("Include flagged sensor readings", value=False)
display_df = df if show_flagged else clean_df
st.dataframe(
    display_df.sort_values(["reading_date", "city"], ascending=[False, True]),
    use_container_width=True
)

st.divider()
st.caption("Built by Abhijeet Sirohi · B.Tech CSE-AIDE · AirWatch v1.0 · Data: OpenAQ (government sensors) + OpenWeather")