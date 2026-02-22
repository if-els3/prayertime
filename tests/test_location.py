"""Tests for the location module."""

import unittest
from unittest.mock import MagicMock, patch

from src.location import DEFAULT_LOCATION, get_location


class TestGetLocation(unittest.TestCase):
    @patch("src.location.requests.get")
    def test_returns_location_on_success(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "status": "success",
            "city": "Jakarta",
            "regionName": "Jakarta",
            "country": "Indonesia",
            "lat": -6.2,
            "lon": 106.8,
            "timezone": "Asia/Jakarta",
        }
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        loc = get_location()
        self.assertEqual(loc["city"], "Jakarta")
        self.assertAlmostEqual(loc["lat"], -6.2)
        self.assertEqual(loc["timezone"], "Asia/Jakarta")

    @patch("src.location.requests.get")
    def test_falls_back_on_failure(self, mock_get):
        mock_get.side_effect = Exception("Network error")
        loc = get_location()
        self.assertEqual(loc["city"], DEFAULT_LOCATION["city"])

    @patch("src.location.requests.get")
    def test_falls_back_on_api_error_status(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"status": "fail", "message": "reserved range"}
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        loc = get_location()
        self.assertEqual(loc["city"], DEFAULT_LOCATION["city"])


if __name__ == "__main__":
    unittest.main()
