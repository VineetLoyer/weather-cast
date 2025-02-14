import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASS, APP_TITLE
import time

def init_connection():
    return create_engine(f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}")

def setup_page():
    st.set_page_config(page_title=APP_TITLE, layout="wide", initial_sidebar_state="expanded")
    
    # Theme Switching
    theme = st.sidebar.radio("🎨 Theme", ["Dark Mode", "Light Mode"])
    
    if theme == "Dark Mode":
        st.markdown("""
        <style>
            body { background-color: #0e1117; color: white; }
            .stApp { background-color: #0e1117; color: white; }
            h1, h2, h3, h4, h5, h6, p, label, div { color: white !important; }
        </style>
        """, unsafe_allow_html=True)
        return "plotly_dark"
    else:
        st.markdown("""
        <style>
            body { background-color: white; color: black; }
            .stApp { background-color: white; color: black; }
            h1, h2, h3, h4, h5, h6, p, label, div { color: black !important; }
        </style>
        """, unsafe_allow_html=True)
        return "plotly_white"

@st.cache_data(ttl=60)
def fetch_weather_data():
    try:
        engine = init_connection()
        query = """
            SELECT * FROM weather_data 
            WHERE date = CURRENT_DATE
            ORDER BY time DESC;
        """
        df = pd.read_sql(query, engine)
        return df
    except Exception as e:
        st.error(f"🚨 Database connection failed: {e}")
        return pd.DataFrame()

def create_weather_plots(city_data, selected_city, plotly_theme):
    fig = make_subplots(
        rows=3, cols=2,
        subplot_titles=[
            "Temperature (°C)", "Pressure (hPa)",
            "Humidity (%)", "Wind Speed (m/s)",
            "Cloud Cover (%)", ""
        ],
        specs=[[{}, {}], [{}, {}], [{}, None]],
        vertical_spacing=0.12
    )

    # Temperature
    fig.add_trace(
        go.Scatter(
            x=city_data["time"], 
            y=city_data["temperature"],
            mode="lines+markers",
            name="Temperature",
            line=dict(color="red")
        ),
        row=1, col=1
    )

    # Pressure
    fig.add_trace(
        go.Scatter(
            x=city_data["time"], 
            y=city_data["pressure"],
            mode="lines+markers",
            name="Pressure",
            line=dict(color="blue")
        ),
        row=1, col=2
    )

    # Humidity
    fig.add_trace(
        go.Scatter(
            x=city_data["time"], 
            y=city_data["humidity"],
            mode="lines+markers",
            name="Humidity",
            line=dict(color="green")
        ),
        row=2, col=1
    )

    # Wind Speed
    fig.add_trace(
        go.Scatter(
            x=city_data["time"], 
            y=city_data["wind_speed"],
            mode="lines+markers",
            name="Wind Speed",
            line=dict(color="purple")
        ),
        row=2, col=2
    )

    # Cloud Cover
    fig.add_trace(
        go.Scatter(
            x=city_data["time"], 
            y=city_data["cloud_cover"],
            mode="lines+markers",
            name="Cloud Cover",
            line=dict(color="gray")
        ),
        row=3, col=1
    )

    # Update layout
    fig.update_layout(
        height=800,
        title=f"Weather Trends for {selected_city}",
        template=plotly_theme,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    return fig

def display_metrics(latest_data, selected_city):
    st.subheader(f"Current Weather Conditions in {selected_city}")
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("🌡️ Temperature", f"{latest_data['temperature']:.1f}°C")
    col2.metric("🎈 Pressure", f"{latest_data['pressure']} hPa")
    col3.metric("💧 Humidity", f"{latest_data['humidity']}%")
    col4.metric("🌬️ Wind Speed", f"{latest_data['wind_speed']} m/s")
    col5.metric("☁️ Cloud Cover", f"{latest_data['cloud_cover']}%")

def main():
    plotly_theme = setup_page()
    st.title("🌎 WeatherCast: Real-time Weather Analytics Dashboard")

    # Load initial data
    df = fetch_weather_data()

    if not df.empty:
        # City Selection in sidebar
        cities = sorted(df["location"].unique())
        selected_city = st.sidebar.selectbox(
            "📍 Select City", 
            cities, 
            index=cities.index("San Jose") if "San Jose" in cities else 0
        )
        
        # Filter data for selected city
        city_data = df[df["location"] == selected_city].copy()
        
        if not city_data.empty:
            # Get latest readings
            latest_data = city_data.iloc[0]
            
            # Display current conditions
            display_metrics(latest_data, selected_city)

            # Create and display plots
            fig = create_weather_plots(city_data, selected_city, plotly_theme)
            st.plotly_chart(fig, use_container_width=True)
            
            # Add refresh button
            if st.sidebar.button("🔄 Refresh Data"):
                st.cache_data.clear()
                st.empty()
            
            # Display last update time
            st.sidebar.write(f"Last Updated: {latest_data['date']} {latest_data['time']}")

    else:
        st.warning("⚠️ No data available. Please check the database connection.")

if __name__ == "__main__":
    main()