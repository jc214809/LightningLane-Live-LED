import unittest
from unittest.mock import patch, MagicMock

import api.weather
import pyowm
import requests
from api.weather import load_config, fetch_weather_data


class TestWeatherModule(unittest.TestCase):

    def setUp(self):
        # Ensure any global state is reset before each test
        api.weather.weather_api_key_valid = True

    @patch('builtins.open', new_callable=unittest.mock.mock_open, read_data='{"weather": {"apikey": "valid_api_key"}}')
    def test_load_config(self, mock_open):
        config = load_config('fake_path.json')
        self.assertEqual(config['weather']['apikey'], 'valid_api_key')

    @patch('api.weather.load_config')
    @patch('pyowm.OWM')
    def test_fetch_weather_data_valid(self, mock_owm, mock_load_config):
        # Manually reset the global variable
        api.weather.weather_api_key_valid = True

        # Mock load_config to return valid API key
        mock_load_config.return_value = {'weather': {'apikey': 'valid_api_key'}}

        # Create mocks for the weather manager and response
        mock_weather_manager = MagicMock()
        mock_observation = MagicMock()
        mock_weather_data = MagicMock()

        # Define the expected weather data
        mock_weather_data.temperature.return_value = {"temp": 75.0}
        mock_weather_data.detailed_status = "Sunny"
        mock_weather_data.status = "Clear"
        mock_weather_data.weather_icon_name = "01d"

        # Set up mock relationships
        mock_observation.weather = mock_weather_data
        mock_observation.location.name = "Test City"

        # Configure the mock OWM to return the correct structures
        mock_owm.return_value.weather_manager.return_value = mock_weather_manager
        mock_weather_manager.weather_at_coords.return_value = mock_observation

        # Call the function
        result = fetch_weather_data(0, 0)

        # Validate results
        self.assertIsNotNone(result)
        self.assertEqual(result['temperature'], "75°")
        self.assertEqual(result['description'], "Sunny")
        self.assertEqual(result['city'], "Test City")

    @patch('api.weather.load_config')
    @patch('pyowm.OWM')
    @patch('api.weather.debug.warning')  # Mock the debug warning function
    def test_fetch_weather_data_invalid_key(self, mock_debug_warning, mock_owm, mock_load_config):
        # Mock load_config to return invalid API key
        mock_load_config.return_value = {'weather': {'apikey': 'invalid_api_key'}}

        # Simulate the invalid API key behavior
        mock_owm.side_effect = pyowm.commons.exceptions.UnauthorizedError()

        result = fetch_weather_data(0, 0)

        self.assertIsNone(result)
        mock_debug_warning.assert_called_with(
            "[WEATHER] The API key provided doesn't appear to be valid. Please check your config.json.")

    @patch('api.weather.load_config')
    @patch('pyowm.OWM')
    def test_fetch_weather_data_request_failure(self, mock_requests_get, mock_load_config):
        # Mock load_config to return valid API key
        mock_load_config.return_value = {'weather': {'apikey': 'valid_api_key'}}

        # Simulate a request exception
        mock_requests_get.side_effect = requests.RequestException("Request failed")

        # Ensure patching points to the correct full path of debug.error
        with patch('api.weather.debug.error') as mock_error:
            result = fetch_weather_data(0, 0)
            self.assertIsNone(result)  # Should return None on request failure
            mock_error.assert_called_with("Failed to fetch weather data: Request failed")


if __name__ == '__main__':
    unittest.main()