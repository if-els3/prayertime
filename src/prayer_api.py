"""Fetch prayer times and Hijri date from the Aladhan API."""

import datetime
import requests

ALADHAN_BASE = "https://api.aladhan.com/v1"

PRAYER_NAMES = ["Fajr", "Sunrise", "Dhuhr", "Asr", "Maghrib", "Isha"]
PRAYER_DISPLAY = {
    "Fajr": "Subuh / Fajr",
    "Sunrise": "Sunrise / Syuruq",
    "Dhuhr": "Dzuhur / Dhuhr",
    "Asr": "Ashar / Asr",
    "Maghrib": "Maghrib",
    "Isha": "Isya / Isha",
}

# Calculation method: 11 = Egyptian GAES (common in many countries)
# 2 = ISNA, 3 = MWL, 4 = Mecca, 5 = Karachi, 11 = Egypt, 15 = Dubai, 20 = Turkey
DEFAULT_METHOD = 11


def fetch_prayer_times(lat: float, lon: float, date: datetime.date = None, method: int = DEFAULT_METHOD) -> dict:
    """
    Fetch prayer times and Hijri date for given coordinates and date.

    Returns a dict with:
        timings: {prayer_name: "HH:MM"} for the six main prayers
        hijri: {day, month_name, year}  Hijri date components
        gregorian: {date_str}
    Raises requests.RequestException or ValueError on failure.
    """
    if date is None:
        date = datetime.date.today()
    date_str = date.strftime("%d-%m-%Y")
    url = f"{ALADHAN_BASE}/timings/{date_str}"
    params = {
        "latitude": lat,
        "longitude": lon,
        "method": method,
    }
    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    body = resp.json()
    if body.get("code") != 200:
        raise ValueError(f"Aladhan API error: {body.get('status')}")

    data = body["data"]
    raw_timings = data["timings"]

    # Keep only the six main prayer times (strip seconds if present)
    timings = {}
    for name in PRAYER_NAMES:
        raw = raw_timings.get(name, "00:00")
        timings[name] = raw[:5]  # "HH:MM"

    hijri_data = data["date"]["hijri"]
    hijri = {
        "day": hijri_data["day"],
        "month_name": hijri_data["month"]["en"],
        "month_ar": hijri_data["month"]["ar"],
        "year": hijri_data["year"],
    }

    greg_data = data["date"]["gregorian"]
    gregorian = {
        "date_str": greg_data.get("date", date.strftime("%d-%m-%Y")),
        "weekday": greg_data.get("weekday", {}).get("en", ""),
    }

    return {"timings": timings, "hijri": hijri, "gregorian": gregorian}


def time_str_to_today_dt(time_str: str, tz=None) -> datetime.datetime:
    """
    Convert 'HH:MM' string to a timezone-aware datetime for today.
    If tz is None, returns naive datetime.
    """
    now = datetime.datetime.now(tz) if tz else datetime.datetime.now()
    hour, minute = map(int, time_str.split(":"))
    dt = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    return dt


def get_next_prayer(timings: dict, now: datetime.datetime, tz=None) -> tuple:
    """
    Given a timings dict and current datetime, return (prayer_name, prayer_datetime)
    of the next upcoming prayer. Returns (None, None) if all prayers passed.
    """
    for name in PRAYER_NAMES:
        if name == "Sunrise":
            continue  # Sunrise is not a prayer time for reminders
        prayer_dt = time_str_to_today_dt(timings[name], tz)
        if prayer_dt > now:
            return name, prayer_dt
    return None, None


def seconds_until(target_dt: datetime.datetime, now: datetime.datetime = None) -> int:
    """Return seconds from now until target_dt (can be negative if past)."""
    if now is None:
        now = datetime.datetime.now(target_dt.tzinfo)
    delta = target_dt - now
    return int(delta.total_seconds())
