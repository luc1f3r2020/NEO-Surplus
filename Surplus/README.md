
# NEO Surplus Tracker (Flask)

A minimal Flask app for work-study students to enter device serial and tag numbers for surplus, list entries, and export CSV.

## Features
- Add devices (serial + tag)
- List & search
- CSV export
- SQLite database (auto-created)
- Bootstrap 5 modern UI

## Quickstart (Windows)
1. Extract the ZIP to `C:\Scripts\SurplusTracker` (recommended path).
2. Double-click `run.bat` (first run creates a venv, installs deps, and launches).
3. Open http://127.0.0.1:5000

## Quickstart (PowerShell)
```powershell
.\run.ps1
```

## Cloud Deployment
- **Render**: push to GitHub; add a Web Service. Build command: `pip install -r requirements.txt`. Start: `gunicorn app:app`.
- **Fly.io**: `fly launch` (use `PORT` env). App listens on `$PORT` automatically via `app.py`.
- **Azure App Service**: Python runtime; startup command `gunicorn app:app`.

## Notes
- The DB file `devices.db` is created in the app root.
- Set `FLASK_SECRET_KEY` env var for production.
