import os, json, requests
from datetime import datetime, timezone, timedelta

# ----------------------------
# AUTH
# ----------------------------

TOKEN = os.environ["OURA_TOKEN"]
headers = {"Authorization": f"Bearer {TOKEN}"}

# ----------------------------
# CONFIG
# ----------------------------

LOOKBACK_DAYS = 90

end   = datetime.now(timezone.utc).date()
start = end - timedelta(days=LOOKBACK_DAYS)
params = {"start_date": str(start), "end_date": str(end)}

# ----------------------------
# FETCH
# ----------------------------

def get(endpoint):
    r = requests.get(
        f"https://api.ouraring.com/v2/usercollection/{endpoint}",
        headers=headers,
        params=params
    )
    if r.status_code == 401:
        print(f"Unauthorized — check your OURA_TOKEN secret.")
        return []
    if r.status_code != 200:
        print(f"Error fetching {endpoint}: {r.status_code} {r.text}")
        return []
    return r.json().get("data", [])

print("Fetching sleep...")
sleep = get("sleep")

print("Fetching daily sleep scores...")
daily_sleep = get("daily_sleep")

print("Fetching readiness...")
readiness = get("readiness")

print("Fetching daily activity...")
activity = get("daily_activity")

print("Fetching HRV...")
hrv = get("daily_hrv")

print("Fetching workout summaries...")
workouts = get("workout")

print("Fetching sessions...")
sessions = get("session")

# ----------------------------
# SAVE
# ----------------------------

os.makedirs("data", exist_ok=True)

with open("data/oura.json", "w") as f:
    json.dump({
        "updated_at":    datetime.now(timezone.utc).isoformat(),
        "lookback_days": LOOKBACK_DAYS,
        "sleep":         sleep,
        "daily_sleep":   daily_sleep,
        "readiness":     readiness,
        "activity":      activity,
        "hrv":           hrv,
        "workouts":      workouts,
        "sessions":      sessions,
    }, f, indent=2)

print(f"\nDone.")
print(f"  Sleep records:        {len(sleep)}")
print(f"  Daily sleep scores:   {len(daily_sleep)}")
print(f"  Readiness records:    {len(readiness)}")
print(f"  Activity records:     {len(activity)}")
print(f"  HRV records:          {len(hrv)}")
print(f"  Workouts:             {len(workouts)}")
print(f"  Sessions:             {len(sessions)}")
