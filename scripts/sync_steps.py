import os
import json
from datetime import date, timedelta
from garminconnect import Garmin

# Login
client = Garmin(os.environ["GARMIN_EMAIL"], os.environ["GARMIN_PASSWORD"])
client.login()

# Get start of current week (Monday)
today = date.today()
monday = today - timedelta(days=today.weekday())

# Fetch daily steps for each day Mon -> today
weekly_steps = 0
for i in range((today - monday).days + 1):
    day = monday + timedelta(days=i)
    stats = client.get_stats(day.isoformat())
    weekly_steps += stats.get("totalSteps", 0)

# Save to data/steps.json
output = {
    "weekly_steps": weekly_steps,
    "goal": 70000,
    "updated": today.isoformat()
}

os.makedirs("data", exist_ok=True)
with open("data/steps.json", "w") as f:
    json.dump(output, f)

print(f"Synced: {weekly_steps} steps")
