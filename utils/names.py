"""How the app spells park and ride names, and which destination is Walt Disney World. Pure and
standard-library only: api/ (which fetches and cleans the feed) and parks/names.py (which the
settings page's picker uses) both build on it, so neither has to import the other."""

DISNEY_WORLD_DESTINATION_ID = "e957da41-3552-4cf6-b636-5babc5cbc4e5"
WATER_PARK_KEYWORDS = ("Water Park", "Shores")


def clean_park_name(raw_name):
    return raw_name.replace("Theme", " ").replace("Park", " ").replace("Disney's", "").strip()


def is_water_park(raw_name):
    return any(kw in raw_name for kw in WATER_PARK_KEYWORDS)


def clean_ride_name(raw_name):
    """A ride's name as the app shows and matches it: no trademark sign or asterisk, a plain hyphen, and without
    the party suffix."""
    return (
        raw_name.replace("™", "")
        .replace("–", "-")
        .replace("*", " ")
        .replace("An Original", "")
        .replace(" at Mickey's Not-So-Scary Halloween Party", "")
    )
