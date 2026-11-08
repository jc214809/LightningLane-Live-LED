from parks.names import DISNEY_WORLD_DESTINATION_ID, config_names

DESTINATIONS = [
    {"id": DISNEY_WORLD_DESTINATION_ID, "name": "Walt Disney World® Resort", "parks": [
        {"id": "1", "name": "Magic Kingdom Park"}, {"id": "2", "name": "Disney's Animal Kingdom Theme Park"},
        {"id": "3", "name": "Disney's Typhoon Lagoon Water Park"}, {"id": "4", "name": "EPCOT"}]},
    {"id": "cp", "name": "Cedar Point", "parks": [{"id": "5", "name": "Cedar Point"},
                                                  {"id": "6", "name": "Cedar Point Shores"}]},
    {"id": "other", "name": "Somewhere Else", "parks": [{"id": "7", "name": "EPCOT"}, {"name": ""}, "junk", {}]},
    "junk", {"id": "x", "name": "No parks"}, {"id": "y", "parks": None},
]


def test_names_are_as_config_json_takes_them_without_water_parks():
    assert config_names(DESTINATIONS) == [
        ("Animal Kingdom", "Walt Disney World® Resort"), ("Cedar Point", "Cedar Point"),
        ("EPCOT", "Walt Disney World® Resort"), ("Magic Kingdom", "Walt Disney World® Resort")]


def test_a_reply_thats_not_a_list_has_no_names():
    assert config_names(None) == [] and config_names({"destinations": []}) == []


def test_clean_ride_name_drops_marks_and_party_suffixes_as_the_app_always_did():
    from parks.names import clean_ride_name
    assert clean_ride_name("Tron™ Lightcycle") == "Tron Lightcycle"
    assert clean_ride_name("Pirates – Cruise*") == "Pirates - Cruise "
    assert clean_ride_name("Meet Mickey at Mickey's Not-So-Scary Halloween Party") == "Meet Mickey"
    assert clean_ride_name("An Original Show") == " Show"


def test_park_ids_matches_the_app_by_raw_or_cleaned_name_ignoring_case():
    from parks.names import DISNEY_WORLD_DESTINATION_ID, park_ids
    destinations = [{"id": DISNEY_WORLD_DESTINATION_ID, "parks": [{"id": "mk", "name": "Magic Kingdom Park"},
                                                                   {"id": "ec", "name": "EPCOT"}]},
                    {"id": "cp", "parks": [{"id": "cpid", "name": "Cedar Point"}]}, "junk", {"parks": "no"}]
    assert park_ids(destinations, ["magic kingdom", "Cedar Point", "Nowhere"]) == {"Magic Kingdom": "mk", "Cedar Point": "cpid"}
    assert park_ids(destinations, ["Magic Kingdom Park"]) == {"Magic Kingdom": "mk"}
    assert park_ids("nope", ["EPCOT"]) == {}
