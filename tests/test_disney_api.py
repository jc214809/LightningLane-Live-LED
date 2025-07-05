from datetime import datetime, timezone
from unittest.mock import patch

from api.disney_api import (
    is_special_event,
    determine_llmp_price,
    get_down_time,
    park_has_operating_attraction,
)


def test_is_special_event_true():
    schedule = [{"type": "TICKETED_EVENT", "description": "Special ticketed event tonight"}]
    assert is_special_event(schedule)


def test_is_special_event_false():
    schedule = [{"type": "OPERATING", "description": "Open"}]
    assert not is_special_event(schedule)


def test_determine_llmp_price():
    event = {"purchases": [{"name": "Lightning Lane Multi Pass", "price": {"formatted": "$20"}}]}
    assert determine_llmp_price(event) == "$20"


def test_get_down_time():
    with patch('api.disney_api.datetime') as mock_datetime:
        mock_datetime.now.return_value = datetime(2024, 1, 1, 1, 0, 0, tzinfo=timezone.utc)
        mock_datetime.strptime.side_effect = lambda *a, **kw: datetime.strptime(*a, **kw)
        minutes = get_down_time("2024-01-01T00:00:00Z")
    assert minutes == 60


def test_park_has_operating_attraction_true():
    park = {
        "name": "Test Park",
        "attractions": [
            {"name": "Ride A", "waitTime": 10, "status": "OPERATING"},
            {"name": "Ride B", "waitTime": None, "status": "CLOSED"},
        ],
    }
    assert park_has_operating_attraction(park)


def test_park_has_operating_attraction_false():
    park = {
        "name": "Test Park",
        "attractions": [
            {"name": "Ride A", "waitTime": None, "status": "CLOSED"},
        ],
    }
    assert not park_has_operating_attraction(park)
