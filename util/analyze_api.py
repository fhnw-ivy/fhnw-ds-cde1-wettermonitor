import datetime
import time
import requests
import json

stations = ["mythenquai", "tiefenbrunnen"]
api_url = "https://tecdottir.herokuapp.com/measurements/{}?startDate={}&sort=timestamp_cet%20desc&limit=1&offset=0"

def watch_latest_data():
    timestamps = {s: [] for s in stations}

    while True:
        for station in stations:
            date = datetime.datetime.now().strftime("%Y-%m-%d")
            data = requests.get(api_url.format(station, date)).json()
            if data:
                timestamp = data["result"][0]["values"]["timestamp_cet"]["value"]
                timestamp = datetime.datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S%z")

                print(f"{datetime.datetime.now()} - {station}: {timestamp}")

                if timestamp not in timestamps[station]:
                    timestamps[station].append(timestamp)
                    print(f"New timestamp for {station}: {timestamp}")

        with open("timestamps.json", "w") as f:
            json.dump({s: [t.strftime("%Y-%m-%dT%H:%M:%S%z") for t in timestamps[s]] for s in stations}, f)

        time.sleep(60)


if __name__ == "__main__":
    watch_latest_data()