import requests
import time


def fetch_disney_world_park_ids():
    """Fetch and return a list of Disney World parks with their respective IDs."""
    api_url = "https://queue-times.com/parks.json"
    response = requests.get(api_url)
    parks_data = response.json()

    disney_attractions = next(
        (company for company in parks_data if company["name"] == "Walt Disney Attractions"),
        None
    )

    if not disney_attractions:
        return []

    disney_world_park_names = {
        "Animal Kingdom",
        "Disney Hollywood Studios",
        "Disney Magic Kingdom",
        "Epcot"
    }

    return [
        (park["name"], park["id"])
        for park in disney_attractions["parks"]
        if park["name"] in disney_world_park_names
    ]


def fetch_wait_times(disney_park_list):
    """Fetch and return an array containing park, land, ride, wait time, category, and open status."""
    wait_times_data = []

    for park_name, park_id in disney_park_list:
        api_url = f"https://queue-times.com/parks/{park_id}/queue_times.json"
        response = requests.get(api_url)
        park_wait_times = response.json()

        if "lands" not in park_wait_times:
            continue

        for park_area in park_wait_times["lands"]:
            for attraction in park_area["rides"]:
                # Determine category based on ride name
                category = "Character Meet and Greet" if "Meet" in attraction["name"] else "Attraction"

                # Append ride information to list
                wait_times_data.append({
                    "Park": park_name,
                    "Land": park_area["name"],
                    "Ride": attraction["name"],
                    "Wait Time": attraction["wait_time"],
                    "Category": category,
                    "Open": attraction["is_open"]
                })

    return wait_times_data


if __name__ == "__main__":
    refresh_interval_seconds = 300  # Refresh every 5 minutes

    while True:
        disney_park_list = fetch_disney_world_park_ids()

        if disney_park_list:
            disney_wait_times = fetch_wait_times(disney_park_list)
            print(disney_wait_times)  # Now includes "Is Open" status

        time.sleep(refresh_interval_seconds)
