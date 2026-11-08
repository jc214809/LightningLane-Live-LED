"""Park names as config.json's "parks" takes them, shared by the app (api.disney_api) and the
settings page's picker, so the page offers exactly the names the app can find. No imports
beyond the standard library: the settings page runs without the app's packages loaded."""

DISNEY_WORLD_DESTINATION_ID = "e957da41-3552-4cf6-b636-5babc5cbc4e5"
WATER_PARK_KEYWORDS = ("Water Park", "Shores")


def clean_park_name(raw_name):
    return raw_name.replace("Theme", " ").replace("Park", " ").replace("Disney's", "").strip()


def is_water_park(raw_name):
    return any(kw in raw_name for kw in WATER_PARK_KEYWORDS)


def clean_ride_name(raw_name):
    """A ride's name as the app shows and matches it: no trademark sign or asterisk, a plain hyphen, and without
    the party suffix."""
    return (raw_name.replace("\u2122", "").replace("–", "-").replace("*", " ").replace("An Original", "")
            .replace(" at Mickey's Not-So-Scary Halloween Party", ""))


def park_ids(destinations, park_names):
    """{park name as config.json has it: park id} for each of park_names that /v1/destinations lists, matched like
    the app does (raw or cleaned name, ignoring case); the name is the one the destinations list gives, cleaned."""
    wanted = {n.lower() for n in park_names}
    found = {}
    for dest in destinations if isinstance(destinations, list) else []:
        is_disney = isinstance(dest, dict) and dest.get("id") == DISNEY_WORLD_DESTINATION_ID
        for park in dest.get("parks") if isinstance(dest, dict) and isinstance(dest.get("parks"), list) else []:
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
    names = {}
    for dest in destinations if isinstance(destinations, list) else []:
        if not isinstance(dest, dict):
            continue
        is_disney = dest.get("id") == DISNEY_WORLD_DESTINATION_ID
        for park in dest.get("parks") if isinstance(dest.get("parks"), list) else []:
            raw = park.get("name") if isinstance(park, dict) else None
            if not isinstance(raw, str) or not raw.strip() or is_water_park(raw):
                continue
            name = clean_park_name(raw) if is_disney else raw.strip()
            names.setdefault(name.lower(), (name, str(dest.get("name") or "")))
    return sorted(names.values(), key=lambda n: n[0].lower())
