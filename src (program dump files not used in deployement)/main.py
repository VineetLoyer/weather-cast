from apscheduler.schedulers.blocking import BlockingScheduler
import subprocess
import time
import os
from fetch_weather import fetch_weather
from kafka_producer import send_to_kafka, get_locations
from logging_config import logger
from config import LOCATIONS_FILE

def start_kafka_consumer():
    """Ensure Kafka Consumer is running in the background."""
    logger.info("Starting Kafka Consumer...")
    subprocess.Popen(["python", "src/kafka_consumer.py"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def run_pipeline():
    """Orchestrate the WeatherCast pipeline."""
    locations = get_locations(LOCATIONS_FILE)

    # ✅ Step 1: Start Kafka Consumer (if not running)
    start_kafka_consumer()

    # ✅ Step 2: Fetch & Send Weather Data
    for location in locations:
        weather_data = fetch_weather(location)
        if weather_data:
            send_to_kafka(weather_data)

    # ✅ Step 3: Wait for Kafka Consumer to Process Data
    logger.info("Waiting for Kafka Consumer to ingest data into S3/RDS...")
    time.sleep(30)  # Allow consumer time to process

    # ✅ Step 4: Trigger Airflow DAG for Batch Processing
    logger.info("Triggering Airflow DAG for batch processing & forecasting...")
    os.system("airflow dags trigger weathercast_pipeline")

    # ✅ Step 5: Wait for Airflow DAG Completion
    logger.info("Waiting for Airflow to process data...")
    time.sleep(120)  # Adjust based on DAG duration

    # ✅ Step 6: Restart Streamlit Dashboard
    logger.info("Restarting Streamlit Dashboard to update UI...")
    os.system("pkill -f streamlit")  # Stop previous Streamlit instance
    os.system("streamlit run src/app.py &")  # Restart UI

# ⏳ Schedule Pipeline to Run Every 30 Minutes
scheduler = BlockingScheduler()
scheduler.add_job(run_pipeline, "interval", minutes=30)

if __name__ == "__main__":
    logger.info("Starting WeatherCast pipeline automation...")
    scheduler.start()
