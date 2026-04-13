import os, sys, time, json, requests
from datetime import datetime, timezone, timedelta

# ----------------------------
# CONFIG
# ----------------------------

FTP_WATTS        = 280    # your current bike FTP in watts
THRESHOLD_PACE   = 4.5    # run threshold pace in min/km (e.g. 4.5 = 4:30/km)
LOOKBACK_DAYS    = 60     # how many days back to fetch on each run

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
# HELPERS
# ----------------------------

def api_get(url, params=None):
    while True:
        try:
            r = requests.get(url, headers=headers, params=params, timeout=30)
        except requests.exceptions.RequestException as e:
            print(f"Network error, retrying in 10s: {e}")
            time.sleep(10)
            continue
        if r.status_code == 429:
            print("Rate limit hit. Sleeping 15 minutes...")
            time.sleep(900)
            continue
        if r.status_code == 401:
            print("Authorization failed.")
            sys.exit(1)
        if r.status_code != 200:
            print(f"API error {r.status_code}: {r.text}")
            return None
        return r.json()

def calc_tss(detail):
    sport        = detail.get("sport_type", "")
    moving_time  = detail.get("moving_time", 0)

    # Bike: power-based TSS
    if sport in ("Ride", "VirtualRide", "GravelRide", "EBikeRide"):
        np = detail.get("weighted_average_watts")
        if np and FTP_WATTS:
            intensity_factor = np / FTP_WATTS
            tss = (moving_time * np * intensity_factor) / (FTP_WATTS * 3600) * 100
            return round(tss, 1), "power"

    # Run: rTSS pace-based
    if sport in ("Run", "TrailRun", "VirtualRun"):
        distance_m = detail.get("distance", 0)
        if distance_m and moving_time and THRESHOLD_PACE:
            pace_min_km = (moving_time / 60) / (distance_m / 1000)
            threshold_time_min = (distance_m / 1000) * THRESHOLD_PACE
            rtss = (moving_time / 60) / threshold_time_min * 100 * (moving_time / 3600)
            return round(rtss, 1), "pace"

    # Fallback: suffer score estimate
    suffer = detail.get("suffer_score")
    if suffer:
        return round(suffer * 2, 1), "hr_estimate"

    return None, None

# ----------------------------
# LOAD EXISTING DATA
# ----------------------------

os.makedirs("data/streams", exist_ok=True)

existing_file = "data/strava.json"
if os.path.exists(existing_file):
    with open(existing_file) as f:
        existing_data = json.load(f)
    existing_activities = existing_data.get("activities", [])
    existing_ids = {a["id"] for a in existing_activities}
    print(f"Existing activities loaded: {len(existing_ids)}")
else:
    existing_activities = []
    existing_ids = set()
    print("No existing data. Starting fresh.")

# ----------------------------
# BACKFILL TSS ON EXISTING RECORDS
# ----------------------------
updated = False
for a in existing_activities:
    if a.get("tss") is not None:
        continue  # already has TSS, skip

    # Build a fake detail dict from what we have
    fake = {
        "sport_type":             a.get("sport_type") or a.get("type"),
        "moving_time":            a.get("moving_time_sec") or a.get("moving_time_s"),
        "distance":               a.get("distance_m"),
        "weighted_average_watts": a.get("weighted_power"),
        "average_watts":          a.get("avg_watts") or a.get("avg_power"),
        "suffer_score":           a.get("suffer_score"),
    }
    tss_value, tss_method = calc_tss(fake)
    if tss_value is not None:
        a["tss"]        = tss_value
        a["tss_method"] = tss_method
        a["ftp_used"]   = FTP_WATTS
        a["threshold_pace_used"] = THRESHOLD_PACE
        updated = True

if updated:
    print("Backfilled TSS on existing simplified records.")

# ----------------------------
# FETCH RECENT ACTIVITIES
# ----------------------------

after_timestamp = int((datetime.now(timezone.utc) - timedelta(days=LOOKBACK_DAYS)).timestamp())
new_activities = []
page = 1

