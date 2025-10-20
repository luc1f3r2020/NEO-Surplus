
# NEO Surplus Tracker (Flask)

A simple Flask app for entering surplus device Serial/Tag numbers, choosing a Device Type, listing entries, exporting CSV, and making a one-click backup.

## Features
- Add devices (Serial, Tag, Device Type)
- Search & list
- Export CSV
- Backup button -> creates `backups/surplus_backup_YYYYMMDD_HHMMSS.zip`
- SQLite database auto-created
- Bootstrap 5 with NEO blue/gold styling

## Local Run
```bash
python -m venv .venv
./.venv/Scripts/activate  # Windows
pip install -r requirements.txt
python app.py
```
Open http://127.0.0.1:5000

## Deploy (Render)
- Root Directory: repo root (or set if using subfolder)
- Build Command: `pip install -r requirements.txt`
- Start Command: `gunicorn app:app`

## Deploy (Docker)
```bash
docker build -t neo-surplus .
docker run -p 8080:8080 neo-surplus
```
Then open http://localhost:8080
