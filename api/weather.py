import json

import pyowm
import requests

from utils import debug

weather_api_key_valid= True

def load_config(file_path):
    """Load the configuration from a JSON file."""
    with open(file_path, 'r') as file:
        config = json.load(file)
    return config

def fetch_weather_data(lat, lon):
    """Fetch the current weather data for the specified city."""
    config = load_config('config.json')
    weather_api_key = config['weather']['apikey']  # Set up your weather API key
    global weather_api_key_valid  # Use the global flag to modify the outside state
    debug.info(f"Your Open Weather API Key is valid? {weather_api_key_valid}")
    try:
        debug.info(f"Fetching weather for lat:{lat} and lon:{lon}")
        if weather_api_key_valid:
            owm = pyowm.OWM(weather_api_key)
            client = owm.weather_manager()
            observation = client.weather_at_coords(lat, lon)
            weather_data = observation.weather  # Get the weather data
            debug.log(f"Weather Data for {observation.location.name}: {weather_data}")
            return {
                "temperature": str(int(weather_data.temperature('fahrenheit')["temp"])) + "°",
                "description": weather_data.detailed_status,
                "short_description": weather_data.status,
                "city": observation.location.name,
                "icon": weather_data.weather_icon_name # Icon code
            }
        else:
            debug.warning("[WEATHER] API key is invalid. Skipping API call.")
            return None  # Don't make further calls if the key is invalid
    except pyowm.commons.exceptions.UnauthorizedError:
        weather_api_key_valid = False  # Mark the key as invalid
        debug.warning(
            "[WEATHER] The API key provided doesn't appear to be valid. Please check your config.json."
        )
        return None
    except requests.RequestException as e:
        weather_api_key_valid = False  # Mark the key as invalid
        debug.error(f"Failed to fetch weather data: {e}")
        return None