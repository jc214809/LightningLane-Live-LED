import unittest
from unittest.mock import patch, MagicMock

import pyowm
import requests

import api.weather as weather_mod
from api.weather import load_config, fetch_weather_data

exceptions = pyowm.commons.exceptions


def observation(temp=75.0, status="Clear", detailed="Sunny", city="Test City", icon="01d"):
    weather = MagicMock()
    weather.temperature.return_value = {"temp": temp}
    weather.status = status
    weather.detailed_status = detailed
    weather.weather_icon_name = icon
    obs = MagicMock()
    obs.weather = weather
    obs.location.name = city
    return obs


class TestWeatherModule(unittest.TestCase):

    def setUp(self):
        weather_mod._reset()
        self.clock = 1000.0
        self.slept = []
        patches = [
            patch('api.weather.time.monotonic', side_effect=lambda: self.clock),
            patch('api.weather.time.sleep', side_effect=self._sleep),
            patch('api.weather.random.uniform', return_value=0.0),
            patch('api.weather.load_config', side_effect=lambda path: self.config),
            patch('pyowm.OWM'),
        ]
        mocks = [p.start() for p in patches]
        for p in patches:
            self.addCleanup(p.stop)
        self.config = {'weather': {'apikey': 'valid_api_key'}}
        self.owm = mocks[-1]
        self.api = self.owm.return_value.weather_manager.return_value.weather_at_coords
        self.api.return_value = observation()

    def _sleep(self, seconds):
        self.slept.append(seconds)
        self.clock += seconds

    def advance(self, seconds):
        self.clock += seconds

    @patch('builtins.open', new_callable=unittest.mock.mock_open, read_data='{"weather": {"apikey": "valid_api_key"}}')
    def test_load_config(self, mock_open):
        config = load_config('fake_path.json')
        self.assertEqual(config['weather']['apikey'], 'valid_api_key')

    def test_fetch_weather_data_valid(self):
        result = fetch_weather_data(0, 0)
        self.assertEqual(result['temperature'], "75°")
        self.assertEqual(result['description'], "Sunny")
        self.assertEqual(result['city'], "Test City")
        self.assertEqual(result['icon'], "01d")
        self.owm.assert_called_with('valid_api_key')

    def test_thunderstorm_is_shortened(self):
        self.api.return_value = observation(status="Thunderstorm")
        self.assertEqual(fetch_weather_data(0, 0)['short_description'], "T-Storm")

    def test_a_fresh_reading_is_reused_instead_of_calling_again(self):
        fetch_weather_data(0, 0)
        self.advance(weather_mod.CACHE_S - 1)
        fetch_weather_data(0, 0)
        self.assertEqual(self.api.call_count, 1)
        self.advance(1)
        fetch_weather_data(0, 0)
        self.assertEqual(self.api.call_count, 2)

    def test_each_location_is_cached_separately(self):
        fetch_weather_data(0, 0)
        fetch_weather_data(1, 1)
        self.assertEqual(self.api.call_count, 2)

    # --- rejected key (401) ---

    def test_rejected_key_is_not_called_again_until_the_recheck(self):
        self.api.side_effect = exceptions.UnauthorizedError()
        with patch('api.weather.debug.warning') as warning:
            self.assertIsNone(fetch_weather_data(0, 0))
        self.assertIn("rejected the API key (401)", warning.call_args[0][0])
        self.advance(weather_mod.KEY_RECHECK_S - 1)
        fetch_weather_data(0, 0)
        fetch_weather_data(1, 1)
        self.assertEqual(self.api.call_count, 1, "no calls while waiting to recheck")
        self.assertEqual(self.slept, [], "a 401 isn't retried")

    def test_recheck_is_one_call_and_brings_weather_back(self):
        self.api.side_effect = exceptions.UnauthorizedError()
        fetch_weather_data(0, 0)
        self.advance(weather_mod.KEY_RECHECK_S)
        self.api.side_effect = None
        with patch('api.weather.debug.info') as info:
            result = fetch_weather_data(0, 0)
        self.assertEqual(result['temperature'], "75°")
        self.assertEqual(self.api.call_count, 2)
        info.assert_called_with("[WEATHER] OpenWeatherMap accepted the API key again.")
        # Recovered: other parks fetch straight away.
        fetch_weather_data(1, 1)
        self.assertEqual(self.api.call_count, 3)

    def test_failed_recheck_blocks_the_other_parks_too(self):
        self.api.side_effect = exceptions.UnauthorizedError()
        fetch_weather_data(0, 0)
        self.advance(weather_mod.KEY_RECHECK_S)
        fetch_weather_data(0, 0)
        fetch_weather_data(1, 1)
        fetch_weather_data(2, 2)
        self.assertEqual(self.api.call_count, 2, "only the first park's call rechecks")

    def test_recheck_wait_doubles_up_to_the_cap(self):
        self.api.side_effect = exceptions.UnauthorizedError()
        fetch_weather_data(0, 0)
        waits = []
        for _ in range(6):
            waits.append(weather_mod._rejected["wait"])
            self.advance(weather_mod._rejected["wait"])
            fetch_weather_data(0, 0)
        self.assertEqual(waits, [300, 600, 1200, 2400, 3600, 3600])

    def test_rejection_warns_once_not_every_recheck(self):
        self.api.side_effect = exceptions.UnauthorizedError()
        with patch('api.weather.debug.warning') as warning:
            fetch_weather_data(0, 0)
            for _ in range(3):
                self.advance(weather_mod.KEY_RECHECK_MAX_S)
                fetch_weather_data(0, 0)
        self.assertEqual(warning.call_count, 1)

    def test_new_key_in_config_skips_the_wait(self):
        self.api.side_effect = exceptions.UnauthorizedError()
        fetch_weather_data(0, 0)
        self.api.side_effect = None
        self.config = {'weather': {'apikey': 'fixed_key'}}
        result = fetch_weather_data(0, 0)
        self.assertEqual(result['temperature'], "75°")
        self.owm.assert_called_with('fixed_key')
        self.assertIsNone(weather_mod._rejected)

    def test_rejected_key_keeps_showing_the_last_reading(self):
        fetch_weather_data(0, 0)
        self.advance(weather_mod.CACHE_S)
        self.api.side_effect = exceptions.UnauthorizedError()
        self.assertEqual(fetch_weather_data(0, 0)['temperature'], "75°")

    # --- temporary failures ---

    def test_timeout_is_retried_with_backoff_then_succeeds(self):
        self.api.side_effect = [exceptions.TimeoutError("timed out"), exceptions.BadGatewayError("502"), observation()]
        self.assertEqual(fetch_weather_data(0, 0)['temperature'], "75°")
        self.assertEqual(self.slept, [1.0, 2.0])

    def test_dns_failure_keeps_the_last_reading_and_does_not_raise(self):
        # Disneypi, Sep 27: a DNS outage surfaced as InvalidSSLCertificateError and
        # escaped fetch_weather_data, aborting the rest of the update cycle.
        fetch_weather_data(0, 0)
        self.advance(weather_mod.CACHE_S)
        self.api.side_effect = exceptions.InvalidSSLCertificateError(
            "Failed to resolve 'api.openweathermap.org' url: /data/2.5/weather?APPID=valid_api_key&lat=0")
        with patch('api.weather.debug.warning') as warning:
            result = fetch_weather_data(0, 0)
        self.assertEqual(result['temperature'], "75°")
        self.assertEqual(self.api.call_count, 1 + weather_mod.RETRIES + 1)
        message = warning.call_args[0][0]
        self.assertIn("Failed to resolve", message)
        self.assertNotIn("valid_api_key", message, "the key is redacted from logs")

    def test_outage_pauses_the_other_parks_instead_of_retrying_each(self):
        self.api.side_effect = exceptions.InvalidSSLCertificateError("connection refused")
        fetch_weather_data(0, 0)
        fetch_weather_data(1, 1)
        fetch_weather_data(2, 2)
        self.assertEqual(self.api.call_count, weather_mod.RETRIES + 1)
        self.advance(weather_mod.PAUSE_S)
        self.api.side_effect = None
        self.assertEqual(fetch_weather_data(1, 1)['temperature'], "75°")

    def test_raw_requests_error_is_handled(self):
        self.api.side_effect = requests.RequestException("Request failed")
        self.assertIsNone(fetch_weather_data(0, 0))

    def test_rate_limit_pauses_without_retrying(self):
        self.api.side_effect = exceptions.APIRequestError('{"cod":429, "message": "Your account is temporary blocked"}')
        with patch('api.weather.debug.warning') as warning:
            self.assertIsNone(fetch_weather_data(0, 0))
        self.assertIn("429", warning.call_args[0][0])
        self.assertEqual(self.slept, [])
        fetch_weather_data(1, 1)
        self.assertEqual(self.api.call_count, 1)

    def test_not_found_is_not_retried(self):
        self.api.side_effect = exceptions.NotFoundError("Unable to find the resource")
        self.assertIsNone(fetch_weather_data(0, 0))
        self.assertEqual(self.api.call_count, 1)
        self.assertIsNone(weather_mod._rejected)

    def test_last_reading_expires_after_an_hour(self):
        fetch_weather_data(0, 0)
        self.api.side_effect = exceptions.TimeoutError("timed out")
        self.advance(weather_mod.STALE_S)
        self.assertIsNone(fetch_weather_data(0, 0))

    # --- bad responses and config ---

    def test_response_missing_temperature_is_handled(self):
        self.api.return_value.weather.temperature.return_value = {}
        self.assertIsNone(fetch_weather_data(0, 0))

    def test_unparseable_response_is_handled(self):
        self.api.side_effect = exceptions.ParseAPIResponseError("Impossible to parse API response data")
        self.assertIsNone(fetch_weather_data(0, 0))

    def test_missing_key_skips_the_call(self):
        self.config = {}
        self.assertIsNone(fetch_weather_data(0, 0))
        self.config = {'weather': {'apikey': ''}}
        self.assertIsNone(fetch_weather_data(0, 0))
        self.api.assert_not_called()

    def test_unreadable_config_is_handled(self):
        with patch('api.weather.load_config', side_effect=ValueError("bad json")):
            self.assertIsNone(fetch_weather_data(0, 0))
        self.api.assert_not_called()


if __name__ == '__main__':
    unittest.main()
