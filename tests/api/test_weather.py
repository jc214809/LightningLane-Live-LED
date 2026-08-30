import unittest
from unittest.mock import patch, MagicMock
import pyowm
import requests

from api.weather import load_config, fetch_weather_data

class TestWeatherModule(unittest.TestCase):

    def setUp(self):
        try:
            import api.weather as weather_mod
            weather_mod.weather_api_key_valid = True
        except AttributeError:
            pass

    @patch('builtins.open', new_callable=unittest.mock.mock_open, read_data='{"weather": {"apikey": "valid_api_key"}}')
    def test_load_config(self, mock_open):
        config = load_config('fake_path.json')
        self.assertEqual(config['weather']['apikey'], 'valid_api_key')

    @patch('api.weather.load_config')
    @patch('pyowm.OWM')
    def test_fetch_weather_data_valid(self, mock_OWM, mock_load_config):
        from api.weather import fetch_weather_data
        mock_load_config.return_value = {'weather': {'apikey': 'valid_api_key'}}
        import api.weather as weather_mod
        weather_mod.weather_api_key_valid = True

        mock_weather_manager = MagicMock()
        mock_observation = MagicMock()
        mock_weather_data = MagicMock()
        mock_weather_data.temperature.return_value = {"temp": 75.0}
        mock_weather_data.detailed_status = "Sunny"
        mock_weather_data.status = "Clear"
        mock_weather_data.weather_icon_name = "01d"

        mock_observation.weather = mock_weather_data
        mock_observation.location.name = "Test City"

        mock_OWM.return_value.weather_manager.return_value = mock_weather_manager
        mock_weather_manager.weather_at_coords.return_value = mock_observation

        result = fetch_weather_data(0, 0)
        self.assertIsNotNone(result)
        self.assertEqual(result['temperature'], "75°")
        self.assertEqual(result['description'], "Sunny")
        self.assertEqual(result['city'], "Test City")

    @patch('api.weather.load_config')
    @patch('pyowm.OWM')
    @patch('api.weather.debug.warning')
    def test_fetch_weather_data_invalid_key(self, mock_warning, mock_OWM, mock_load_config):
        from api.weather import fetch_weather_data
        mock_load_config.return_value = {'weather': {'apikey': 'invalid_api_key'}}
        mock_OWM.side_effect = pyowm.commons.exceptions.UnauthorizedError()
        result = fetch_weather_data(0, 0)
        self.assertIsNone(result)
        mock_warning.assert_called_with(
            "[WEATHER] The API key provided doesn't appear to be valid. Please check your config.json."
        )

    @patch('api.weather.load_config')
    @patch('pyowm.OWM')
    def test_fetch_weather_data_request_failure(self, mock_OWM, mock_load_config):
        from api.weather import fetch_weather_data
        mock_load_config.return_value = {'weather': {'apikey': 'valid_api_key'}}
        mock_weather_manager = MagicMock()
        mock_weather_manager.weather_at_coords.side_effect = requests.RequestException("Request failed")
        mock_OWM.return_value.weather_manager.return_value = mock_weather_manager

        with patch('api.weather.debug.error') as mock_error:
            result = fetch_weather_data(0, 0)
            self.assertIsNone(result)
            mock_error.assert_called_with("Failed to fetch weather data: Request failed")

    @patch('pyowm.OWM')
    def test_fetch_weather_data_uses_api_key_argument_without_config_file(self, mock_OWM):
        """Callers with no config.json (e.g. the bullpen plugin) pass api_key directly."""
        from api.weather import fetch_weather_data

        mock_weather_manager = MagicMock()
        mock_observation = MagicMock()
        mock_weather_data = MagicMock()
        mock_weather_data.temperature.return_value = {"temp": 75.0}
        mock_weather_data.detailed_status = "Sunny"
        mock_weather_data.status = "Clear"
        mock_weather_data.weather_icon_name = "01d"
        mock_observation.weather = mock_weather_data
        mock_observation.location.name = "Test City"
        mock_OWM.return_value.weather_manager.return_value = mock_weather_manager
        mock_weather_manager.weather_at_coords.return_value = mock_observation

        with patch('api.weather.load_config') as mock_load_config:
            result = fetch_weather_data(0, 0, api_key="argument_api_key")
            mock_load_config.assert_not_called()
        mock_OWM.assert_called_with("argument_api_key")
        self.assertEqual(result['city'], "Test City")

    def test_fetch_weather_data_no_key_no_config_file_returns_none(self):
        """No api_key argument and no config.json on disk: fail soft, not with an exception."""
        from api.weather import fetch_weather_data

        with patch('api.weather.load_config', side_effect=FileNotFoundError()):
            with patch('api.weather.debug.warning') as mock_warning:
                result = fetch_weather_data(0, 0)
        self.assertIsNone(result)
        mock_warning.assert_called_once()

    def test_fetch_weather_data_config_file_missing_weather_key_returns_none(self):
        """config.json exists but has no weather.apikey: fail soft, not with a KeyError."""
        from api.weather import fetch_weather_data

        with patch('api.weather.load_config', return_value={}):
            with patch('api.weather.debug.warning') as mock_warning:
                result = fetch_weather_data(0, 0)
        self.assertIsNone(result)
        mock_warning.assert_called_once()

if __name__ == '__main__':
    unittest.main()