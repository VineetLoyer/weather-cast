import json
import os

DATA_DIR = "/opt/airflow/data/"
OUTPUT_FILE = "/opt/airflow/data/weather_data.json"

def merge_weather_data():
    all_weather_data = {}

    for city in os.listdir(DATA_DIR):
        city_path = os.path.join(DATA_DIR, city)
        
        if os.path.isdir(city_path):
            json_files = sorted([f for f in os.listdir(city_path) if f.endswith('.json')])

            if json_files:
                latest_file = json_files[-1]  # Pick the latest JSON file
                with open(os.path.join(city_path, latest_file), "r") as f:
                    all_weather_data[city] = json.load(f)

    # Save merged data
    with open(OUTPUT_FILE, "w") as f:
        json.dump(all_weather_data, f, indent=4)

    print(f"Merged weather data saved at: {OUTPUT_FILE}")

if __name__ == "__main__":
    merge_weather_data()
