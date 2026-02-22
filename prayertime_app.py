#!/usr/bin/env python3
"""
Prayer Time Desktop Widget
Islamic pixel-art themed always-on-top window showing:
  - Current location and date (Gregorian + Hijri)
  - Daily prayer times
  - Countdown to next prayer (with Fajr/Maghrib highlighted for Ramadan)
  - Desktop reminders at 10 and 5 minutes before each prayer
  - Alarm notification at each prayer time
"""

import datetime
import threading
import time
import tkinter as tk
from tkinter import messagebox

import pytz

from src.location import get_location
from src.prayer_api import (
    PRAYER_DISPLAY,
    PRAYER_NAMES,
    fetch_prayer_times,
    seconds_until,
    time_str_to_today_dt,
)
from src.notifier import schedule_reminders

# ──────────────────────────────────────────────────────────────────────────────
# Theme constants — pixel-art Islamic palette
# ──────────────────────────────────────────────────────────────────────────────
BG_DARK = "#0d1117"          # near-black background
BG_CARD = "#161b22"          # slightly lighter card
BG_HIGHLIGHT = "#1a3a2a"     # deep Islamic green for highlighted row
BORDER_COLOR = "#2ea043"     # Islamic green border
ACCENT_GOLD = "#f0c040"      # gold accents
ACCENT_GREEN = "#3fb950"     # bright green
TEXT_WHITE = "#e6edf3"       # off-white text
TEXT_DIM = "#8b949e"         # dimmed text
TEXT_GOLD = "#f0c040"        # gold text
TEXT_RED = "#ff6b6b"         # warning red
TEXT_FAJR = "#7ec8e3"        # light blue for Fajr
TEXT_MAGHRIB = "#ffa07a"     # orange-red for Maghrib

FONT_PIXEL = ("Courier", 10, "bold")      # pixel-ish font
FONT_PIXEL_SM = ("Courier", 8)
FONT_PIXEL_LG = ("Courier", 14, "bold")
FONT_PIXEL_XL = ("Courier", 18, "bold")
FONT_TITLE = ("Courier", 12, "bold")
FONT_CLOCK = ("Courier", 22, "bold")
FONT_ARABIC = ("Arial", 16, "bold")       # for Arabic/bismillah

WINDOW_W = 480
WINDOW_H = 720

REFRESH_MS = 1000  # update UI every second

# ──────────────────────────────────────────────────────────────────────────────
# Helper: pixel-art decorative lines
# ──────────────────────────────────────────────────────────────────────────────
PIXEL_BORDER_H = "▀" * 52
PIXEL_BORDER_B = "▄" * 52
MOSQUE_ART = (
    "    ▄▄▄        ▄▄▄       ▄▄▄    ",
    "   █▄▄▄█  ▄▄▄  █▄▄▄█  ▄  █▄▄▄█  ",
    "  ▄██▄██▄█████▄██▄██▄███▄██▄██▄ ",
    "  ████████████████████████████  ",
    " ▄████████████████████████████▄ ",
    " █████████████████████████████  ",
)


def _fmt_countdown(seconds: int) -> str:
    """Format seconds into HH:MM:SS countdown string."""
    if seconds < 0:
        return "00:00:00"
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:02d}"


