import os, sys, json, time, requests

# ----------------------------
# AUTH
# ----------------------------

CLIENT_ID     = os.environ["STRAVA_CLIENT_ID"]
CLIENT_SECRET = os.environ["STRAVA_CLIENT_SECRET"]
REFRESH_TOKEN = os.environ["STRAVA_REFRESH_TOKEN"]

token_res = requests.post("https://www.strava.com/oauth/token", data={
    "client_id":     CLIENT_ID,
    "client_secret": CLIENT_SECRET,
    "refresh_token": REFRESH_TOKEN,
    "grant_type":    "refresh_token",
})
token_res.raise_for_status()
access_token = token_res.json()["access_token"]
headers = {"Authorization": f"Bearer {access_token}"}
print("Access token refreshed.")

# ----------------------------
# CONFIG
# ----------------------------

STREAM_KEYS = [
    "time",
    "distance",
    "altitude",
    "velocity_smooth",
    "heartrate",
    "cadence",
    "watts",
    "grade_smooth",
]

# ----------------------------
# LOAD ACTIVITY LIST
# ----------------------------

with open("data/strava.json") as f:
    strava = json.load(f)

activities = strava.get("activities", [])
print(f"Total activities: {len(activities)}")

os.makedirs("data/streams", exist_ok=True)

# ----------------------------
# BACKFILL STREAMS
# ----------------------------

fetched = 0
skipped = 0
failed  = 0

for i, a in enumerate(activities):
    activity_id = a.get("id")
    if not activity_id:
        continue

    stream_file = f"data/streams/{activity_id}.json"

    # Skip if already have it
    if os.path.exists(stream_file):
        skipped += 1
        continue

    print(f"[{i+1}/{len(activities)}] Fetching streams for {activity_id} ({a.get('sport_type') or a.get('type')}, {a.get('start_date','')[:10]})...")

    while True:
        try:
            r = requests.get(
                f"https://www.strava.com/api/v3/activities/{activity_id}/streams",
                headers=headers,
                params={"keys": ",".join(STREAM_KEYS), "key_by_type": "true"},
                timeout=30,
            )
        except requests.exceptions.RequestException as e:
            print(f"  Network error, retrying in 10s: {e}")
            time.sleep(10)
            continue

        if r.status_code == 429:
            print("  Rate limit hit. Sleeping 15 minutes...")
            time.sleep(900)
            continue

        if r.status_code == 401:
            print("  Auth failed.")
            sys.exit(1)

        if r.status_code == 404:
            print(f"  No streams available for {activity_id} (manual/indoor activity)")
            failed += 1
            break

        if r.status_code != 200:
            print(f"  Error {r.status_code}: {r.text}")
            failed += 1
            break

        data = r.json()
        if not data:
            print(f"  Empty streams for {activity_id}")
            failed += 1
            break

        streams_out = {}
        max_len = max((len(v["data"]) for v in data.values()), default=0)
        for key in STREAM_KEYS:
            if key in data:
                streams_out[key] = data[key]["data"]
            else:
                streams_out[key] = [None] * max_len

        with open(stream_file, "w") as f:
            json.dump(streams_out, f)

        fetched += 1
        break

    time.sleep(1)  # be polite to Strava's API

print(f"\nDone. Fetched: {fetched} | Skipped (already had): {skipped} | Failed/no data: {failed}")
