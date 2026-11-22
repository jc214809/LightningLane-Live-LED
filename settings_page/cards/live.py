"""The cards that hold keys and connections: live ride updates, weather and the PIN by Pushover."""

from settings_page.markup import _field, _key_field, _options, _section, _switch, sub_dict
from utils.config import DEFAULT_WS_PROTOCOL, WS_PROTOCOLS


def live_card(config):
    ws = sub_dict(config, "websocket")
    return _section(
        "live",
        "Live ride updates",
        "Wait times as they change, from ThemeParks.wiki.",
        (
            _key_field("themeparks_key", "ThemeParks.wiki API key", ws.get("api_key"), "Needed for live updates.")
            + _switch(
                "ws_enabled",
                "Live ride updates",
                ws.get("enabled", True),
                "When off, the board still checks wait times every 5 minutes.",
            )
            + _field(
                "ws_protocol",
                "Live update protocol",
                _options(
                    "ws_protocol", [(p, p.capitalize()) for p in WS_PROTOCOLS], ws.get("protocol", DEFAULT_WS_PROTOCOL)
                ),
                "Preview is ThemeParks.wiki's newer feed; pick Legacy to go back to the old one.",
            )
        ),
        "live",
    )


def weather_card(config):
    weather = sub_dict(config, "weather")
    return _section(
        "weather",
        "Weather",
        "The temperature and conditions on each park's screen.",
        (_key_field("weather_key", "OpenWeatherMap API key", weather.get("apikey"), "From openweathermap.org.")),
        "cloud",
    )


def phone_card(config):
    push = sub_dict(config, "pushover")
    return _section(
        "phone",
        "PIN by Pushover",
        "Optional: sign in from a board you can't see.",
        (
            _key_field("pushover_user", "Pushover user key", push.get("user_key"), "On your pushover.net dashboard.")
            + _key_field(
                "pushover_token",
                "Pushover app token",
                push.get("app_token"),
                "Make an app on pushover.net for the board.",
            )
            + _switch(
                "pushover_enabled",
                "Send the PIN to my phone",
                push.get("enabled", True),
                "With both keys, the sign-in page can send its PIN to your phone (it still shows on the board).",
            )
        ),
        "phone",
    )