while True:
    data = api_get(
        "https://www.strava.com/api/v3/athlete/activities",
        params={"per_page": 100, "page": page, "after": after_timestamp}
    )

    if not isinstance(data, list) or len(data) == 0:
        break

    new_this_page = 0

    for a in data:
        activity_id = a["id"]

        if activity_id in existing_ids:
            continue

        print(f"Fetching detail for activity {activity_id}...")

        # Detailed activity
        detail = api_get(f"https://www.strava.com/api/v3/activities/{activity_id}")
        if not detail:
            continue

        # Streams
        streams_data = api_get(
            f"https://www.strava.com/api/v3/activities/{activity_id}/streams",
            params={"keys": ",".join(STREAM_KEYS), "key_by_type": "true"}
        )

        if streams_data:
            try:
                streams_out = {}
                max_len = max((len(v["data"]) for v in streams_data.values()), default=0)
                for key in STREAM_KEYS:
                    if key in streams_data:
                        streams_out[key] = streams_data[key]["data"]
                    else:
                        streams_out[key] = [None] * max_len
                with open(f"data/streams/{activity_id}.json", "w") as f:
                    json.dump(streams_out, f)
            except Exception as e:
                print(f"Stream save error for {activity_id}: {e}")

        tss_value, tss_method = calc_tss(detail)

        new_activities.append({
            # IDs
            "id":                       activity_id,
            "external_id":              detail.get("external_id"),
            "upload_id":                detail.get("upload_id"),

            # title + description
            "title":                    detail.get("name"),
            "description":              detail.get("description"),

            # sport
            "type":                     detail.get("type"),
            "sport_type":               detail.get("sport_type"),
            "workout_type":             detail.get("workout_type"),

            # dates
            "start_date":               detail.get("start_date"),
            "start_date_local":         detail.get("start_date_local"),
            "timezone":                 detail.get("timezone"),

            # distance + time
            "distance_m":               detail.get("distance"),
            "moving_time_sec":          detail.get("moving_time"),
            "elapsed_time_sec":         detail.get("elapsed_time"),

            # elevation
            "total_elevation_gain_m":   detail.get("total_elevation_gain"),
            "elev_high":                detail.get("elev_high"),
            "elev_low":                 detail.get("elev_low"),

            # speed
            "avg_speed_ms":             detail.get("average_speed"),
            "max_speed_ms":             detail.get("max_speed"),

            # heart rate
            "has_hr":                   detail.get("has_heartrate"),
            "avg_hr":                   detail.get("average_heartrate"),
            "max_hr":                   detail.get("max_heartrate"),

            # power
            "device_watts":             detail.get("device_watts"),
            "avg_power":                detail.get("average_watts"),
            "max_power":                detail.get("max_watts"),
            "weighted_power":           detail.get("weighted_average_watts"),
            "kilojoules":               detail.get("kilojoules"),

            # cadence
            "avg_cadence":              detail.get("average_cadence"),

            # temp
            "avg_temp":                 detail.get("average_temp"),

            # calories
            "calories":                 detail.get("calories"),

            # suffer score
            "suffer_score":             detail.get("suffer_score"),

            # training load
            "tss":                      tss_value,
            "tss_method":               tss_method,
            "ftp_used":                 FTP_WATTS,
            "threshold_pace_used":      THRESHOLD_PACE,

            # flags
            "trainer":                  detail.get("trainer"),
            "commute":                  detail.get("commute"),
            "manual":                   detail.get("manual"),
            "private":                  detail.get("private"),

            # gear
            "gear_id":                  detail.get("gear_id"),

            # social
            "kudos_count":              detail.get("kudos_count"),
            "comment_count":            detail.get("comment_count"),
            "achievement_count":        detail.get("achievement_count"),
            "athlete_count":            detail.get("athlete_count"),
            "photo_count":              detail.get("photo_count"),

            # gps
            "start_latlng":             detail.get("start_latlng"),
            "end_latlng":               detail.get("end_latlng"),

            # misc
            "visibility":               detail.get("visibility"),
            "flagged":                  detail.get("flagged"),
            "has_streams":              streams_data is not None,
        })

        new_this_page += 1
        time.sleep(1)

    print(f"Page {page} — new activities: {new_this_page}")
    page += 1

# ----------------------------
# MERGE + SAVE
# ----------------------------

all_activities = existing_activities + new_activities

# Sort by date descending
all_activities.sort(key=lambda a: a.get("start_date", ""), reverse=True)

with open("data/strava.json", "w") as f:
    json.dump({
        "updated_at":       datetime.now(timezone.utc).isoformat(),
        "ftp":              FTP_WATTS,
        "threshold_pace":   THRESHOLD_PACE,
        "activity_count":   len(all_activities),
        "activities":       all_activities,
    }, f, indent=2)

print(f"\nDone. New: {len(new_activities)} | Total: {len(all_activities)}")
