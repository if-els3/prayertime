# 🕌 Prayer Time Desktop Widget

An Islamic pixel-art themed always-on-top desktop widget that shows your current location, Gregorian + Hijri date, daily prayer times, countdown to the next prayer, and special Ramadan Imsak/Iftar countdowns — with desktop reminders at 10 and 5 minutes before each prayer and an alarm at prayer time.

![Prayer Time Widget](https://github.com/user-attachments/assets/bbb051e4-d159-4334-8508-2e4424ae0e86)

---

## ✨ Features

| Feature | Details |
|---|---|
| 📍 Location | Auto-detected via IP geolocation (falls back to Jakarta) |
| 📅 Date | Gregorian **and** Hijri date displayed together |
| 🕌 Prayer times | Fajr, Sunrise, Dhuhr, Asr, Maghrib, Isha via [Aladhan API](https://aladhan.com) |
| ⏳ Countdown | Live countdown to the next prayer |
| 🌙 Ramadan | Dedicated Imsak (Fajr) & Iftar (Maghrib) countdowns |
| 🔔 Reminders | Desktop notifications **10 min** and **5 min** before each prayer |
| 🔊 Alarm | Desktop notification + system bell exactly at prayer time |
| 📌 Always on top | Window stays above other applications |
| 🖱️ Draggable | Drag the window anywhere on your screen |
| 🎨 Theme | Pixel-art Islamic aesthetic (dark green / gold palette) |
| 🚀 Autostart | Setup scripts for Linux and Windows startup |

---

## 🛠 Requirements

- Python 3.8+
- `tkinter` (usually bundled with Python; on Ubuntu: `sudo apt install python3-tk`)
- Internet connection (for location detection and prayer times)

---

## 📦 Installation

```bash
# 1. Clone the repository
git clone https://github.com/if-els3/prayertime.git
cd prayertime

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Run the app
python prayertime_app.py
```

---

## 🚀 Auto-start at Login

### Linux (GNOME / KDE / XFCE)

```bash
bash autostart/install-autostart-linux.sh
```

This creates a `.desktop` entry in `~/.config/autostart/` so the widget launches automatically at each login.

### Windows

Double-click `autostart/install-autostart-windows.bat` (or run as Administrator).
This adds a registry key under `HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Run`.

---

## 🗂 Project Structure

```
prayertime/
├── prayertime_app.py        # Main entry point — GUI application
├── requirements.txt
├── src/
│   ├── location.py          # IP-based geolocation
│   ├── prayer_api.py        # Aladhan API — prayer times & Hijri date
│   └── notifier.py          # Desktop notifications & reminder scheduling
├── tests/
│   ├── test_location.py
│   ├── test_prayer_api.py
│   └── test_notifier.py
└── autostart/
    ├── install-autostart-linux.sh
    └── install-autostart-windows.bat
```

---

## ⚙️ Configuration

Open `prayertime_app.py` and adjust the constants near the top:

| Constant | Default | Description |
|---|---|---|
| `WINDOW_W / WINDOW_H` | `480 × 720` | Widget size in pixels |
| `REFRESH_MS` | `1000` | Clock refresh interval (ms) |

Prayer calculation method (default `11` = Egyptian GAES) can be changed in `src/prayer_api.py`:

```python
DEFAULT_METHOD = 11  # see https://aladhan.com/prayer-times-api#GetTimings for codes
```

---

## 🧪 Running Tests

```bash
pip install pytest
python -m pytest tests/ -v
```

---

## 📜 Credits

- Prayer times API: [Aladhan.com](https://aladhan.com)
- Geolocation: [ip-api.com](https://ip-api.com)
- Inspired by [waktu-sholat](https://github.com/renomureza/waktu-sholat) and [ramadan-cli](https://github.com/ahmadawais/ramadan-cli)
