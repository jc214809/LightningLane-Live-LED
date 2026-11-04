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
