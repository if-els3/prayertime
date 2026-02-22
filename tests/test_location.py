"""Tests for the location module."""

import json
import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from src.location import (
    DEFAULT_LOCATION,
    clear_manual_location,
    get_location,
    load_manual_location,
    save_manual_location,
)


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


class TestManualLocation(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()
        self._orig_config_dir = __import__("src.location", fromlist=["CONFIG_DIR"]).CONFIG_DIR
        self._orig_config_file = __import__("src.location", fromlist=["CONFIG_FILE"]).CONFIG_FILE
        import src.location as loc_mod
        loc_mod.CONFIG_DIR = self._tmpdir
        loc_mod.CONFIG_FILE = os.path.join(self._tmpdir, "location.json")

    def tearDown(self):
        import src.location as loc_mod
        loc_mod.CONFIG_DIR = self._orig_config_dir
        loc_mod.CONFIG_FILE = self._orig_config_file
        import shutil
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def test_save_and_load_manual_location(self):
        loc = {
            "city": "Ciseeng",
            "region": "Bogor",
            "country": "ID",
            "lat": -6.5567,
            "lon": 106.5614,
            "timezone": "Asia/Jakarta",
        }
        save_manual_location(loc)
        loaded = load_manual_location()
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded["city"], "Ciseeng")
        self.assertAlmostEqual(loaded["lat"], -6.5567)

    def test_load_returns_none_when_no_file(self):
        result = load_manual_location()
        self.assertIsNone(result)

    def test_clear_manual_location(self):
        loc = {
            "city": "Test", "region": "Test", "country": "ID",
            "lat": 0.0, "lon": 0.0, "timezone": "UTC",
        }
        save_manual_location(loc)
        self.assertIsNotNone(load_manual_location())
        clear_manual_location()
        self.assertIsNone(load_manual_location())

    def test_load_returns_none_for_invalid_json(self):
        import src.location as loc_mod
        with open(loc_mod.CONFIG_FILE, "w") as f:
            f.write("not valid json")
        result = load_manual_location()
        self.assertIsNone(result)

    def test_load_returns_none_for_missing_keys(self):
        import src.location as loc_mod
        with open(loc_mod.CONFIG_FILE, "w") as f:
            json.dump({"city": "Test"}, f)
        result = load_manual_location()
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
