import os, requests, json
from datetime import datetime, timezone

CLIENT_ID     = os.environ["STRAVA_CLIENT_ID"]
CLIENT_SECRET = os.environ["STRAVA_CLIENT_SECRET"]
REFRESH_TOKEN = os.environ["STRAVA_REFRESH_TOKEN"]

# Exchange refresh token for a fresh access token
token_res = requests.post("https://www.strava.com/oauth/token", data={
    "client_id":     CLIENT_ID,
    "client_secret": CLIENT_SECRET,
    "refresh_token": REFRESH_TOKEN,
    "grant_type":    "refresh_token",
})
token_res.raise_for_status()
access_token = token_res.json()["access_token"]

# Fetch the last 30 activities
activities_res = requests.get(
    "https://www.strava.com/api/v3/athlete/activities",
    headers={"Authorization": f"Bearer {access_token}"},
    params={"per_page": 30, "page": 1},
)
activities_res.raise_for_status()
activities = activities_res.json()

# Keep only the fields you actually need
def clean(a):
    return {
        "id":            a["id"],
        "name":          a["name"],
        "type":          a["sport_type"],
        "distance_m":    a["distance"],
        "moving_time_s": a["moving_time"],
        "start_date":    a["start_date_local"],
        "total_elev_m":  a["total_elevation_gain"],
        "avg_speed_ms":  a.get("average_speed"),
        "avg_watts":     a.get("average_watts"),
        "avg_hr":        a.get("average_heartrate"),
    }

os.makedirs("data", exist_ok=True)
with open("data/strava.json", "w") as f:
    json.dump({
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "activities": [clean(a) for a in activities],
    }, f, indent=2)

print(f"Saved {len(activities)} activities.")
