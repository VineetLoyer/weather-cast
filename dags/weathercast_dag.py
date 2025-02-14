import os
import json
import requests
import boto3
import psycopg2
from datetime import datetime, timezone
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago
from config import (
    BASE_URL, OPENWEATHER_API_KEY,
    AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION, AWS_S3_BUCKET,
    DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASS,
    DATASET_DIR, BASE_DIR
)

# 🔹 Constants
DATA_DIR = "/opt/airflow/dataset/raw"
LOCATIONS = ["Los Angeles", "New York", "Chicago", "Houston", "Phoenix","Philadelphia", "San Antonio", "San Diego", "Dallas", "San Jose"]
KELVIN_TO_CELSIUS = 273.15

def ensure_directories(city):
    """Create necessary directories for data storage"""
    city_dir = os.path.join(DATA_DIR, city.replace(" ", "_"))
    os.makedirs(city_dir, exist_ok=True)
    return city_dir

# 🔹 Initialize S3 Client
s3_client = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION
)

# 🔹 PostgreSQL Connection
def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )

# 🔹 Create Weather Table
def create_table():
    query = """
        CREATE TABLE IF NOT EXISTS weather_data (
            id SERIAL PRIMARY KEY,
            location VARCHAR(255),
            temperature FLOAT,
            pressure FLOAT,
            humidity FLOAT,
            wind_speed FLOAT,
            cloud_cover INT,
            date DATE,
            time TIME,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(query)
        conn.commit()
        cur.close()
        conn.close()
        print("✅ Checked and created 'weather_data' table.")
    except Exception as e:
        print(f"❌ Error creating table: {e}")

# 🔹 Fetch Weather Data
def fetch_weather_data():
    current_datetime = datetime.now(timezone.utc)
    # Round to nearest 15 minutes
    current_datetime = current_datetime.replace(
        minute=(current_datetime.minute // 15) * 15,
        second=0,
        microsecond=0
    )
    current_date = current_datetime.strftime("%Y-%m-%d")
    current_time = current_datetime.strftime("%H-%M")
    
    try:
        for city in LOCATIONS:
            try:
                city_dir = ensure_directories(city)
                
                response = requests.get(
                    BASE_URL,
                    params={
                        "q": city,
                        "appid": OPENWEATHER_API_KEY
                    },
                    timeout=10
                )
                response.raise_for_status()
                data = response.json()
                
                # Save with 15-minute interval timestamp
                file_path = os.path.join(city_dir, f"{current_date}_{current_time}.json")
                with open(file_path, "w") as f:
                    json.dump(data, f, indent=4)
                print(f"✅ Saved weather data for {city} to {file_path}")
                
            except requests.RequestException as e:
                print(f"❌ Failed to fetch data for {city}: {str(e)}")
                continue
            
    except Exception as e:
        print(f"❌ Critical error in fetch_weather_data: {str(e)}")
        raise

# 🔹 Upload to S3
def upload_to_s3():
    current_datetime = datetime.now(timezone.utc)
    current_datetime = current_datetime.replace(
        minute=(current_datetime.minute // 15) * 15,
        second=0,
        microsecond=0
    )
    current_date = current_datetime.strftime("%Y-%m-%d")
    current_time = current_datetime.strftime("%H-%M")
    
    try:
        for city in LOCATIONS:
            city_dir = os.path.join(DATA_DIR, city.replace(" ", "_"))
            file_path = os.path.join(city_dir, f"{current_date}_{current_time}.json")
            
            if os.path.exists(file_path):
                s3_key = f"raw/{city.replace(' ', '_')}/{current_date}/{current_time}.json"
                
                with open(file_path, "rb") as data:
                    s3_client.put_object(
                        Bucket=AWS_S3_BUCKET,
                        Key=s3_key,
                        Body=data,
                        ContentType="application/json"
                    )
                print(f"✅ Uploaded data to S3: {s3_key}")
            else:
                print(f"⚠️ No data file found for {city} on {current_date}_{current_time}")
                
    except Exception as e:
        print(f"❌ Error uploading to S3: {e}")
        raise

# 🔹 Insert into PostgreSQL (RDS)
def insert_into_db():
    current_datetime = datetime.now(timezone.utc)
    current_datetime = current_datetime.replace(
        minute=(current_datetime.minute // 15) * 15,
        second=0,
        microsecond=0
    )
    current_date = current_datetime.strftime("%Y-%m-%d")
    current_time = current_datetime.strftime("%H-%M")
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Add unique constraint if not exists
        cur.execute("""
            DO $$ 
            BEGIN 
                IF NOT EXISTS (
                    SELECT 1 FROM pg_constraint 
                    WHERE conname = 'unique_weather_reading'
                ) THEN 
                    ALTER TABLE weather_data 
                    ADD CONSTRAINT unique_weather_reading 
                    UNIQUE (location, date, time);
                END IF;
            END $$;
        """)

        # Modified query with ON CONFLICT clause
        query = """
            INSERT INTO weather_data 
            (location, temperature, pressure, humidity, wind_speed, cloud_cover, date, time)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (location, date, time) DO UPDATE 
            SET temperature = EXCLUDED.temperature,
                pressure = EXCLUDED.pressure,
                humidity = EXCLUDED.humidity,
                wind_speed = EXCLUDED.wind_speed,
                cloud_cover = EXCLUDED.cloud_cover
        """

        for city in LOCATIONS:
            city_dir = os.path.join(DATA_DIR, city.replace(" ", "_"))
            file_path = os.path.join(city_dir, f"{current_date}_{current_time}.json")
            
            if os.path.exists(file_path):
                with open(file_path, "r") as f:
                    data = json.load(f)
                
                # Convert timestamp to date and time
                dt_obj = datetime.fromtimestamp(data["dt"])
                date = dt_obj.date()
                time = dt_obj.time()
                
                values = (
                    data.get("name", "Unknown"),
                    round(data["main"]["temp"] - KELVIN_TO_CELSIUS, 2),
                    data["main"]["pressure"],
                    data["main"]["humidity"],
                    data["wind"]["speed"],
                    data["clouds"]["all"],
                    date,
                    time
                )
                
                cur.execute(query, values)
                print(f"✅ Inserted/Updated weather data for {city} into RDS")
            else:
                print(f"⚠️ No data file found for {city} on {current_date}_{current_time}")
        
        conn.commit()
        cur.close()
        conn.close()
        print("✅ Completed database insertions")

    except Exception as e:
        print(f"❌ Error inserting data into RDS: {e}")
        if 'conn' in locals():
            conn.close()
        raise

# 🔹 Define Airflow DAG
default_args = {
    "owner": "vineet",
    "depends_on_past": False,
    "start_date": days_ago(1),
    "retries": 1,
}

dag = DAG(
    "weathercast_pipeline",
    default_args=default_args,
    description="Fetch, store, and process weather data",
    schedule_interval="*/15 * * * *",  # Every 15 minutes
)

create_table_task = PythonOperator(
    task_id="create_table",
    python_callable=create_table,
    dag=dag,
)

fetch_weather_task = PythonOperator(
    task_id="fetch_weather_data",
    python_callable=fetch_weather_data,
    dag=dag,
)

upload_to_s3_task = PythonOperator(
    task_id="upload_to_s3",
    python_callable=upload_to_s3,
    dag=dag,
)

insert_into_rds_task = PythonOperator(
    task_id="insert_into_rds",
    python_callable=insert_into_db,
    dag=dag,
)

# 🔹 DAG Execution Order
create_table_task >> fetch_weather_task >> [upload_to_s3_task, insert_into_rds_task]