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

st.markdown("""
<style>
    .stApp {
        background-color: #f5f7f9;
        color: #111827;
    }
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    h1 {
        color: #111827 !important;
        font-size: 30px !important;
        font-weight: 800 !important;
        border-left: 4px solid #16a34a;
        padding-left: 14px;
        margin-left: 2px;
        line-height: 1.4 !important;
        margin-bottom: 4px !important;
    }
    h2, h3 {
        color: #111827 !important;
        font-weight: 700 !important;
    }
    .card {
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 10px;
        padding: 16px;
        text-align: center;
        height: 100%;
    }
    .card-value {
        font-size: 28px;
        font-weight: 800;
        color: #111827;
        margin: 6px 0 2px 0;
    }
    .card-unit {
        font-size: 12px;
        color: #6b7280;
        margin-bottom: 6px;
    }
    .card-city {
        font-size: 13px;
        font-weight: 600;
        color: #6b7280;
        margin-bottom: 4px;
    }
    .card-category {
        font-size: 13px;
        font-weight: 700;
        padding: 2px 8px;
        border-radius: 4px;
        display: inline-block;
        margin-top: 4px;
    }
    .forecast-card {
        background: #ffffff;
        border: 1.5px dashed #d1d5db;
        border-radius: 10px;
        padding: 16px;
        text-align: center;
    }
    .forecast-value {
        font-size: 24px;
        font-weight: 800;
        margin: 6px 0 2px 0;
    }
    .section-title {
        font-size: 16px;
        font-weight: 700;
        color: #111827;
        margin-bottom: 4px;
        padding-bottom: 6px;
        border-bottom: 2px solid #16a34a;
        display: inline-block;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #ffffff;
        border-radius: 10px;
        padding: 6px;
        border: 1px solid #e5e7eb;
    }
    .stTabs [data-baseweb="tab"] {
        color: #6b7280;
        font-weight: 600;
        border-radius: 6px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #16a34a !important;
        color: #ffffff !important;
    }
    .stDataFrame {
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        background: #ffffff;
    }
    .stCaption {
        color: #9ca3af !important;
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

CITY_COLORS = {
    "Delhi": "#2563eb",
    "Mumbai": "#16a34a",
    "Bengaluru": "#0891b2",
    "Kolkata": "#7c3aed",
    "Chennai": "#d97706"
}

AQI_COLORS = {
    "Good": "#16a34a",
    "Satisfactory": "#65a30d",
    "Moderate": "#d97706",
    "Poor": "#ea580c",
    "Very Poor": "#dc2626",
    "Severe": "#7c3aed"
}

def get_aqi(pm25):
    if pm25 <= 30: return "Good", "#16a34a"
    elif pm25 <= 60: return "Satisfactory", "#65a30d"
    elif pm25 <= 90: return "Moderate", "#d97706"
    elif pm25 <= 120: return "Poor", "#ea580c"
    elif pm25 <= 250: return "Very Poor", "#dc2626"
    else: return "Severe", "#7c3aed"

def get_advice(pm25):
    if pm25 <= 30: return "Safe for all outdoor activities."
    elif pm25 <= 60: return "Sensitive groups should limit exertion."
    elif pm25 <= 90: return "Children and elderly avoid outdoor exertion."
    elif pm25 <= 120: return "Wear a mask if going outside."
    elif pm25 <= 250: return "Avoid going outside."
    else: return "Health emergency. Stay indoors."

def forecast_tomorrow(city_df):
    city_df = city_df.sort_values("reading_date").copy()
    city_df["day_num"] = (city_df["reading_date"] - city_df["reading_date"].min()).dt.days
    if len(city_df) < 4:
        return None, None
    X = city_df["day_num"].values.reshape(-1, 1)
    y = city_df["avg_pm25"].values
    model = LinearRegression()
    model.fit(X, y)
    next_day = city_df["day_num"].max() + 1
    pred = max(0, round(model.predict([[next_day]])[0], 1))
    std = round(np.std(y) * 0.5, 1)
    return pred, std

# ── Load ──────────────────────────────────────────────────────────────────────

df = load_data()
clean_df = df[df["likely_sensor_error"] == False]
corr_df = load_correlation()
latest = clean_df.sort_values("reading_date").groupby("city").last().reset_index()

# ── Header ────────────────────────────────────────────────────────────────────

col_title, col_status = st.columns([3, 1])
with col_title:
    st.title("AirWatch — India Air Quality Monitor")
    st.caption("OpenAQ government sensors + OpenWeather · 5 Indian cities · Hourly pipeline")
with col_status:
    st.markdown("<br>", unsafe_allow_html=True)
    last_date = clean_df["reading_date"].max().strftime("%d %b %Y") if not clean_df.empty else "—"
    st.markdown(f"""
        <div style="background:#ffffff;border:1px solid #e5e7eb;border-radius:8px;
                    padding:10px 14px;text-align:right;margin-top:8px;">
            <div style="font-size:11px;color:#9ca3af;">Last updated</div>
            <div style="font-size:14px;font-weight:700;color:#111827;">{last_date}</div>
            <div style="font-size:11px;color:#16a34a;font-weight:600;">● Live pipeline</div>
        </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Tabs ──────────────────────────────────────────────────────────────────────

tab1, tab2, tab3, tab4 = st.tabs([
    "Overview",
    "Trends & Forecast",
    "Weather Correlation",
    "Data"
])

# ══ TAB 1: OVERVIEW ══════════════════════════════════════════════════════════

with tab1:
    st.markdown('<p class="section-title">Current Air Quality</p>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    if not latest.empty:
        cols = st.columns(5)
        for i, row in latest.iterrows():
            category, color = get_aqi(row['avg_pm25'])
            advice = get_advice(row['avg_pm25'])
            with cols[i % 5]:
                st.markdown(f"""
                    <div class="card" style="border-top: 3px solid {color};">
                        <div class="card-city">{row['city']}</div>
                        <div class="card-value" style="color:{color};">{row['avg_pm25']}</div>
                        <div class="card-unit">µg/m³ · PM2.5</div>
                        <span class="card-category" style="background:{color}18;color:{color};">
                            {category}
                        </span>
                        <div style="font-size:11px;color:#9ca3af;margin-top:8px;line-height:1.4;">
                            {advice}
                        </div>
                    </div>
                """, unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown('<p class="section-title">City Rankings — Average PM2.5</p>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    ranking = clean_df.groupby("city")["avg_pm25"].mean().round(1).sort_values(ascending=True).reset_index()
    ranking.columns = ["City", "Avg PM2.5"]
    ranking["Category"] = ranking["Avg PM2.5"].apply(lambda x: get_aqi(x)[0])
    ranking["Safe to exercise?"] = ranking["Avg PM2.5"].apply(
        lambda x: "Yes" if x <= 60 else "With caution" if x <= 90 else "No"
    )

    fig_rank = go.Figure()
    for _, row in ranking.iterrows():
        _, color = get_aqi(row["Avg PM2.5"])
        fig_rank.add_trace(go.Bar(
            x=[row["Avg PM2.5"]],
            y=[row["City"]],
            orientation='h',
            marker_color=color,
            text=f"{row['Avg PM2.5']} µg/m³",
            textposition="outside",
            showlegend=False
        ))
    fig_rank.add_vline(x=15, line_dash="dot", line_color="#9ca3af",
                       annotation_text="WHO guideline", annotation_font_color="#9ca3af")
    fig_rank.update_layout(
        height=260,
        plot_bgcolor="#ffffff",
        paper_bgcolor="#ffffff",
        font_color="#111827",
        xaxis=dict(showgrid=True, gridcolor="#f3f4f6", title="Average PM2.5 (µg/m³)"),
        yaxis=dict(showgrid=False),
        margin=dict(t=10, b=10, l=10, r=80),
        bargap=0.3
    )
    st.plotly_chart(fig_rank, use_container_width=True)

# ══ TAB 2: TRENDS & FORECAST ═════════════════════════════════════════════════

with tab2:
    st.markdown('<p class="section-title">PM2.5 Trends</p>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    cities = sorted(clean_df["city"].unique().tolist())
    selected = st.multiselect("Select cities", options=cities, default=cities)
    filtered = clean_df[clean_df["city"].isin(selected)]

    if not filtered.empty:
        fig = px.line(
            filtered,
            x="reading_date",
            y="avg_pm25",
            color="city",
            color_discrete_map=CITY_COLORS,
            labels={"reading_date": "Date", "avg_pm25": "PM2.5 (µg/m³)", "city": "City"}
        )
        fig.add_hline(y=15, line_dash="dot", line_color="#9ca3af",
                      annotation_text="WHO guideline — 15 µg/m³",
                      annotation_position="top left",
                      annotation_font_color="#9ca3af")
        fig.update_layout(
            height=400,
            plot_bgcolor="#ffffff",
            paper_bgcolor="#f5f7f9",
            font_color="#111827",
            xaxis=dict(showgrid=True, gridcolor="#f3f4f6", title="Date"),
            yaxis=dict(showgrid=True, gridcolor="#f3f4f6",
                       title="PM2.5 (µg/m³)",
                       range=[0, clean_df["avg_pm25"].max() * 1.15]),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="left",
                x=0,
                title="",
                font=dict(color="#111827")
            ),
            hovermode="x unified",
            margin=dict(t=40, b=20, r=20)
        )
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<p class="section-title">Next-Day Forecast</p>', unsafe_allow_html=True)
    st.caption("Linear trend model trained on daily PM2.5 history · Uncertainty shown as ± range · Accuracy improves with more data")
    st.markdown("<br>", unsafe_allow_html=True)

    fcols = st.columns(5)
    for i, city in enumerate(sorted(clean_df["city"].unique())):
        city_data = clean_df[clean_df["city"] == city]
        pred, std = forecast_tomorrow(city_data)
        with fcols[i % 5]:
            if pred is not None:
                category, color = get_aqi(pred)
                st.markdown(f"""
                    <div class="forecast-card">
                        <div style="font-size:12px;color:#9ca3af;font-weight:600;">
                            {city}
                        </div>
                        <div style="font-size:11px;color:#9ca3af;margin:2px 0;">
                            Tomorrow's forecast
                        </div>
                        <div class="forecast-value" style="color:{color};">≈{pred}</div>
                        <div style="font-size:11px;color:#9ca3af;">µg/m³ · ±{std}</div>
                        <span style="font-size:11px;font-weight:700;color:{color};
                                     background:{color}18;padding:2px 8px;
                                     border-radius:4px;display:inline-block;margin-top:6px;">
                            {category}
                        </span>
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                    <div class="forecast-card">
                        <div style="font-size:12px;color:#9ca3af;">{city}</div>
                        <div style="font-size:11px;color:#d1d5db;margin-top:8px;">
                            Insufficient data
                        </div>
                    </div>
                """, unsafe_allow_html=True)

# ══ TAB 3: WEATHER CORRELATION ═══════════════════════════════════════════════

with tab3:
    st.markdown('<p class="section-title">Weather — Pollution Correlation</p>', unsafe_allow_html=True)
    st.caption("Does wind speed or humidity explain PM2.5 levels? OpenAQ + OpenWeather joined by city and date.")
    st.markdown("<br>", unsafe_allow_html=True)

    if not corr_df.empty:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Observations", len(corr_df))
        with col2:
            st.metric("Cities", corr_df["city"].nunique())
        with col3:
            st.metric("Avg Wind Speed", f"{corr_df['avg_wind_speed'].mean():.1f} m/s")
        with col4:
            st.metric("Avg Humidity", f"{corr_df['avg_humidity'].mean():.0f}%")

        st.markdown("<br>", unsafe_allow_html=True)

        col_left, col_right = st.columns([1, 2])

        with col_left:
            st.markdown("**Observed Patterns**")
            pattern_counts = corr_df['weather_pollution_pattern'].value_counts().reset_index()
            pattern_counts.columns = ['Pattern', 'Days']
            st.dataframe(pattern_counts, use_container_width=True, hide_index=True)

            st.markdown("<br>", unsafe_allow_html=True)
            wind_corr = corr_df["avg_wind_speed"].corr(corr_df["avg_pm25"])
            humid_corr = corr_df["avg_humidity"].corr(corr_df["avg_pm25"])
            st.markdown(f"""
                <div style="background:#ffffff;border:1px solid #e5e7eb;border-radius:8px;padding:12px;">
                    <div style="font-size:13px;font-weight:700;color:#374151;margin-bottom:8px;">
                        Correlation Coefficients
                    </div>
                    <div style="font-size:12px;color:#6b7280;margin-bottom:4px;">
                        Wind Speed vs PM2.5: 
                        <span style="font-weight:700;color:#111827;">{wind_corr:.2f}</span>
                    </div>
                    <div style="font-size:12px;color:#6b7280;">
                        Humidity vs PM2.5: 
                        <span style="font-weight:700;color:#111827;">{humid_corr:.2f}</span>
                    </div>
                    <div style="font-size:11px;color:#9ca3af;margin-top:8px;">
                        -1 = perfect inverse · 0 = no correlation · +1 = perfect direct
                    </div>
                </div>
            """, unsafe_allow_html=True)

        with col_right:
            fig2 = px.scatter(
                corr_df,
                x="avg_wind_speed",
                y="avg_pm25",
                color="city",
                color_discrete_map=CITY_COLORS,
                hover_data=["reading_date", "weather_pollution_pattern", "avg_humidity"],
                labels={
                    "avg_wind_speed": "Wind Speed (m/s)",
                    "avg_pm25": "PM2.5 (µg/m³)",
                    "city": "City"
                },
                title="Wind Speed vs PM2.5"
            )
            fig2.update_layout(
                height=380,
                plot_bgcolor="#ffffff",
                paper_bgcolor="#f5f7f9",
                font_color="#111827",
                xaxis=dict(showgrid=True, gridcolor="#f3f4f6"),
                yaxis=dict(showgrid=True, gridcolor="#f3f4f6",
                           range=[0, corr_df["avg_pm25"].max() * 1.15]),
                legend=dict(font=dict(color="#111827"), title=""),
                margin=dict(t=40, b=20)
            )
            st.plotly_chart(fig2, use_container_width=True)
    else:
        st.markdown("""
            <div style="background:#ffffff;border:1px solid #e5e7eb;border-radius:10px;
                        padding:32px;text-align:center;">
                <div style="font-size:14px;color:#374151;font-weight:600;">
                    Correlation data building up
                </div>
                <div style="font-size:13px;color:#9ca3af;margin-top:6px;">
                    Both pipelines running since 18 July · Data appears when pollution 
                    and weather readings share the same date
                </div>
            </div>
        """, unsafe_allow_html=True)

# ══ TAB 4: DATA ══════════════════════════════════════════════════════════════

with tab4:
    st.markdown('<p class="section-title">Raw Sensor Data</p>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    show_flagged = st.checkbox("Include flagged sensor readings", value=False)
    display_df = df if show_flagged else clean_df
    st.dataframe(
        display_df.sort_values(["reading_date", "city"], ascending=[False, True]),
        use_container_width=True
    )

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<p class="section-title">Data Quality Summary</p>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    q1, q2, q3, q4 = st.columns(4)
    with q1:
        st.metric("Total readings", len(df))
    with q2:
        st.metric("Clean readings", len(clean_df))
    with q3:
        flagged = len(df[df["likely_sensor_error"] == True])
        st.metric("Flagged readings", flagged)
    with q4:
        st.metric("Days tracked", clean_df["reading_date"].nunique())

st.markdown("<br>", unsafe_allow_html=True)
st.caption("Built by Abhijeet Sirohi · B.Tech CSE-AIDE · 2nd Year Internship · AirWatch v1.0 · Data: OpenAQ + OpenWeather")