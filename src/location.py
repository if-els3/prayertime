"""Location detection using IP geolocation and manual config."""

import json
import os

import requests


DEFAULT_LOCATION = {
    "city": "Jakarta",
    "region": "Jakarta",
    "country": "ID",
    "lat": -6.2088,
    "lon": 106.8456,
    "timezone": "Asia/Jakarta",
}

IPAPI_URL = "http://ip-api.com/json/"

CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".prayertime")
CONFIG_FILE = os.path.join(CONFIG_DIR, "location.json")


def get_location(timeout: int = 5) -> dict:
    """
    Detect current location via IP geolocation.

    Returns a dict with: city, region, country, lat, lon, timezone.
    Falls back to DEFAULT_LOCATION on failure.
    """
    try:
        resp = requests.get(
            IPAPI_URL,
            params={"fields": "city,regionName,country,lat,lon,timezone,status,message"},
            timeout=timeout,
        )
        resp.raise_for_status()
        data = resp.json()
        if data.get("status") == "success":
            return {
                "city": data.get("city", DEFAULT_LOCATION["city"]),
                "region": data.get("regionName", DEFAULT_LOCATION["region"]),
                "country": data.get("country", DEFAULT_LOCATION["country"]),
                "lat": float(data.get("lat", DEFAULT_LOCATION["lat"])),
                "lon": float(data.get("lon", DEFAULT_LOCATION["lon"])),
                "timezone": data.get("timezone", DEFAULT_LOCATION["timezone"]),
            }
    except Exception:
        pass
    return dict(DEFAULT_LOCATION)


def save_manual_location(location: dict) -> None:
    """Save a manually-set location to the config file."""
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(location, f, indent=2)


def load_manual_location() -> dict | None:
    """Load a previously saved manual location, or return None."""
    if not os.path.isfile(CONFIG_FILE):
        return None
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        required = ("city", "region", "country", "lat", "lon", "timezone")
        if all(k in data for k in required):
            return data
    except Exception:
        pass
    return None


def clear_manual_location() -> None:
    """Remove the saved manual location config."""
    if os.path.isfile(CONFIG_FILE):
        os.remove(CONFIG_FILE)
