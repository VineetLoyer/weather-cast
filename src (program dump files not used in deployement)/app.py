import streamlit as st
import pandas as pd
import psycopg2
import os
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from sqlalchemy import create_engine
from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASS, REFRESH_INTERVAL, APP_TITLE, PROCESSED_DIR

st.set_page_config(page_title=APP_TITLE, layout="wide", initial_sidebar_state="expanded")

# ✅ Apply Theme Switching
theme = st.sidebar.radio("🎨 Theme", ["Dark Mode", "Light Mode"])

# ✅ Custom CSS for Dark/Light Mode
if theme == "Dark Mode":
    dark_mode_css = """
    <style>
        body { background-color: #0e1117; color: white; }
        .stApp { background-color: #0e1117; color: white; }
        h1, h2, h3, h4, h5, h6, p, label, div { color: white !important; }
    </style>
    """
    plotly_theme = "plotly_dark"
else:
    light_mode_css = """
    <style>
        body { background-color: white; color: black; }
        .stApp { background-color: white; color: black; }
        h1, h2, h3, h4, h5, h6, p, label, div { color: black !important; }
    </style>
    """
    plotly_theme = "plotly_white"

st.markdown(dark_mode_css if theme == "Dark Mode" else light_mode_css, unsafe_allow_html=True)

# ✅ Connect to RDS using SQLAlchemy
@st.cache_data(ttl=REFRESH_INTERVAL)
def fetch_weather_data():
    try:
        engine = create_engine(f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}")
        query = "SELECT * FROM weather_summary ORDER BY date DESC LIMIT 100;"
        df = pd.read_sql(query, engine)
        return df
    except Exception as e:
        st.error(f"🚨 Database connection failed: {e}")
        return pd.DataFrame()

df = fetch_weather_data()

# ✅ Load Forecast Data
def load_forecast_data(city):
    forecast_file = os.path.join(PROCESSED_DIR, f"{city}_forecast.csv")
    if os.path.exists(forecast_file):
        return pd.read_csv(forecast_file)
    return None

# ✅ UI Layout
st.title("🌎 WeatherCast: Real-time Weather Analytics Dashboard")

# 🚨 Check if data is available
if not df.empty:
    cities = df["location"].unique()
    selected_city = st.sidebar.selectbox("📍 Select City", cities)
    city_data = df[df["location"] == selected_city]
    forecast_data = load_forecast_data(selected_city)

    # ✅ Create Subplots
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=[
            f"🌡️ Temperature Trend in {selected_city} (Historical & Forecast)",
            f"💧 Humidity Trend in {selected_city}",
            f"🌬️ Wind Speed Trend in {selected_city}",
            f"☁️ Cloud Cover Trend in {selected_city}"
        ]
    )

    # ✅ Temperature Trend with Forecast
    fig.add_trace(
        go.Scatter(
            x=city_data["date"], y=city_data["avg_temp"],
            mode="lines+markers", name="Actual Temperature", line=dict(color="blue")
        ),
        row=1, col=1
    )
    if forecast_data is not None:
        fig.add_trace(
            go.Scatter(
                x=forecast_data["date"], y=forecast_data["forecast_temp"],
                mode="lines", name="Forecast Temperature", line=dict(dash="dot", color="red")
            ),
            row=1, col=1
        )

    # ✅ Humidity Trend
    fig.add_trace(
        go.Scatter(x=city_data["date"], y=city_data["avg_humidity"], mode="lines+markers", name="Humidity"),
        row=1, col=2
    )

    # ✅ Wind Speed Trend
    fig.add_trace(
        go.Scatter(x=city_data["date"], y=city_data["avg_wind_speed"], mode="lines+markers", name="Wind Speed"),
        row=2, col=1
    )

    # ✅ Cloud Cover Trend
    fig.add_trace(
        go.Scatter(x=city_data["date"], y=city_data["avg_cloud_coverage"], mode="lines+markers", name="Cloud Cover"),
        row=2, col=2
    )

    # ✅ Apply Theme & Layout
    fig.update_layout(
        title=f"Weather Trends for {selected_city}",
        template=plotly_theme,
        height=700
    )

    st.plotly_chart(fig, use_container_width=True)

    # ✅ Show Latest Data
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🌡️ Avg Temp", f"{city_data['avg_temp'].iloc[-1]:.2f}°C")
    col2.metric("💧 Avg Humidity", f"{city_data['avg_humidity'].iloc[-1]:.1f}%")
    col3.metric("🌬️ Avg Wind Speed", f"{city_data['avg_wind_speed'].iloc[-1]:.2f} km/h")
    col4.metric("☁️ Avg Cloud Cover", f"{city_data['avg_cloud_coverage'].iloc[-1]:.1f}%")

    # ✅ Display Forecast Data (if available)
    if forecast_data is not None:
        st.subheader(f"🔮 Next 30-Day Forecast for {selected_city}")
        st.dataframe(forecast_data)

    st.write(f"🔄 Auto-refreshing every {REFRESH_INTERVAL // 60} minutes...")
    st.sidebar.button("🔄 Refresh Now", on_click=lambda: st.cache_data.clear())

else:
    st.warning("⚠️ No data available. Please check the database connection.")
