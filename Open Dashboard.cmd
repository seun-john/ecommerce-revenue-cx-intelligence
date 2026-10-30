@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo The project Python environment is missing. Run scripts\run.ps1 first.
  pause
  exit /b 1
)
echo Open http://127.0.0.1:8765 in your browser.
echo Keep this window open while using the dashboard. Press Ctrl+C to stop.
".venv\Scripts\python.exe" -m src.dashboard
if errorlevel 1 (
  echo If the dashboard is already running, open http://127.0.0.1:8765
  pause
)
