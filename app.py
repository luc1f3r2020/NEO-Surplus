
from flask import Flask, render_template, request, redirect, url_for, send_file, flash
import sqlite3
import csv
import io
import os
from datetime import datetime
from pathlib import Path
import zipfile

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret")

# --- Paths & DB ---
DB_FILE = "devices.db"
APP_ROOT = Path(__file__).resolve().parent
BACKUPS_DIR = APP_ROOT / "backups"

def get_conn():
    return sqlite3.connect(DB_FILE)

def init_db():
    """Create table if needed (with device_type); upgrade older DBs."""
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS devices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            serial_number TEXT NOT NULL,
            tag_number TEXT NOT NULL,
            device_type TEXT DEFAULT 'Unknown',
            created_at TEXT NOT NULL
        )
    """)
    # Upgrade older DBs (adds device_type if missing)
    try:
        c.execute("ALTER TABLE devices ADD COLUMN device_type TEXT DEFAULT 'Unknown'")
    except sqlite3.OperationalError:
        pass
    conn.commit()
    conn.close()

init_db()

# --- Routes ---
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/add", methods=["POST")
def add_device():
    serial = (request.form.get("serial_number") or "").strip()
    tag = (request.form.get("tag_number") or "").strip()
    dtype = (request.form.get("device_type") or "Unknown").strip()

    if not serial or not tag:
        flash("Both Serial Number and Tag Number are required.", "danger")
        return redirect(url_for("index"))

    conn = get_conn()
    conn.execute(
        "INSERT INTO devices (serial_number, tag_number, device_type, created_at) VALUES (?, ?, ?, ?)",
        (serial, tag, dtype, datetime.utcnow().isoformat(timespec="seconds")),
    )
    conn.commit()
    conn.close()

    flash(f"{dtype} added successfully.", "success")
    return redirect(url_for("device_list"))

@app.route("/devices")
def device_list():
    q = (request.args.get("q") or "").strip()
    conn = get_conn()
    c = conn.cursor()
    if q:
        c.execute("""            SELECT id, serial_number, tag_number, device_type, created_at
            FROM devices
            WHERE serial_number LIKE ? OR tag_number LIKE ? OR device_type LIKE ?
            ORDER BY id DESC
        """, (f"%{q}%", f"%{q}%", f"%{q}%"))
    else:
        c.execute("SELECT id, serial_number, tag_number, device_type, created_at FROM devices ORDER BY id DESC")
    devices = c.fetchall()
    conn.close()
    return render_template("devices.html", devices=devices, q=q)

@app.route("/export")
def export_csv():
    conn = get_conn()
    rows = conn.execute(
        "SELECT id, serial_number, tag_number, device_type, created_at FROM devices ORDER BY id ASC"
    ).fetchall()
    conn.close()

    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(["ID", "Serial Number", "Tag Number", "Device Type", "Created At (UTC)"])
    w.writerows(rows)

    mem = io.BytesIO(out.getvalue().encode("utf-8"))
    mem.seek(0)
    return send_file(mem, as_attachment=True, download_name="devices.csv", mimetype="text/csv")

# Endpoint explicitly named 'create_backup' to match templates
@app.route("/backup", methods=["GET"], endpoint="create_backup")
def create_backup():
    """Create a timestamped ZIP of the entire app (excludes backups/.venv/venv/__pycache__/.git)."""
    BACKUPS_DIR.mkdir(exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_name = f"surplus_backup_{ts}.zip"
    zip_path = BACKUPS_DIR / zip_name
    exclude = {"backups", ".venv", "venv", "__pycache__", ".git"}

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for root, dirs, files in os.walk(APP_ROOT):
            dirs[:] = [d for d in dirs if d not in exclude]
            for f in files:
                full = Path(root) / f
                rel = full.relative_to(APP_ROOT)
                if any(part in exclude for part in rel.parts):
                    continue
                if full == zip_path:
                    continue
                z.write(full, arcname=str(rel))

    return send_file(str(zip_path), as_attachment=True, download_name=zip_name, mimetype="application/zip")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
