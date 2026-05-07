import os
import json
from datetime import date, timedelta
from garminconnect import Garmin

client = Garmin(os.environ["GARMIN_EMAIL"], os.environ["GARMIN_PASSWORD"])
client.login()

today = date.today()

# Build 30-day history (fetches each day once)
history = []
daily_cache = {}
for i in range(29, -1, -1):
    day = today - timedelta(days=i)
    stats = client.get_stats(day.isoformat())
    steps = stats.get("totalSteps", 0)
    daily_cache[day.isoformat()] = steps
    history.append({"date": day.isoformat(), "steps": steps})

# Build this week's breakdown from cache
monday = today - timedelta(days=today.weekday())
day_steps_list = []
for i in range(7):
    day = monday + timedelta(days=i)
    if day <= today:
        day_steps_list.append(daily_cache.get(day.isoformat(), 0))
    else:
        day_steps_list.append(0)

weekly_steps = sum(day_steps_list)

output = {
    "weekly_steps": weekly_steps,
    "goal": 70000,
    "updated": today.isoformat(),
    "day_steps": day_steps_list,
    "history": history
}

os.makedirs("data", exist_ok=True)
with open("data/steps.json", "w") as f:
    json.dump(output, f)

print(f"Synced: {weekly_steps} steps this week")
print(f"Daily breakdown: {day_steps_list}")
