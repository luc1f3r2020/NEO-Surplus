
from flask import Flask, render_template, request, redirect, url_for, send_file, flash
import sqlite3
import csv
import io
import os
from datetime import datetime
import zipfile
from pathlib import Path

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret")  # for flash messages

# ---------- Database Setup ----------
DB_FILE = "devices.db"

# Paths
APP_ROOT = Path(__file__).resolve().parent
BACKUPS_DIR = APP_ROOT / "backups"

def get_conn():
    return sqlite3.connect(DB_FILE)

def init_db():
    """Initialize SQLite database if it doesn't exist."""
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS devices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            serial_number TEXT NOT NULL,
            tag_number TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

init_db()

# Ensure device_type column exists (upgrade-safe)
def _ensure_device_type_column():
    conn = get_conn()
    try:
        conn.execute("ALTER TABLE devices ADD COLUMN device_type TEXT DEFAULT 'Unknown'")
    except Exception:
        pass
    finally:
        conn.close()
_ensure_device_type_column()

# ---------- Routes ----------
@app.route("/")
def index():
    """Main page with form to add new devices."""
    return render_template("index.html")


@app.route("/add", methods=["POST"])
def add_device():
    """Add a new device to the database."""
    serial = (request.form.get("serial_number") or "").strip()
    tag = (request.form.get("tag_number") or "").strip()

    if not serial or not tag:
        flash("Both Serial Number and Tag Number are required.", "danger")
        return redirect(url_for("index"))

    conn = get_conn()
    c = conn.cursor()
    c.execute(
        "INSERT INTO devices (serial_number, tag_number, device_type, created_at) VALUES (?, ?, ?, ?)",
        (serial, tag, dtype, datetime.utcnow().isoformat(timespec="seconds")),
    )
    conn.commit()
    conn.close()

    flash("Device added.", "success")
    return redirect(url_for("device_list"))


@app.route("/devices")
def device_list():
    """Display all devices in a table."""
    q = request.args.get("q", "").strip()
    conn = get_conn()
    c = conn.cursor()
    if q:
        c.execute(
            "SELECT id, serial_number, tag_number, device_type, created_at FROM devices WHERE serial_number LIKE ? OR tag_number LIKE ? ORDER BY id DESC",
            (f"%{q}%", f"%{q}%")
        )
    else:
        c.execute("SELECT id, serial_number, tag_number, device_type, created_at FROM devices ORDER BY id DESC")
    devices = c.fetchall()
    conn.close()
    return render_template("devices.html", devices=devices, q=q)


@app.route("/export")
def export_csv():
    """Export all devices to a CSV file."""
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id, serial_number, tag_number, device_type, created_at FROM devices ORDER BY id ASC")
    devices = c.fetchall()
    conn.close()

    # Create in-memory CSV
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Serial Number", "Tag Number", "Device Type", "Created At (UTC)"])
    writer.writerows(devices)

    mem = io.BytesIO()
    mem.write(output.getvalue().encode("utf-8"))
    mem.seek(0)
    output.close()

    return send_file(mem, as_attachment=True, download_name="devices.csv", mimetype="text/csv")


if __name__ == "__main__":
    # Use host=0.0.0.0 so it works in containers; change port as needed.
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)


@app.route("/backup")
def create_backup():
    """
    Create a timestamped ZIP backup of the entire app directory (excluding the backups folder itself and common virtual env folders).
    The ZIP is saved to ./backups and also sent to the browser for download.
    """
    BACKUPS_DIR.mkdir(exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_name = f"surplus_backup_{ts}.zip"
    zip_path = BACKUPS_DIR / zip_name

    exclude_dirs = {"backups", ".venv", "venv", "__pycache__", ".git"}

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for root, dirs, files in os.walk(APP_ROOT):
            # Skip excluded directories
            rel_root = Path(root).relative_to(APP_ROOT)
            # Remove excluded dirs from traversal
            dirs[:] = [d for d in dirs if d not in exclude_dirs]

            for fname in files:
                full = Path(root) / fname
                # Skip the backup file currently being written
                if full == zip_path:
                    continue
                # Skip files inside excluded dirs (extra safety)
                if any(part in exclude_dirs for part in full.relative_to(APP_ROOT).parts):
                    continue
                arc = full.relative_to(APP_ROOT)
                z.write(full, arcname=str(arc))

    return send_file(str(zip_path), as_attachment=True, download_name=zip_name, mimetype="application/zip")
