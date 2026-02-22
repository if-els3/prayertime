"""Tests for the prayer_api module."""

import datetime
import unittest
from unittest.mock import MagicMock, patch

import pytz

from src.prayer_api import (
    PRAYER_NAMES,
    fetch_prayer_times,
    get_next_prayer,
    seconds_until,
    time_str_to_today_dt,
)

MOCK_RESPONSE = {
    "code": 200,
    "status": "OK",
    "data": {
        "timings": {
            "Fajr": "04:30",
            "Sunrise": "05:55",
            "Dhuhr": "12:00",
            "Asr": "15:30",
            "Maghrib": "18:15",
            "Isha": "19:30",
            "Midnight": "00:00",
            "Imsak": "04:20",
        },
        "date": {
            "gregorian": {
                "date": "01-03-2025",
                "weekday": {"en": "Saturday"},
            },
            "hijri": {
                "day": "1",
                "month": {"en": "Ramadan", "ar": "رَمَضان"},
                "year": "1446",
            },
        },
    },
}


class TestFetchPrayerTimes(unittest.TestCase):
    @patch("src.prayer_api.requests.get")
    def test_returns_timings_and_hijri(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = MOCK_RESPONSE
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        result = fetch_prayer_times(-6.2, 106.8, datetime.date(2025, 3, 1))

        self.assertEqual(result["timings"]["Fajr"], "04:30")
        self.assertEqual(result["timings"]["Maghrib"], "18:15")
        self.assertEqual(result["hijri"]["month_name"], "Ramadan")
        self.assertEqual(result["hijri"]["year"], "1446")

    @patch("src.prayer_api.requests.get")
    def test_strips_seconds_from_time(self, mock_get):
        import copy
        response = copy.deepcopy(MOCK_RESPONSE)
        response["data"]["timings"]["Fajr"] = "04:30 (PKT)"
        mock_resp = MagicMock()
        mock_resp.json.return_value = response
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        result = fetch_prayer_times(-6.2, 106.8)
        self.assertEqual(len(result["timings"]["Fajr"]), 5)

    @patch("src.prayer_api.requests.get")
    def test_raises_on_api_error(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"code": 400, "status": "Bad Request"}
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        with self.assertRaises(ValueError):
            fetch_prayer_times(-6.2, 106.8)


class TestTimeStrToDt(unittest.TestCase):
    def test_converts_to_datetime(self):
        tz = pytz.timezone("Asia/Jakarta")
        dt = time_str_to_today_dt("12:00", tz)
        self.assertEqual(dt.hour, 12)
        self.assertEqual(dt.minute, 0)

    def test_naive_without_tz(self):
        dt = time_str_to_today_dt("18:15")
        self.assertEqual(dt.hour, 18)
        self.assertIsNone(dt.tzinfo)


class TestGetNextPrayer(unittest.TestCase):
    def test_returns_next_prayer(self):
        tz = pytz.utc
        timings = {
            "Fajr": "04:00",
            "Sunrise": "05:30",
            "Dhuhr": "12:00",
            "Asr": "15:30",
            "Maghrib": "18:00",
            "Isha": "19:30",
        }
        now = datetime.datetime.now(tz).replace(hour=12, minute=5, second=0, microsecond=0)
        name, dt = get_next_prayer(timings, now, tz)
        self.assertEqual(name, "Asr")

    def test_skips_sunrise(self):
        tz = pytz.utc
        timings = {
            "Fajr": "04:00",
            "Sunrise": "05:30",
            "Dhuhr": "12:00",
            "Asr": "15:30",
            "Maghrib": "18:00",
            "Isha": "19:30",
        }
        now = datetime.datetime.now(tz).replace(hour=4, minute=30, second=0, microsecond=0)
        name, dt = get_next_prayer(timings, now, tz)
        self.assertNotEqual(name, "Sunrise")

    def test_returns_none_after_isha(self):
        tz = pytz.utc
        timings = {
            "Fajr": "04:00",
            "Sunrise": "05:30",
            "Dhuhr": "12:00",
            "Asr": "15:30",
            "Maghrib": "18:00",
            "Isha": "19:30",
        }
        now = datetime.datetime.now(tz).replace(hour=23, minute=0, second=0, microsecond=0)
        name, dt = get_next_prayer(timings, now, tz)
        self.assertIsNone(name)


class TestSecondsUntil(unittest.TestCase):
    def test_positive_seconds(self):
        tz = pytz.utc
        now = datetime.datetime.now(tz).replace(hour=10, minute=0, second=0, microsecond=0)
        target = now + datetime.timedelta(seconds=300)
        self.assertEqual(seconds_until(target, now), 300)

    def test_negative_seconds_for_past(self):
        tz = pytz.utc
        now = datetime.datetime.now(tz).replace(hour=10, minute=0, second=0, microsecond=0)
        target = now - datetime.timedelta(seconds=60)
        self.assertLess(seconds_until(target, now), 0)


if __name__ == "__main__":
    unittest.main()
