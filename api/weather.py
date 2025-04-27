import json
import requests
import logging

def load_config(file_path):
    """Load the configuration from a JSON file."""
    with open(file_path, 'r') as file:
        config = json.load(file)
    return config

def fetch_weather_data(lat, lon):
    """Fetch the current weather data for the specified city."""
    config = load_config('config.json')
    weather_api_key = config['weather']['apikey']  # Set up your weather API key
    # city = config['weather']['city']  # Specify the city you want to fetch the weather for, e.g., "Orlando"

    api_url = f"http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={weather_api_key}&units=Imperial"
    try:
        logging.debug(f"Weather API URL: {api_url}")
        response = requests.get(api_url)
        logging.debug(f"Weather API response: {response}")
        response.raise_for_status()
        data = response.json()
        logging.debug(f"Weather API Response: {data}")
        return {
            "temperature": str(int(data["main"]["temp"])) + "°",
            "description": data["weather"][0]["description"],
            "short_description": data["weather"][0]["main"],
            "city": data["name"],
            "icon": data["weather"][0]["icon"]  # Icon code
        }
    except requests.RequestException as e:
        logging.error(f"Failed to fetch weather data: {e}")
        return None