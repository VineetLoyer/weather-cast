#Purpose of this python code file is to handle API calls to fetch weather data.

import requests
from config import OPENWEATHER_API_KEY, BASE_URL
from logging_config import logger

# Fetch weather data for a location
def fetch_weather(location):
    logger.info(f"Fetching weather data for location: {location}")
    params = {"q": location, "appid": OPENWEATHER_API_KEY}
    
    # Example of API call:
    #       api.openweathermap.org/data/2.5/weather?q=London,uk&APPID=6c1ea51197146aa25f554a4b7f3da8f3
    
    try:
        response = requests.get(BASE_URL, params=params)
        response.raise_for_status()  # Raise an exception for HTTP errors
        logger.info(f"Successfully fetched data for {location}")
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error while fetching data for {location}: {e}")
        return None