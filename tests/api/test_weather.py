import unittest
from unittest.mock import patch, MagicMock

import pyowm
import requests

import api.weather as weather_mod
from api.weather import fetch_weather_data

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
            patch('api.weather.load_config', side_effect=lambda *path: self.config),
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


class TestFetchWeatherLogPinning(TestWeatherModule):
    """Every log call, in order, and the exact return value, for each path of fetch_weather_data."""

    def setUp(self):
        super().setUp()
        self.logged = []
        for level in ("log", "info", "warning"):
            patcher = patch(f"api.weather.debug.{level}", side_effect=lambda m, level=level: self.logged.append((level, m)))
            patcher.start()
            self.addCleanup(patcher.stop)

    def messages(self):
        return [m for level, m in self.logged if not m.startswith("Weather Data for")]

    def test_success_returns_the_exact_reading_and_logs_the_observation(self):
        result = fetch_weather_data(0, 0)
        self.assertEqual(result, {"temperature": "75\u00b0", "description": "Sunny", "short_description": "Clear",
                                  "city": "Test City", "icon": "01d"})
        self.assertEqual([level for level, _ in self.logged], ["log"])
        self.assertTrue(self.logged[0][1].startswith("Weather Data for Test City:"))

    def test_cached_reading_returns_the_same_object_with_no_logs(self):
        first = fetch_weather_data(0, 0)
        self.logged.clear()
        self.assertIs(fetch_weather_data(0, 0), first)
        self.assertEqual(self.logged, [])

    def test_unreadable_config_logs_the_error(self):
        for exc in (OSError("disk"), ValueError("bad json"), AttributeError("nope")):
            self.logged.clear()
            with patch("api.weather.load_config", side_effect=exc):
                self.assertIsNone(fetch_weather_data(0, 0))
            self.assertEqual(self.logged, [("warning", f"[WEATHER] Couldn't read the API key from config.json: {exc}")])

    def test_unreadable_config_falls_back_to_the_last_reading(self):
        first = fetch_weather_data(0, 0)
        self.advance(weather_mod.CACHE_S)
        with patch("api.weather.load_config", side_effect=OSError("disk")):
            self.assertIs(fetch_weather_data(0, 0), first)

    def test_no_key_logs_and_falls_back(self):
        first = fetch_weather_data(0, 0)
        self.advance(weather_mod.CACHE_S)
        self.config = {}
        self.logged.clear()
        self.assertIs(fetch_weather_data(0, 0), first)
        self.assertEqual(self.logged, [("log", "[WEATHER] No API key in config.json; skipping weather.")])

    def test_first_401_warns_then_repeats_log_the_longer_wait(self):
        self.api.side_effect = exceptions.UnauthorizedError()
        self.assertIsNone(fetch_weather_data(0, 0))
        self.assertEqual(self.logged, [("warning", "[WEATHER] OpenWeatherMap rejected the API key (401); "
                                                   "checking it again in 5 min. Check config.json.")])
        self.logged.clear()
        self.advance(weather_mod.KEY_RECHECK_S)
        self.assertIsNone(fetch_weather_data(0, 0))
        self.assertEqual(self.logged, [("log", "[WEATHER] API key still rejected; next check in 10 min.")])

    def test_waiting_on_a_rejected_key_is_silent_and_falls_back(self):
        first = fetch_weather_data(0, 0)
        self.advance(weather_mod.CACHE_S)
        self.api.side_effect = exceptions.UnauthorizedError()
        fetch_weather_data(0, 0)
        self.logged.clear()
        self.assertIs(fetch_weather_data(0, 0), first)
        self.assertEqual(self.logged, [])
        self.assertEqual(self.api.call_count, 2)

    def test_changed_key_logs_and_retries(self):
        self.api.side_effect = exceptions.UnauthorizedError()
        fetch_weather_data(0, 0)
        self.logged.clear()
        self.api.side_effect = None
        self.config = {"weather": {"apikey": "fixed_key"}}
        fetch_weather_data(0, 0)
        self.assertEqual(self.messages(), ["[WEATHER] API key changed in config.json; trying it now."])
        self.assertEqual(self.logged[0][0], "info")

    def test_still_rejected_key_that_is_unchanged_but_due_is_called_again(self):
        self.api.side_effect = exceptions.UnauthorizedError()
        fetch_weather_data(0, 0)
        self.advance(weather_mod.KEY_RECHECK_S)
        self.api.side_effect = None
        self.logged.clear()
        fetch_weather_data(0, 0)
        self.assertEqual(self.messages(), ["[WEATHER] OpenWeatherMap accepted the API key again."])

    def test_not_found_logs_the_redacted_message(self):
        self.api.side_effect = exceptions.NotFoundError("no such place valid_api_key")
        self.assertIsNone(fetch_weather_data(3, 4))
        self.assertEqual(self.logged, [("warning", "[WEATHER] No weather for lat:3 lon:4 (404): no such place ***")])

    def test_not_found_falls_back_to_the_last_reading(self):
        first = fetch_weather_data(3, 4)
        self.advance(weather_mod.CACHE_S)
        self.api.side_effect = exceptions.NotFoundError("gone")
        self.assertIs(fetch_weather_data(3, 4), first)

    def test_rate_limit_logs_and_sets_the_pause(self):
        self.api.side_effect = exceptions.APIRequestError("429 too many")
        self.assertIsNone(fetch_weather_data(0, 0))
        self.assertEqual(self.logged, [("warning", "[WEATHER] Rate limited (429); pausing weather for 60s.")])
        self.assertEqual(weather_mod._paused_until, self.clock + weather_mod.PAUSE_S)

    def test_rate_limit_after_a_retry_stops_there(self):
        self.api.side_effect = [exceptions.TimeoutError("timed out"), exceptions.APIRequestError("429")]
        self.assertIsNone(fetch_weather_data(0, 0))
        self.assertEqual(self.slept, [1.0])
        self.assertEqual(self.api.call_count, 2)
        self.assertEqual([level for level, _ in self.logged], ["log", "warning"])

    def test_retries_log_each_delay_then_the_final_warning(self):
        self.api.side_effect = requests.ConnectionError("conn valid_api_key reset")
        self.assertIsNone(fetch_weather_data(0, 0))
        reason = "ConnectionError: conn *** reset"
        self.assertEqual(self.logged, [
            ("log", f"[WEATHER] Fetch failed ({reason}); retrying in 1.0s."),
            ("log", f"[WEATHER] Fetch failed ({reason}); retrying in 2.0s."),
            ("warning", f"[WEATHER] Fetch failed after 3 tries ({reason}); "
                        f"keeping the last reading and pausing weather for 60s."),
        ])
        self.assertEqual(self.slept, [1.0, 2.0])
        self.assertEqual(weather_mod._paused_until, self.clock + weather_mod.PAUSE_S)

    def test_backoff_adds_the_jitter(self):
        self.api.side_effect = [KeyError("x"), observation()]
        with patch("api.weather.random.uniform", return_value=0.25) as uniform:
            fetch_weather_data(0, 0)
        uniform.assert_called_once_with(0, weather_mod.BACKOFF_S)
        self.assertEqual(self.slept, [1.25])
        self.assertEqual(self.messages(), ["[WEATHER] Fetch failed (KeyError: 'x'); retrying in 1.2s."])

    def test_each_caught_exception_type_is_retried(self):
        for exc in (TypeError("t"), ValueError("v"), AttributeError("a"), KeyError("k"), requests.Timeout("r"),
                    exceptions.PyOWMError("p")):
            self.api.reset_mock()
            self.api.side_effect = exc
            weather_mod._reset()
            self.assertIsNone(fetch_weather_data(0, 0))
            self.assertEqual(self.api.call_count, 3, type(exc).__name__)

    def test_an_uncaught_exception_type_propagates(self):
        self.api.side_effect = RuntimeError("boom")
        with self.assertRaises(RuntimeError):
            fetch_weather_data(0, 0)

    def test_failure_after_pause_falls_back_to_the_last_reading_without_logs(self):
        first = fetch_weather_data(0, 0)
        self.advance(weather_mod.CACHE_S)
        self.api.side_effect = exceptions.TimeoutError("t")
        fetch_weather_data(0, 0)
        self.logged.clear()
        self.assertIs(fetch_weather_data(0, 0), first)
        self.assertEqual(self.logged, [])

    def test_stale_reading_is_not_used_during_a_pause(self):
        fetch_weather_data(0, 0)
        self.advance(weather_mod.STALE_S)
        self.api.side_effect = exceptions.TimeoutError("t")
        self.assertIsNone(fetch_weather_data(0, 0))
        self.assertIsNone(fetch_weather_data(0, 0))

    def test_success_stores_the_reading_with_its_fetch_time(self):
        result = fetch_weather_data(5, 6)
        self.assertEqual(weather_mod._last_good[(5, 6)], (result, self.clock))


if __name__ == '__main__':
    unittest.main()
