import os
import json
from datetime import date, timedelta
from garminconnect import Garmin

client = Garmin(os.environ["GARMIN_EMAIL"], os.environ["GARMIN_PASSWORD"])
client.login()

today = date.today()
monday = today - timedelta(days=today.weekday())

day_steps_list = []
for i in range(7):
    day = monday + timedelta(days=i)
    if day <= today:
        stats = client.get_stats(day.isoformat())
        day_steps_list.append(stats.get("totalSteps", 0))
    else:
        day_steps_list.append(0)

weekly_steps = sum(day_steps_list)

output = {
    "weekly_steps": weekly_steps,
    "goal": 70000,
    "updated": today.isoformat(),
    "day_steps": day_steps_list
}

os.makedirs("data", exist_ok=True)
with open("data/steps.json", "w") as f:
    json.dump(output, f)

print(f"Synced: {weekly_steps} steps this week")
print(f"Daily breakdown: {day_steps_list}")
