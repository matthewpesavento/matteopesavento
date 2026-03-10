import pandas as pd
import requests
import os
import time

ACCESS_TOKEN = "4fcdb45614db12c663e8a7e8133442bc362ec247"

headers = {
    "Authorization": f"Bearer {ACCESS_TOKEN}"
}

df = pd.read_csv("training_data.csv")

os.makedirs("streams", exist_ok=True)

print("Activities:", len(df))

for activity_id in df["id"]:

    file = f"streams/{activity_id}.csv"

    if os.path.exists(file):
        continue

    url = f"https://www.strava.com/api/v3/activities/{activity_id}/streams"

    params = {
        "keys": "time,distance,heartrate,watts,cadence,velocity_smooth,grade_smooth,altitude",
        "key_by_type": "true"
    }

    r = requests.get(url, headers=headers, params=params)

    # RATE LIMIT HANDLING
    if r.status_code == 429:
        print("Rate limit hit. Sleeping 15 minutes...")
        time.sleep(900)
        continue

    # AUTH ERROR
    if r.status_code == 401:
        print("Access token expired. Get a new one.")
        break

    if r.status_code != 200:
        print("Error:", activity_id, r.text)
        continue

    data = r.json()

    if not data:
        continue

    streams = {}

    for key in data:
        streams[key] = data[key]["data"]

    pd.DataFrame(streams).to_csv(file, index=False)

    print("Saved", activity_id)

    time.sleep(1)
