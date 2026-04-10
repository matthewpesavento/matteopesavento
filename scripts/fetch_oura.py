import os, requests, json
from datetime import datetime, timezone, timedelta

TOKEN = os.environ["OURA_TOKEN"]
headers = {"Authorization": f"Bearer {TOKEN}"}

# Pull the last 30 days
end   = datetime.now(timezone.utc).date()
start = end - timedelta(days=30)
params = {"start_date": str(start), "end_date": str(end)}

def get(path):
    r = requests.get(f"https://api.ouraring.com/v2/usercollection/{path}",
                     headers=headers, params=params)
    r.raise_for_status()
    return r.json().get("data", [])

sleep    = get("sleep")
readiness = get("readiness")
activity  = get("daily_activity")
hrv       = get("daily_hrv")

os.makedirs("data", exist_ok=True)
with open("data/oura.json", "w") as f:
    json.dump({
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "sleep":      sleep,
        "readiness":  readiness,
        "activity":   activity,
        "hrv":        hrv,
    }, f, indent=2)

print(f"Saved {len(sleep)} sleep records, {len(readiness)} readiness records.")
