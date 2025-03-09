import requests
import time
import pandas as pd
import schedule

class WaitTimes:
    def __init__(self):
        self.df = pd.DataFrame(columns=["Park", "Land", "Ride", "Wait Time"])

    def update_wait_times(self, park_ids):
        rows = []
        for park_name, park_id in park_ids:
            url = f"https://queue-times.com/parks/{park_id}/queue_times.json"
            response = requests.get(url)
            data = response.json()
            if "lands" not in data:
                continue
            for land in data["lands"]:
                for ride in land["rides"]:
                    rows.append([park_name, land["name"], ride["name"], ride["wait_time"]])
        
        # Update the DataFrame with the new data
        new_df = pd.DataFrame(rows, columns=["Park", "Land", "Ride", "Wait Time"])
        self.df = new_df
        print(self.df.to_string(index=False))

    def get_dataframe(self):
        return self.df

def get_disney_world_park_ids():
    url = "https://queue-times.com/parks.json"
    response = requests.get(url)
    data = response.json()
    walt_disney_attractions = None
    for company in data:
        if company["name"] == "Walt Disney Attractions":
            walt_disney_attractions = company
            break
    if not walt_disney_attractions:
        return []
    disney_world_parks = [
        "Animal Kingdom",
        "Disney Hollywood Studios",
        "Disney Magic Kingdom",
        "Epcot"
    ]
    park_ids = []
    for park in walt_disney_attractions["parks"]:
        if park["name"] in disney_world_parks:
            park_ids.append((park["name"], park["id"]))
    return park_ids

def job(wait_times):
    park_ids = get_disney_world_park_ids()
    if park_ids:
        wait_times.update_wait_times(park_ids)

# Instantiate the WaitTimes object
wait_times = WaitTimes()

# Schedule the job to run every 5 minutes
schedule.every(1).minutes.do(job, wait_times)

if __name__ == "__main__":
    while True:
        schedule.run_pending()  # Run all pending jobs
        time.sleep(1)  # Sleep for 1 second to avoid high CPU usage
