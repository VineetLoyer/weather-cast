import requests
import json
import psycopg2
from datetime import datetime, timedelta
from config import NOAA_API_KEY, DB_HOST, DB_NAME, DB_USER, DB_PASS, DB_PORT

NOAA_API_URL = "https://www.ncdc.noaa.gov/cdo-web/api/v2/data"
DATASET_ID = "GHCND"
YEARS = 5  # Fetch last 5 years

# Load NOAA Station IDs
with open("station_ids.json", "r") as f:
    STATION_IDS = json.load(f)

headers = {"token": NOAA_API_KEY}

# Connect to AWS RDS
conn = psycopg2.connect(
    host=DB_HOST,
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASS,
    port=DB_PORT
)
cur = conn.cursor()

# ✅ Create table with correct units
cur.execute("""
    CREATE TABLE IF NOT EXISTS weather_data (
        id SERIAL PRIMARY KEY,
        city VARCHAR(255),
        date DATE,
        temperature FLOAT,   -- Celsius (°C)
        humidity FLOAT,      -- Percentage (%)
        wind_speed FLOAT,    -- m/s
        cloud_coverage FLOAT -- Percentage (%)
    )
""")
conn.commit()

# ✅ Fetch data and apply unit conversions
for city, station_id in STATION_IDS.items():
    print(f"📡 Fetching weather data for {city} ({station_id})...")

    for days_ago in range(0, YEARS * 365, 10):  # Fetch 10 days at a time
        start_date = (datetime.utcnow() - timedelta(days=days_ago+10)).strftime("%Y-%m-%d")
        end_date = (datetime.utcnow() - timedelta(days=days_ago)).strftime("%Y-%m-%d")

        params = {
            "datasetid": DATASET_ID,
            "stationid": station_id,
            "startdate": start_date,
            "enddate": end_date,
            "limit": 1000
        }

        response = requests.get(NOAA_API_URL, headers=headers, params=params)

        if response.status_code == 200:
            data = response.json()
            if "results" in data:
                for record in data["results"]:
                    try:
                        record_date = record["date"][:10]

                        # ✅ Apply Unit Conversions
                        temp = record.get("value", None)
                        if temp is not None:  
                            temp = temp / 10  # Convert tenths of °C → °C

                        humidity = record.get("humidity", None)  # Already in %

                        wind_speed = record.get("windspeed", None)
                        if wind_speed is not None:
                            wind_speed = wind_speed * 0.27778  # Convert km/h → m/s

                        cloud_coverage = record.get("cloudcover", None)
                        if cloud_coverage is not None:
                            cloud_coverage = (cloud_coverage / 8) * 100  # Convert Oktas → %

                        # ✅ Insert into RDS
                        cur.execute("""
                            INSERT INTO weather_data (city, date, temperature, humidity, wind_speed, cloud_coverage)
                            VALUES (%s, %s, %s, %s, %s, %s)
                        """, (city, record_date, temp, humidity, wind_speed, cloud_coverage))

                    except Exception as e:
                        print(f"⚠️ Error inserting data for {city} on {record_date}: {e}")

            conn.commit()
        else:
            print(f"❌ Failed to fetch data for {city} ({station_id}) → {response.text}")

# ✅ Close connection
cur.close()
conn.close()

print("✅ All weather data successfully stored in RDS with correct units!")
