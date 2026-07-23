import os
import psycopg2
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from dotenv import load_dotenv
import numpy as np
from sklearn.linear_model import LinearRegression

load_dotenv()

st.set_page_config(
    page_title="AirWatch — India Air Quality",
    layout="wide"
)

# Custom theme — white with green and orange accents
st.markdown("""
<style>
    .stApp {
        background-color: #ffffff;
        color: #111827;
    }
    .stMetric {
        background-color: #f9fafb;
        border: 1px solid #e5e7eb;
        border-radius: 10px;
        padding: 16px;
    }
    .stMetricLabel {
        color: #6b7280 !important;
        font-size: 13px !important;
    }
    .stMetricValue {
        color: #111827 !important;
        font-size: 28px !important;
        font-weight: 700 !important;
    }
    h1 {
        color: #111827 !important;
        font-size: 32px !important;
        font-weight: 800 !important;
        border-left: 5px solid #16a34a;
        padding-left: 12px;
    }
    h2, h3 {
        color: #111827 !important;
        font-weight: 700 !important;
    }
    .section-header {
        background: linear-gradient(90deg, #f0fdf4, #fff7ed);
        border-left: 4px solid #16a34a;
        padding: 10px 16px;
        border-radius: 6px;
        margin-bottom: 16px;
    }
    .stDataFrame {
        border: 1px solid #e5e7eb;
        border-radius: 8px;
    }
    [data-testid="stSidebar"] {
        background-color: #f9fafb;
    }
    .stSelectbox, .stMultiSelect {
        background-color: #f9fafb;
    }
    hr {
        border-color: #e5e7eb !important;
    }
    .stCaption {
        color: #6b7280 !important;
    }
    .forecast-card {
        background: linear-gradient(135deg, #f0fdf4, #fff7ed);
        border: 1px solid #d1fae5;
        border-radius: 10px;
        padding: 16px;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# ── Data loading ──────────────────────────────────────────────────────────────

@st.cache_data(ttl=1800)
def load_data():
    try:
        db_url = st.secrets.get("SUPABASE_DB_URL") or os.getenv("SUPABASE_DB_URL")
        conn = psycopg2.connect(db_url)
        df = pd.read_sql("""
            SELECT city, reading_date, avg_pm25, max_pm25,
                   num_readings, likely_sensor_error
            FROM mart_city_pollution_trends
            WHERE reading_date >= '2026-06-01'
            ORDER BY city, reading_date
        """, conn)
        conn.close()
        df['reading_date'] = pd.to_datetime(df['reading_date'])
        return df
    except Exception as e:
        st.warning(f"Using sample data — {e}")
        return pd.DataFrame({
            'city': ['Delhi','Mumbai','Bengaluru','Kolkata','Chennai'] * 3,
            'reading_date': pd.to_datetime(['2026-06-25','2026-07-10','2026-07-23'] * 5),
            'avg_pm25': [53,44,47,26,8,26,21.6,33,21,65.1,65.1,65.1,16,23,34],
            'max_pm25': [53,44,47,26,8,26,21.6,33,21,65.1,65.1,65.1,16,23,34],
            'num_readings': [1,3,2]*5,
            'likely_sensor_error': [False]*15
        })

@st.cache_data(ttl=1800)
def load_correlation():
    try:
        db_url = st.secrets.get("SUPABASE_DB_URL") or os.getenv("SUPABASE_DB_URL")
        conn = psycopg2.connect(db_url)
        df = pd.read_sql("""
            SELECT city, reading_date, avg_pm25, avg_temp,
                   avg_humidity, avg_wind_speed, weather_pollution_pattern
            FROM mart_pollution_weather_correlation
            ORDER BY city, reading_date
        """, conn)
        conn.close()
        df['reading_date'] = pd.to_datetime(df['reading_date'])
        return df
    except:
        return pd.DataFrame()

def get_recommendation(pm25):
    if pm25 <= 30:
        return "Good", "Safe for all outdoor activities.", "#16a34a"
    elif pm25 <= 60:
        return "Satisfactory", "Sensitive individuals should limit prolonged exertion.", "#65a30d"
    elif pm25 <= 90:
        return "Moderate", "Children and elderly should avoid outdoor exertion.", "#d97706"
    elif pm25 <= 120:
        return "Poor", "Reduce outdoor activities. Wear a mask.", "#ea580c"
    elif pm25 <= 250:
        return "Very Poor", "Avoid going outside. Keep windows closed.", "#dc2626"
    else:
        return "Severe", "Health emergency. Do not go outside.", "#7c3aed"

def forecast_tomorrow(city_df):
    city_df = city_df.sort_values("reading_date").copy()
    city_df["day_num"] = (city_df["reading_date"] - city_df["reading_date"].min()).dt.days
    if len(city_df) < 3:
        return None
    X = city_df["day_num"].values.reshape(-1, 1)
    y = city_df["avg_pm25"].values
    model = LinearRegression()
    model.fit(X, y)
    next_day = city_df["day_num"].max() + 1
    prediction = model.predict([[next_day]])[0]
    return max(0, round(prediction, 2))

# ── Load data ─────────────────────────────────────────────────────────────────

df = load_data()
clean_df = df[df["likely_sensor_error"] == False]
corr_df = load_correlation()
latest = clean_df.sort_values("reading_date").groupby("city").last().reset_index()

# ── Header ────────────────────────────────────────────────────────────────────

st.title("AirWatch — India Air Quality Monitor")
st.caption("Real-time PM2.5 tracking across 5 major Indian cities · OpenAQ government sensors + OpenWeather · Updated hourly")
st.divider()

# ── Section 1: Should You Go Outside ─────────────────────────────────────────

st.markdown('<div class="section-header"><b>01 — Should You Go Outside Today?</b><br><span style="color:#6b7280;font-size:13px;">Based on current PM2.5 levels and India\'s National AQI standards</span></div>', unsafe_allow_html=True)

if not latest.empty:
    rec_cols = st.columns(5)
    for i, row in latest.iterrows():
        category, advice, color = get_recommendation(row['avg_pm25'])
        with rec_cols[i % 5]:
            st.markdown(f"""
                <div style="border:2px solid {color};border-radius:10px;padding:14px;text-align:center;background:#fafafa;">
                    <div style="font-weight:700;font-size:15px;color:#374151;">{row['city']}</div>
                    <div style="color:{color};font-size:22px;font-weight:800;margin:6px 0;">{category}</div>
                    <div style="color:#6b7280;font-size:13px;font-weight:600;">{row['avg_pm25']} µg/m³</div>
                    <div style="color:#9ca3af;font-size:12px;margin-top:8px;line-height:1.4;">{advice}</div>
                </div>
            """, unsafe_allow_html=True)

st.divider()

# ── Section 2: PM2.5 Trends ───────────────────────────────────────────────────

st.markdown('<div class="section-header"><b>02 — PM2.5 Pollution Trends</b><br><span style="color:#6b7280;font-size:13px;">Daily average PM2.5 levels since 25 June 2026</span></div>', unsafe_allow_html=True)

cities = sorted(clean_df["city"].unique().tolist())
selected_cities = st.multiselect("Select cities", options=cities, default=cities)
filtered = clean_df[clean_df["city"].isin(selected_cities)]

if not filtered.empty:
    fig = px.line(
        filtered,
        x="reading_date",
        y="avg_pm25",
        color="city",
        markers=True,
        color_discrete_map={
            "Delhi": "#ea580c",
            "Mumbai": "#16a34a",
            "Bengaluru": "#0284c7",
            "Kolkata": "#7c3aed",
            "Chennai": "#d97706"
        },
        labels={"reading_date": "Date", "avg_pm25": "PM2.5 (µg/m³)", "city": "City"}
    )
    fig.add_hline(
        y=15, line_dash="dot", line_color="#9ca3af",
        annotation_text="WHO 24hr guideline — 15 µg/m³",
        annotation_position="top left",
        annotation_font_color="#9ca3af"
    )
    fig.update_layout(
        height=420,
        plot_bgcolor="#ffffff",
        paper_bgcolor="#ffffff",
        font_color="#111827",
        xaxis=dict(showgrid=True, gridcolor="#f3f4f6", title="Date"),
        yaxis=dict(showgrid=True, gridcolor="#f3f4f6",
                   title="PM2.5 (µg/m³)", range=[0, clean_df["avg_pm25"].max() * 1.15]),
        legend_title="City",
        hovermode="x unified",
        margin=dict(t=20, b=20)
    )
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# ── Section 3: Tomorrow's Forecast ────────────────────────────────────────────

st.markdown('<div class="section-header"><b>03 — Next-Day PM2.5 Forecast</b><br><span style="color:#6b7280;font-size:13px;">Linear trend forecast based on historical readings · Early model, accuracy improves with more data</span></div>', unsafe_allow_html=True)

forecast_cols = st.columns(5)
for i, city in enumerate(sorted(clean_df["city"].unique())):
    city_data = clean_df[clean_df["city"] == city]
    prediction = forecast_tomorrow(city_data)
    if prediction is not None:
        category, _, color = get_recommendation(prediction)
        with forecast_cols[i % 5]:
            st.markdown(f"""
                <div class="forecast-card">
                    <div style="font-weight:700;font-size:14px;color:#374151;">{city}</div>
                    <div style="font-size:11px;color:#9ca3af;margin:2px 0;">Tomorrow's forecast</div>
                    <div style="color:{color};font-size:26px;font-weight:800;margin:6px 0;">{prediction}</div>
                    <div style="color:#6b7280;font-size:12px;">µg/m³ · {category}</div>
                </div>
            """, unsafe_allow_html=True)

st.caption("Forecast uses linear regression on daily PM2.5 trend. Statistical significance improves as more data accumulates.")

st.divider()

# ── Section 4: City Rankings ──────────────────────────────────────────────────

st.markdown('<div class="section-header"><b>04 — City Rankings</b><br><span style="color:#6b7280;font-size:13px;">Ranked by average PM2.5 across the full tracking period</span></div>', unsafe_allow_html=True)

ranking = clean_df.groupby("city")["avg_pm25"].mean().round(2).sort_values(ascending=False).reset_index()
ranking.columns = ["City", "Average PM2.5 (µg/m³)"]
ranking["AQI Category"] = ranking["Average PM2.5 (µg/m³)"].apply(
    lambda x: "Good" if x <= 30 else
              "Satisfactory" if x <= 60 else
              "Moderate" if x <= 90 else
              "Poor" if x <= 120 else "Very Poor"
)
ranking["Safe to Exercise?"] = ranking["Average PM2.5 (µg/m³)"].apply(
    lambda x: "Yes" if x <= 60 else "With caution" if x <= 90 else "No"
)
ranking.index = ranking.index + 1
st.dataframe(ranking, use_container_width=True)

st.divider()

# ── Section 5: Weather Correlation ────────────────────────────────────────────

st.markdown('<div class="section-header"><b>05 — Weather — Pollution Correlation</b><br><span style="color:#6b7280;font-size:13px;">Does wind speed or humidity explain PM2.5 levels? OpenAQ + OpenWeather joined by city and date</span></div>', unsafe_allow_html=True)

if not corr_df.empty:
    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown("**Observed Patterns**")
        pattern_counts = corr_df['weather_pollution_pattern'].value_counts().reset_index()
        pattern_counts.columns = ['Pattern', 'Days Observed']
        st.dataframe(pattern_counts, use_container_width=True, hide_index=True)

    with col2:
        fig2 = px.scatter(
            corr_df,
            x="avg_wind_speed",
            y="avg_pm25",
            color="city",
            size="avg_humidity",
            hover_data=["reading_date", "weather_pollution_pattern", "avg_temp"],
            color_discrete_map={
                "Delhi": "#ea580c",
                "Mumbai": "#16a34a",
                "Bengaluru": "#0284c7",
                "Kolkata": "#7c3aed",
                "Chennai": "#d97706"
            },
            labels={
                "avg_wind_speed": "Wind Speed (m/s)",
                "avg_pm25": "PM2.5 (µg/m³)",
                "avg_humidity": "Humidity (%)",
                "city": "City"
            },
            title="Wind Speed vs PM2.5 (bubble size = humidity)"
        )
        fig2.update_layout(
            height=350,
            plot_bgcolor="#ffffff",
            paper_bgcolor="#ffffff",
            font_color="#111827",
            xaxis=dict(showgrid=True, gridcolor="#f3f4f6"),
            yaxis=dict(showgrid=True, gridcolor="#f3f4f6"),
            margin=dict(t=40, b=20)
        )
        st.plotly_chart(fig2, use_container_width=True)
else:
    st.info("Correlation data loading — pipelines running since 18 July.")

st.divider()

# ── Section 6: Raw Data ───────────────────────────────────────────────────────

st.markdown('<div class="section-header"><b>06 — Raw Data</b><br><span style="color:#6b7280;font-size:13px;">Full dataset — toggle to include sensor-flagged readings</span></div>', unsafe_allow_html=True)

show_flagged = st.checkbox("Include flagged sensor readings", value=False)
display_df = df if show_flagged else clean_df
st.dataframe(
    display_df.sort_values(["reading_date", "city"], ascending=[False, True]),
    use_container_width=True
)

st.divider()
st.caption("Built by Abhijeet Sirohi · B.Tech CSE-AIDE · 2nd Year Internship · Data: OpenAQ (government sensors) + OpenWeather · AirWatch v1.0")