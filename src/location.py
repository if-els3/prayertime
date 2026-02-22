"""Location detection using IP geolocation."""

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
