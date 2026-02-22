"""Desktop notifications and audio alerts for prayer times."""

import threading

try:
    from plyer import notification as plyer_notification
    _PLYER_AVAILABLE = True
except ImportError:
    _PLYER_AVAILABLE = False

APP_NAME = "Prayer Time"
APP_ICON = ""  # Path to icon file; empty = default


def _send_plyer(title: str, message: str, timeout: int = 10) -> None:
    """Send a desktop notification via plyer (cross-platform)."""
    if not _PLYER_AVAILABLE:
        return
    try:
        kwargs = dict(
            app_name=APP_NAME,
            title=title,
            message=message,
            timeout=timeout,
        )
        if APP_ICON:
            kwargs["app_icon"] = APP_ICON
        plyer_notification.notify(**kwargs)
    except Exception:
        pass


def notify_reminder(prayer_display_name: str, minutes: int, callback=None) -> None:
    """
    Send a desktop notification for a prayer reminder N minutes before prayer time.
    Optionally calls callback() in the GUI thread.
    """
    title = f"🕌 {prayer_display_name} — {minutes} minutes"
    message = f"{prayer_display_name} prayer starts in {minutes} minutes. Prepare for prayer."
    _send_plyer(title, message, timeout=15)
    if callback:
        callback(title, message)


def notify_prayer_time(prayer_display_name: str, callback=None) -> None:
    """
    Send a desktop notification when prayer time arrives.
    Optionally calls callback() in the GUI thread.
    """
    title = f"🕌 {prayer_display_name} — Time to Pray!"
    message = f"It is now time for {prayer_display_name} prayer. Allahu Akbar!"
    _send_plyer(title, message, timeout=30)
    if callback:
        callback(title, message)


def schedule_reminders(
    prayer_name: str,
    prayer_display_name: str,
    seconds_until_prayer: int,
    gui_callback=None,
) -> list:
    """
    Schedule reminder notifications at 10 min and 5 min before prayer,
    and an alert exactly at prayer time.

    Returns list of Timer objects so they can be cancelled if needed.
    """
    timers = []

    for remind_minutes in (10, 5):
        delay = seconds_until_prayer - remind_minutes * 60
        if delay > 0:
            t = threading.Timer(
                delay,
                notify_reminder,
                args=(prayer_display_name, remind_minutes, gui_callback),
            )
            t.daemon = True
            t.start()
            timers.append(t)

    if seconds_until_prayer > 0:
        t = threading.Timer(
            seconds_until_prayer,
            notify_prayer_time,
            args=(prayer_display_name, gui_callback),
        )
        t.daemon = True
        t.start()
        timers.append(t)

    return timers
