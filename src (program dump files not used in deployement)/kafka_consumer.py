# Kafka Consumer Logic for testing
import os
import json
import time
import boto3
import psycopg2
from kafka import KafkaConsumer
from datetime import datetime
from config import (
    KAFKA_SERVER, KAFKA_TOPIC, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY,
    AWS_REGION, AWS_S3_BUCKET, DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASS
)
from logging_config import logger

# ✅ Initialize PostgreSQL Connection
try:
    conn = psycopg2.connect(
        host=DB_HOST,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        port=DB_PORT
    )
    cur = conn.cursor()
    logger.info("Connected to AWS RDS PostgreSQL successfully.")
except Exception as e:
    logger.error(f"Failed to connect to PostgreSQL: {e}")
    exit()

# ✅ Initialize Kafka Consumer
consumer = KafkaConsumer(
    KAFKA_TOPIC,
    bootstrap_servers=KAFKA_SERVER,
    auto_offset_reset="earliest",
    group_id="weather-consumers"
)

# ✅ Create Table if Not Exists
def create_table():
    query = """
        CREATE TABLE IF NOT EXISTS weather_data (
            id SERIAL PRIMARY KEY,
            location VARCHAR(255),
            temperature FLOAT,
            humidity FLOAT,
            timestamp BIGINT
        );
    """
    cur.execute(query)
    conn.commit()
    logger.info("Checked and created 'weather_data' table if it didn’t exist.")

# ✅ Insert Data into PostgreSQL
def insert_into_db(data):
    """Insert weather data into AWS RDS PostgreSQL."""
    query = """
        INSERT INTO weather_data (location, temperature, humidity, timestamp)
        VALUES (%s, %s, %s, %s)
    """
    values = (data["name"], data["main"]["temp"], data["main"]["humidity"], data["dt"])
    try:
        cur.execute(query, values)
        conn.commit()
        logger.info(f"Inserted weather data for {data['name']} into RDS.")
    except Exception as e:
        logger.error(f"Error inserting data into PostgreSQL: {e}")

# ✅ Save Locally Before Uploading to S3
DATA_DIR = "data"

def save_to_file(data):
    """Save weather data locally in structured location-wise directories."""
    location = data["name"].replace(" ", "_").lower()
    location_dir = os.path.join(DATA_DIR, location)
    os.makedirs(location_dir, exist_ok=True)

    date_str = datetime.utcnow().strftime("%Y-%m-%d")
    file_path = os.path.join(location_dir, f"{date_str}.json")

    try:
        # Append to existing file if available
        if os.path.exists(file_path):
            with open(file_path, "r+") as file:
                existing_data = json.load(file)
                existing_data.append(data)
                file.seek(0)
                json.dump(existing_data, file, indent=4)
        else:
            with open(file_path, "w") as file:
                json.dump([data], file, indent=4)

        logger.info(f"Weather data saved locally at {file_path}")
    except Exception as e:
        logger.error(f"Error saving local data for {location}: {e}")

# ✅ Upload to AWS S3
s3_client = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION
)

def save_to_s3(data):
    """Upload weather data to AWS S3 under structured folders."""
    date_str = datetime.utcnow().strftime("%Y-%m-%d")
    location = data["name"].replace(" ", "_").lower()
    filename = f"raw/{location}/{date_str}.json"

    try:
        s3_client.put_object(
            Bucket=AWS_S3_BUCKET,
            Key=filename,
            Body=json.dumps(data),
            ContentType="application/json"
        )
        logger.info(f"Uploaded weather data to S3 bucket '{AWS_S3_BUCKET}': {filename}")
    except Exception as e:
        logger.error(f"Error uploading data to S3: {e}")

# ✅ Start Kafka Consumer
if __name__ == "__main__":
    create_table()
    logger.info("Kafka Consumer started... Listening for messages.")
    
    try:
        while True:
            for message in consumer:
                weather_data = json.loads(message.value.decode())

                # ✅ Store locally
                save_to_file(weather_data)

                # ✅ Insert into RDS
                insert_into_db(weather_data)

                # ✅ Upload to S3
                save_to_s3(weather_data)

            logger.info("Sleeping for 15 minutes before consuming new data...")
            time.sleep(900)  # Sleep for 15 minutes (900 seconds)
    except KeyboardInterrupt:
        logger.info("Kafka Consumer shutting down gracefully...")
    finally:
        consumer.close()
        conn.close()
        logger.info("Kafka Consumer and PostgreSQL connection closed.")
