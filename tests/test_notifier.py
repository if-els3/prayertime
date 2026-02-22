"""Tests for the notifier module."""

import unittest
from unittest.mock import MagicMock, patch

from src.notifier import notify_prayer_time, notify_reminder, schedule_reminders


class TestNotifyReminder(unittest.TestCase):
    @patch("src.notifier._send_plyer")
    def test_calls_send_plyer(self, mock_plyer):
        notify_reminder("Subuh / Fajr", 10)
        mock_plyer.assert_called_once()
        args = mock_plyer.call_args[0]
        self.assertIn("10", args[0])
        self.assertIn("Subuh", args[0])

    @patch("src.notifier._send_plyer")
    def test_calls_callback(self, mock_plyer):
        cb = MagicMock()
        notify_reminder("Maghrib", 5, callback=cb)
        cb.assert_called_once()


class TestNotifyPrayerTime(unittest.TestCase):
    @patch("src.notifier._send_plyer")
    def test_calls_send_plyer(self, mock_plyer):
        notify_prayer_time("Maghrib")
        mock_plyer.assert_called_once()
        args = mock_plyer.call_args[0]
        self.assertIn("Maghrib", args[0])
        self.assertIn("Time to Pray", args[0])


class TestScheduleReminders(unittest.TestCase):
    def test_no_timers_for_past_prayer(self):
        timers = schedule_reminders("Fajr", "Subuh / Fajr", -100)
        self.assertEqual(len(timers), 0)

    def test_only_alarm_timer_when_less_than_5_min(self):
        # 200 seconds until prayer — only the "at prayer" timer, not 5-min or 10-min
        with patch("src.notifier.threading.Timer") as mock_timer_cls:
            mock_timer = MagicMock()
            mock_timer_cls.return_value = mock_timer
            timers = schedule_reminders("Fajr", "Subuh / Fajr", 200)
            # Only 1 timer: the exact-time alarm
            self.assertEqual(len(timers), 1)

    def test_all_three_timers_for_future_prayer(self):
        # 700 seconds = 11+ minutes — should get 5-min, 10-min NOT met, and alarm
        # Actually 700s = ~11.6 min, so 10-min reminder at -300s delay (700-600=100s) ✓
        with patch("src.notifier.threading.Timer") as mock_timer_cls:
            mock_timer = MagicMock()
            mock_timer_cls.return_value = mock_timer
            timers = schedule_reminders("Maghrib", "Maghrib", 700)
            # 700-600=100 (10-min reminder) ✓, 700-300=400 (5-min reminder) ✓, alarm ✓
            self.assertEqual(len(timers), 3)


if __name__ == "__main__":
    unittest.main()
