"""Park names as config.json's "parks" takes them, shared by the app and the settings page's picker, so
the page offers exactly the names the app can find. The cleaning rules and Walt Disney World's destination
id live in utils/names.py (api/disney_api.py uses them too) and are re-exported here, so importers of
parks.names keep working. No imports beyond utils.names: the settings page runs without the app's
packages loaded."""

from utils.names import (
    DISNEY_WORLD_DESTINATION_ID,
    WATER_PARK_KEYWORDS,
    clean_park_name,
    clean_ride_name,
    is_water_park,
)

__all__ = [
    "DISNEY_WORLD_DESTINATION_ID",
    "WATER_PARK_KEYWORDS",
    "clean_park_name",
    "clean_ride_name",
    "is_water_park",
    "park_ids",
    "config_names",
]


def park_ids(destinations, park_names):
    """{park name as config.json has it: park id} for each of park_names that /v1/destinations lists, matched like
    the app does (raw or cleaned name, ignoring case); the name is the one the destinations list gives, cleaned."""
    wanted = {n.lower() for n in park_names}
    found: dict[str, str] = {}
    for dest in destinations if isinstance(destinations, list) else []:
        is_disney = isinstance(dest, dict) and dest.get("id") == DISNEY_WORLD_DESTINATION_ID
        parks = dest.get("parks") if isinstance(dest, dict) else None
        for park in parks if isinstance(parks, list) else []:
            raw = park.get("name") if isinstance(park, dict) else None
            if not isinstance(raw, str) or not park.get("id"):
                continue
            cleaned = clean_park_name(raw) if is_disney else raw.strip()
            if raw.lower() in wanted or cleaned.lower() in wanted:
                found.setdefault(cleaned, str(park["id"]))
    return found


def config_names(destinations):
    """[(name, destination name)] for every park /v1/destinations lists, water parks left out (the
    app drops them), named as config.json takes them: Walt Disney World's cleaned ("Magic Kingdom"),
    the rest as the API has them. Skips anything malformed; first of a repeated name wins."""
    names: dict[str, tuple[str, str]] = {}
    for dest in destinations if isinstance(destinations, list) else []:
        if not isinstance(dest, dict):
            continue
        is_disney = dest.get("id") == DISNEY_WORLD_DESTINATION_ID
        parks = dest.get("parks")
        for park in parks if isinstance(parks, list) else []:
            raw = park.get("name") if isinstance(park, dict) else None
            if not isinstance(raw, str) or not raw.strip() or is_water_park(raw):
                continue
            name = clean_park_name(raw) if is_disney else raw.strip()
            names.setdefault(name.lower(), (name, str(dest.get("name") or "")))
    return sorted(names.values(), key=lambda n: n[0].lower())
