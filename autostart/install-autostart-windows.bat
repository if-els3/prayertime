@echo off
REM install-autostart-windows.bat
REM Adds the Prayer Time app to the Windows startup registry key

SET "APP_DIR=%~dp0.."
SET "PYTHON=pythonw"
SET "SCRIPT=%APP_DIR%\prayertime_app.py"
SET "REG_KEY=HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
SET "REG_NAME=PrayerTime"

REG ADD "%REG_KEY%" /v "%REG_NAME%" /t REG_SZ /d "\"%PYTHON%\" \"%SCRIPT%\"" /f
IF %ERRORLEVEL% == 0 (
    echo Autostart registered successfully.
    echo Prayer Time will launch at next Windows login.
) ELSE (
    echo Failed to register autostart entry.
)
pause
