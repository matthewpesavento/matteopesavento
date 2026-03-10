import pandas as pd
import os
from openai import OpenAI

# ----------------------------
# CONFIG
# ----------------------------

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # make sure your key is set in terminal
CSV_FILE = "training_data.csv"

# ----------------------------
# DEFINE YOUR ZONES
# ----------------------------

# Example HR zones (beats per minute)
hr_zones = {
    "Zone 1": (60, 153),
    "Zone 2": (154, 173),
    "Zone 3": (174, 184),
    "Zone 4": (185, 193),
    "Zone 5": (194, 204)
}

# Example Power zones (watts)
power_zones = {
    "Recovery": (0, 130),
    "Easy": (131, 185),
    "Aerobic": (186, 260),
    "Threshold": (261, 330),
    "Anaerobic": (331, 900)
}

# Example pace zones (minutes/km)
pace_zones = {
    "Easy": (5.0, 10.0),
    "LT1": (4.25, 5.0),
    "LT2": (3.9, 4.25),
    "VO2Max": (2.5, 3.9)
}

# ----------------------------
# LOAD DATA
# ----------------------------

if not os.path.exists(CSV_FILE):
    print(f"{CSV_FILE} not found. Run pull_strava.py first.")
    exit()

df = pd.read_csv(CSV_FILE)

# ----------------------------
# PREPARE PROMPT
# ----------------------------

# convert dataframe to dict for GPT
activities = df.to_dict(orient="records")

prompt = f"""
You are a coach AI. Here are my workouts with HR, power, and distance/time:

{activities}

My zones are:

HR zones: {hr_zones}
Power zones: {power_zones}
Pace zones: {pace_zones}

Benchmark my workouts according to these zones and provide feedback.

If I want to become a top Age Group 70.3 triathlete for the 30-34 division, and I want to improve
speed overall, and within each discipline, provide me a week of training plan.
"""

# ----------------------------
# CALL GPT-5
# ----------------------------

client = OpenAI(api_key=OPENAI_API_KEY)

response = client.chat.completions.create(
    model="gpt-5",
    messages=[{"role": "user", "content": prompt}]
)

print(response.choices[0].message.content)
