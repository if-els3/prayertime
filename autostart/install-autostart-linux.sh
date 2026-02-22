#!/usr/bin/env bash
# install-autostart-linux.sh
# Installs the Prayer Time app to run at login on Linux (systemd user or .desktop)
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$(dirname "$SCRIPT_DIR")"
PYTHON="$(command -v python3)"
AUTOSTART_DIR="$HOME/.config/autostart"
DESKTOP_FILE="$AUTOSTART_DIR/prayertime.desktop"

mkdir -p "$AUTOSTART_DIR"

cat > "$DESKTOP_FILE" <<EOF
[Desktop Entry]
Type=Application
Name=Prayer Time
Comment=Islamic prayer time desktop widget
Exec=$PYTHON $APP_DIR/prayertime_app.py
Icon=dialog-information
Terminal=false
Categories=Utility;
X-GNOME-Autostart-enabled=true
EOF

chmod +x "$DESKTOP_FILE"
echo "✅  Autostart entry created at: $DESKTOP_FILE"
echo "    The Prayer Time app will launch automatically at next login."
