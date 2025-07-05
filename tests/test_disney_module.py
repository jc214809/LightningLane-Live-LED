from datetime import datetime
from unittest.mock import patch, mock_open
import pytest

# Patch config loading so the module imports without a real file
MOCK_CONFIG = '{"debug": false, "trip_countdown": {"trip_date": "2025-01-01"}}'
with patch('builtins.open', mock_open(read_data=MOCK_CONFIG)):
    import disney
    from disney import validate_date


def test_validate_date_valid():
    date = validate_date("2025-01-01")
    assert isinstance(date, datetime)
    assert date.year == 2025


def test_validate_date_invalid():
    with pytest.raises(ValueError):
        validate_date("01-01-2025")
