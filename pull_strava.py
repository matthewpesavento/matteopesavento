import requests
import pandas as pd
import os
import sys

# ----------------------------
# CONFIG
# ----------------------------

ACCESS_TOKEN = "4fcdb45614db12c663e8a7e8133442bc362ec247"

filename = "training_data.csv"

headers = {
    "Authorization": f"Bearer {ACCESS_TOKEN}"
}

# ----------------------------
# LOAD EXISTING DATA
# ----------------------------

if os.path.exists(filename):
    df_existing = pd.read_csv(filename)
    existing_ids = set(df_existing["id"])
    print(f"Existing activities loaded: {len(existing_ids)}")
else:
    df_existing = pd.DataFrame()
    existing_ids = set()
    print("No existing data found. Downloading full history.")

activities = []
page = 1

# ----------------------------
# DOWNLOAD ACTIVITIES
# ----------------------------

while True:

    url = "https://www.strava.com/api/v3/athlete/activities"

    params = {
        "per_page": 100,
        "page": page
    }

    response = requests.get(url, headers=headers, params=params)

    if response.status_code != 200:
        print("Strava API error:", response.text)
        sys.exit()

    data = response.json()

    # stop if no activities
    if not isinstance(data, list) or len(data) == 0:
        break

    new_this_page = 0

    for a in data:
        activity_id = a["id"]

        if activity_id in existing_ids:
            continue  # skip already saved

        activities.append({
            "id": activity_id,
            "name": a["name"],
            "type": a["type"],
            "distance_km": a["distance"] / 1000 if a.get("distance") else None,
            "moving_time_min": a["moving_time"] / 60 if a.get("moving_time") else None,
            "date": a["start_date"],
            "avg_hr": a.get("average_heartrate", None),
            "max_hr": a.get("max_heartrate", None),
            "avg_power": a.get("average_watts", None),
            "max_power": a.get("max_watts", None),
            "np": a.get("weighted_average_watts", None)
        })

        new_this_page += 1

    print(f"Page {page} processed — new activities: {new_this_page}")

    page += 1

# ----------------------------
# SAVE DATA
# ----------------------------

df_new = pd.DataFrame(activities)

df_combined = pd.concat([df_existing, df_new], ignore_index=True)

df_combined.to_csv(filename, index=False)

print("")
print("Download complete.")
print(f"New activities added: {len(df_new)}")
print(f"Total activities stored: {len(df_combined)}")