# ──────────────────────────────────────────────────────────────────────────────
# Main App
# ──────────────────────────────────────────────────────────────────────────────
class PrayerTimeApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self._drag_x = 0
        self._drag_y = 0

        self.location = {}
        self.tz = None
        self.timings = {}
        self.hijri = {}
        self.gregorian = {}
        self.active_timers: list = []
        self._load_error = ""
        self._loading = True
        self._next_prayer_name = None
        self._next_prayer_dt = None
        self._reminder_scheduled_for: set = set()  # tracks which prayers got reminders

        self._setup_window()
        self._build_ui()
        self._start_data_load()

    # ──────────────────────────────────────────────────────────────────────
    # Window setup
    # ──────────────────────────────────────────────────────────────────────
    def _setup_window(self):
        root = self.root
        root.title("Prayer Time")
        root.geometry(f"{WINDOW_W}x{WINDOW_H}")
        root.configure(bg=BG_DARK)
        root.resizable(False, False)
        root.overrideredirect(True)        # remove OS title bar
        root.attributes("-topmost", True)  # always on top
        root.attributes("-alpha", 0.97)

        # Center on screen
        screen_w = root.winfo_screenwidth()
        screen_h = root.winfo_screenheight()
        x = screen_w - WINDOW_W - 40
        y = (screen_h - WINDOW_H) // 2
        root.geometry(f"{WINDOW_W}x{WINDOW_H}+{x}+{y}")

        # Drag support
        root.bind("<ButtonPress-1>", self._on_drag_start)
        root.bind("<B1-Motion>", self._on_drag_motion)

    def _on_drag_start(self, event):
        self._drag_x = event.x_root - self.root.winfo_x()
        self._drag_y = event.y_root - self.root.winfo_y()

    def _on_drag_motion(self, event):
        self.root.geometry(f"+{event.x_root - self._drag_x}+{event.y_root - self._drag_y}")

    # ──────────────────────────────────────────────────────────────────────
    # UI construction
    # ──────────────────────────────────────────────────────────────────────
    def _build_ui(self):
        root = self.root

        # ── outer border frame ───────────────────────────────────────────
        outer = tk.Frame(root, bg=BORDER_COLOR, bd=0)
        outer.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        inner = tk.Frame(outer, bg=BG_DARK, bd=0)
        inner.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)

        # ── title bar (drag zone + close) ────────────────────────────────
        title_bar = tk.Frame(inner, bg=BG_CARD, height=32)
        title_bar.pack(fill=tk.X, side=tk.TOP)
        title_bar.pack_propagate(False)

        tk.Label(
            title_bar,
            text="  🕌  PRAYER TIME  ◆  مواقيت الصلاة  ",
            font=FONT_PIXEL,
            fg=ACCENT_GOLD,
            bg=BG_CARD,
        ).pack(side=tk.LEFT, padx=6)

        tk.Button(
            title_bar,
            text=" ✕ ",
            font=FONT_PIXEL_SM,
            fg=TEXT_RED,
            bg=BG_CARD,
            activeforeground=TEXT_WHITE,
            activebackground="#3a1a1a",
            bd=0,
            cursor="hand2",
            command=self.root.destroy,
        ).pack(side=tk.RIGHT, padx=4, pady=4)

        # ── top green pixel border ────────────────────────────────────────
        tk.Label(
            inner,
            text=PIXEL_BORDER_H,
            font=("Courier", 6),
            fg=BORDER_COLOR,
            bg=BG_DARK,
        ).pack(fill=tk.X)

        # ── Bismillah banner ──────────────────────────────────────────────
        tk.Label(
            inner,
            text="بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيْمِ",
            font=FONT_ARABIC,
            fg=ACCENT_GOLD,
            bg=BG_DARK,
            pady=4,
        ).pack(fill=tk.X)

        # ── pixel mosque art ──────────────────────────────────────────────
        mosque_frame = tk.Frame(inner, bg=BG_DARK)
        mosque_frame.pack()
        for line in MOSQUE_ART:
            tk.Label(
                mosque_frame,
                text=line,
                font=("Courier", 7),
                fg=ACCENT_GREEN,
                bg=BG_DARK,
            ).pack()

        # ── location label ────────────────────────────────────────────────
        self.lbl_location = tk.Label(
            inner,
            text="📍 Detecting location…",
            font=FONT_PIXEL,
            fg=TEXT_DIM,
            bg=BG_DARK,
        )
        self.lbl_location.pack(pady=(6, 0))

        # ── Gregorian date ────────────────────────────────────────────────
        self.lbl_date = tk.Label(
            inner,
            text="",
            font=FONT_PIXEL,
            fg=TEXT_WHITE,
            bg=BG_DARK,
        )
        self.lbl_date.pack()

        # ── Hijri date ────────────────────────────────────────────────────
        self.lbl_hijri = tk.Label(
            inner,
            text="",
            font=FONT_PIXEL,
            fg=ACCENT_GOLD,
            bg=BG_DARK,
        )
        self.lbl_hijri.pack()

        # ── live clock ────────────────────────────────────────────────────
        self.lbl_clock = tk.Label(
            inner,
            text="00:00:00",
            font=FONT_CLOCK,
            fg=ACCENT_GOLD,
            bg=BG_DARK,
            pady=4,
        )
        self.lbl_clock.pack()

        # ── pixel divider ─────────────────────────────────────────────────
        tk.Label(
            inner,
            text="◇ ─────────────────────────── ◇",
            font=("Courier", 9),
            fg=BORDER_COLOR,
            bg=BG_DARK,
        ).pack(pady=2)

        # ── prayer times grid ─────────────────────────────────────────────
        self.prayer_frame = tk.Frame(inner, bg=BG_DARK)
        self.prayer_frame.pack(fill=tk.X, padx=10, pady=4)

        self.prayer_rows: dict = {}   # prayer_name -> dict of label widgets
        self._build_prayer_rows()

        # ── pixel divider ─────────────────────────────────────────────────
        tk.Label(
            inner,
            text="◇ ─────────────────────────── ◇",
            font=("Courier", 9),
            fg=BORDER_COLOR,
            bg=BG_DARK,
        ).pack(pady=2)

        # ── next prayer countdown ─────────────────────────────────────────
        tk.Label(
            inner,
            text="NEXT PRAYER",
            font=FONT_PIXEL,
            fg=TEXT_DIM,
            bg=BG_DARK,
        ).pack()

        self.lbl_next_name = tk.Label(
            inner,
            text="—",
            font=FONT_PIXEL_LG,
            fg=ACCENT_GREEN,
            bg=BG_DARK,
        )
        self.lbl_next_name.pack()

        self.lbl_countdown = tk.Label(
            inner,
            text="--:--:--",
            font=FONT_CLOCK,
            fg=ACCENT_GOLD,
            bg=BG_DARK,
        )
        self.lbl_countdown.pack()

        # ── Fajr / Maghrib highlight block (Ramadan info) ─────────────────
        ram_frame = tk.Frame(inner, bg=BG_HIGHLIGHT, bd=1, relief=tk.RIDGE)
        ram_frame.pack(fill=tk.X, padx=14, pady=8)

        tk.Label(
            ram_frame,
            text="🌙  RAMADAN  — IMSAK & IFTAR",
            font=FONT_PIXEL,
            fg=ACCENT_GOLD,
            bg=BG_HIGHLIGHT,
            pady=4,
        ).pack()

        row1 = tk.Frame(ram_frame, bg=BG_HIGHLIGHT)
        row1.pack(fill=tk.X, padx=8, pady=2)

        # Fajr remaining
        tk.Label(row1, text="Imsak (Fajr)", font=FONT_PIXEL_SM, fg=TEXT_FAJR, bg=BG_HIGHLIGHT).pack(side=tk.LEFT)
        self.lbl_fajr_remain = tk.Label(row1, text="--:--:--", font=FONT_PIXEL, fg=TEXT_FAJR, bg=BG_HIGHLIGHT)
        self.lbl_fajr_remain.pack(side=tk.RIGHT)

        row2 = tk.Frame(ram_frame, bg=BG_HIGHLIGHT)
        row2.pack(fill=tk.X, padx=8, pady=2)

        # Maghrib remaining
        tk.Label(row2, text="Iftar (Maghrib)", font=FONT_PIXEL_SM, fg=TEXT_MAGHRIB, bg=BG_HIGHLIGHT).pack(side=tk.LEFT)
        self.lbl_maghrib_remain = tk.Label(row2, text="--:--:--", font=FONT_PIXEL, fg=TEXT_MAGHRIB, bg=BG_HIGHLIGHT)
        self.lbl_maghrib_remain.pack(side=tk.RIGHT)

        # ── notification banner (hidden by default) ───────────────────────
        self.notif_frame = tk.Frame(inner, bg="#2d1b00", bd=1, relief=tk.RIDGE)
        self.lbl_notif_title = tk.Label(
            self.notif_frame,
            text="",
            font=FONT_PIXEL,
            fg=ACCENT_GOLD,
            bg="#2d1b00",
        )
        self.lbl_notif_title.pack(pady=2)
        self.lbl_notif_msg = tk.Label(
            self.notif_frame,
            text="",
            font=FONT_PIXEL_SM,
            fg=TEXT_WHITE,
            bg="#2d1b00",
            wraplength=440,
        )
        self.lbl_notif_msg.pack(pady=(0, 4))
        # don't pack yet – show only when notification fires

        # ── bottom pixel border ───────────────────────────────────────────
        tk.Label(
            inner,
            text=PIXEL_BORDER_B,
            font=("Courier", 6),
            fg=BORDER_COLOR,
            bg=BG_DARK,
        ).pack(fill=tk.X, side=tk.BOTTOM)

    def _build_prayer_rows(self):
        """Create labelled rows in the prayer grid for each prayer."""
        header = tk.Frame(self.prayer_frame, bg=BG_CARD)
        header.pack(fill=tk.X, pady=(0, 2))
        tk.Label(header, text="Prayer", font=FONT_PIXEL, fg=TEXT_DIM, bg=BG_CARD, width=22, anchor="w").pack(side=tk.LEFT, padx=4)
        tk.Label(header, text="Time", font=FONT_PIXEL, fg=TEXT_DIM, bg=BG_CARD, width=10, anchor="e").pack(side=tk.RIGHT, padx=4)

        for name in PRAYER_NAMES:
            is_fajr = name == "Fajr"
            is_maghrib = name == "Maghrib"
            if is_fajr:
                row_bg = "#0a1a2a"
                fg = TEXT_FAJR
            elif is_maghrib:
                row_bg = "#1a0a0a"
                fg = TEXT_MAGHRIB
            else:
                row_bg = BG_CARD
                fg = TEXT_WHITE

            row = tk.Frame(self.prayer_frame, bg=row_bg, pady=2)
            row.pack(fill=tk.X, pady=1)

            # icon
            icon = "🌙" if is_fajr else ("🌅" if name == "Sunrise" else ("🌇" if is_maghrib else "☀️"))
            lbl_name = tk.Label(
                row,
                text=f" {icon}  {PRAYER_DISPLAY[name]}",
                font=FONT_PIXEL,
                fg=fg,
                bg=row_bg,
                anchor="w",
                width=26,
            )
            lbl_name.pack(side=tk.LEFT, padx=4)

            lbl_time = tk.Label(
                row,
                text="--:--",
                font=FONT_PIXEL_LG,
                fg=fg,
                bg=row_bg,
                anchor="e",
                width=8,
            )
            lbl_time.pack(side=tk.RIGHT, padx=4)

            self.prayer_rows[name] = {
                "row": row,
                "lbl_name": lbl_name,
                "lbl_time": lbl_time,
                "bg": row_bg,
                "fg": fg,
            }

    # ──────────────────────────────────────────────────────────────────────
    # Data loading (runs in background thread)
    # ──────────────────────────────────────────────────────────────────────
    def _start_data_load(self):
        t = threading.Thread(target=self._load_data, daemon=True)
        t.start()
        self._tick()  # start the clock immediately

    def _load_data(self):
        """Fetch location + prayer times in background thread."""
        try:
            self.location = get_location()
            try:
                self.tz = pytz.timezone(self.location["timezone"])
            except Exception:
                self.tz = pytz.utc

            today = datetime.datetime.now(self.tz).date()
            result = fetch_prayer_times(self.location["lat"], self.location["lon"], today)
            self.timings = result["timings"]
            self.hijri = result["hijri"]
            self.gregorian = result["gregorian"]

            self.root.after(0, self._on_data_loaded)
        except Exception as exc:
            self._load_error = str(exc)
            self.root.after(0, self._on_data_error)

    def _on_data_loaded(self):
        """Called in main thread once data is ready."""
        self._loading = False
        loc = self.location
        self.lbl_location.config(
            text=f"📍 {loc['city']}, {loc['region']}, {loc['country']}",
            fg=ACCENT_GREEN,
        )

        # Update prayer time labels
        for name, t in self.timings.items():
            if name in self.prayer_rows:
                self.prayer_rows[name]["lbl_time"].config(text=t)

        self._schedule_all_reminders()

    def _on_data_error(self):
        self._loading = False
        self.lbl_location.config(
            text=f"⚠ Could not load data: {self._load_error[:60]}",
            fg=TEXT_RED,
        )

    # ──────────────────────────────────────────────────────────────────────
    # Notification scheduling
    # ──────────────────────────────────────────────────────────────────────
    def _schedule_all_reminders(self):
        """Schedule desktop reminders for every upcoming prayer today."""
        if not self.timings or not self.tz:
            return

        # Cancel existing timers
        for t in self.active_timers:
            t.cancel()
        self.active_timers.clear()
        self._reminder_scheduled_for.clear()

        now = datetime.datetime.now(self.tz)
        for name in PRAYER_NAMES:
            if name == "Sunrise":
                continue
            prayer_dt = time_str_to_today_dt(self.timings[name], self.tz)
            secs = seconds_until(prayer_dt, now)
            if secs > 0:
                timers = schedule_reminders(
                    name,
                    PRAYER_DISPLAY[name],
                    secs,
                    gui_callback=self._on_notification,
                )
                self.active_timers.extend(timers)
                self._reminder_scheduled_for.add(name)

    def _on_notification(self, title: str, message: str):
        """Called from a timer thread; schedule GUI update in main thread."""
        self.root.after(0, lambda: self._show_notif_banner(title, message))
        self.root.after(0, lambda: self.root.bell())  # audible system bell

    def _show_notif_banner(self, title: str, message: str):
        """Show an in-app notification banner for a few seconds."""
        self.lbl_notif_title.config(text=title)
        self.lbl_notif_msg.config(text=message)
        self.notif_frame.pack(fill=tk.X, padx=14, pady=4)
        # Flash window
        self.root.attributes("-topmost", True)
        # Hide after 15 seconds
        self.root.after(15000, self._hide_notif_banner)

    def _hide_notif_banner(self):
        self.notif_frame.pack_forget()

    # ──────────────────────────────────────────────────────────────────────
    # Live clock + countdown tick
    # ──────────────────────────────────────────────────────────────────────
    def _tick(self):
        """Called every second to update the live clock and countdowns."""
        try:
            tz = self.tz or pytz.utc
            now = datetime.datetime.now(tz)

            # Live clock
            self.lbl_clock.config(text=now.strftime("%H:%M:%S"))

            # Date labels (updated every tick in case of midnight rollover)
            greg_str = now.strftime("%A, %d %B %Y")
            self.lbl_date.config(text=f"📅 {greg_str}")

            if self.hijri:
                hijri = self.hijri
                self.lbl_hijri.config(
                    text=f"☪  {hijri['day']} {hijri['month_name']} {hijri['year']} H"
                )
            else:
                self.lbl_hijri.config(text="☪  Loading Hijri date…")

            if self.timings:
                self._update_prayer_highlights(now, tz)
                self._update_countdown(now, tz)
                self._update_fajr_maghrib(now, tz)

        except Exception:
            pass  # never crash the tick loop

        self.root.after(REFRESH_MS, self._tick)

    def _update_prayer_highlights(self, now, tz):
        """Highlight the current/next prayer row."""
        for name in PRAYER_NAMES:
            if name not in self.prayer_rows:
                continue
            widgets = self.prayer_rows[name]
            prayer_dt = time_str_to_today_dt(self.timings[name], tz)
            secs = seconds_until(prayer_dt, now)

            # active = within last 30 min and not yet 30 min past
            if -1800 < secs <= 0:
                row_bg = "#1a2a00"
                fg = ACCENT_GREEN
            elif 0 < secs <= 600:  # within 10 min
                row_bg = "#2a1a00"
                fg = ACCENT_GOLD
            else:
                row_bg = widgets["bg"]
                fg = widgets["fg"]

            widgets["row"].config(bg=row_bg)
            widgets["lbl_name"].config(bg=row_bg, fg=fg)
            widgets["lbl_time"].config(bg=row_bg, fg=fg)

    def _update_countdown(self, now, tz):
        """Update the next-prayer countdown display."""
        next_name = None
        next_dt = None
        for name in PRAYER_NAMES:
            if name == "Sunrise":
                continue
            prayer_dt = time_str_to_today_dt(self.timings[name], tz)
            if prayer_dt > now:
                next_name = name
                next_dt = prayer_dt
                break

        if next_name:
            secs = seconds_until(next_dt, now)
            self.lbl_next_name.config(text=PRAYER_DISPLAY[next_name])
            fg = TEXT_FAJR if next_name == "Fajr" else (TEXT_MAGHRIB if next_name == "Maghrib" else ACCENT_GREEN)
            self.lbl_next_name.config(fg=fg)
            color = TEXT_RED if secs < 300 else ACCENT_GOLD
            self.lbl_countdown.config(text=_fmt_countdown(secs), fg=color)
        else:
            self.lbl_next_name.config(text="All prayers done for today ✓")
            self.lbl_countdown.config(text="——:——:——")

    def _update_fajr_maghrib(self, now, tz):
        """Update the Ramadan Fajr/Maghrib remaining time labels."""
        fajr_dt = time_str_to_today_dt(self.timings["Fajr"], tz)
        secs_fajr = seconds_until(fajr_dt, now)
        if secs_fajr > 0:
            self.lbl_fajr_remain.config(text=_fmt_countdown(secs_fajr))
        else:
            self.lbl_fajr_remain.config(text="passed ✓", fg=TEXT_DIM)

        maghrib_dt = time_str_to_today_dt(self.timings["Maghrib"], tz)
        secs_maghrib = seconds_until(maghrib_dt, now)
        if secs_maghrib > 0:
            self.lbl_maghrib_remain.config(text=_fmt_countdown(secs_maghrib))
        else:
            self.lbl_maghrib_remain.config(text="passed ✓", fg=TEXT_DIM)


# ──────────────────────────────────────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────────────────────────────────────
def main():
    root = tk.Tk()
    app = PrayerTimeApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
