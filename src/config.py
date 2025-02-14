# Centralized configuration and environment variable management.
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Configuration
NOAA_API_KEY = os.getenv("NOAA_API_KEY")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
BASE_URL = "http://api.openweathermap.org/data/2.5/weather"

# Kafka Configuration
KAFKA_SERVER = "localhost:9092"
KAFKA_TOPIC = "weather-data"

# Logging Configuration
LOG_DIR = "logs"
LOG_FILE = f"{LOG_DIR}/weathercast.log"

# Utility Constants
LOCATIONS_FILE = "locations.txt"

 
# AWS S3 Configuration
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
AWS_S3_BUCKET = os.getenv("AWS_S3_BUCKET")

# Database Configuration
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")

REFRESH_INTERVAL = 600
APP_TITLE = "WeatherCast : Real-time Weather Analytics Dashboard"
PROCESSED_DIR = os.path.join(os.getcwd(), "dataset", "processed")

BASE_DIR = os.path.abspath(os.path.dirname(__file__))  # Get the base directory of src
DATASET_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "dataset"))  # dataset/ outside src
MODELS_DIR = os.path.join(BASE_DIR, "models")  # src/models