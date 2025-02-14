#Kafka producer logic

from kafka import KafkaProducer
import json
from logging_config import logger
from config import KAFKA_TOPIC, KAFKA_SERVER, LOCATIONS_FILE
from fetch_weather import fetch_weather

producer = KafkaProducer(
    bootstrap_servers=KAFKA_SERVER,
    value_serializer=lambda v: json.dumps(v).encode("utf-8")
)

def send_to_kafka(data):
    """Send data to the Kafka topic."""
    try:
        producer.send(KAFKA_TOPIC, value=data)
        producer.flush()
        logger.info(f"Data sent to Kafka topic {KAFKA_TOPIC}")
    except Exception as e:
        logger.error(f"Error sending data to Kafka: {e}")

def get_locations(file_path):
    """Read locations from a file."""
    with open(file_path, "r") as file:
        return [line.strip() for line in file]

if __name__ == "__main__":
    from config import LOCATIONS_FILE
    locations = get_locations(LOCATIONS_FILE)
    for location in locations:
        weather_data = fetch_weather(location)
        if weather_data:
            send_to_kafka(weather_data)
