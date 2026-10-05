import os
import secrets
from pathlib import Path
from flask import Blueprint, current_app, render_template, request, redirect, url_for, flash, send_from_directory, abort
from werkzeug.utils import secure_filename
from .db import get_db

main = Blueprint("main", __name__)
ALLOWED = {"mp4", "webm", "ogg", "mov", "m4v"}

def allowed_file(name):
    return "." in name and name.rsplit(".", 1)[1].lower() in ALLOWED

@main.get("/")
def index():
    q = request.args.get("q", "").strip()
    db = get_db()
    if q:
        videos = db.execute(
            "SELECT * FROM videos WHERE title LIKE ? OR description LIKE ? ORDER BY uploaded_at DESC",
            (f"%{q}%", f"%{q}%")
        ).fetchall()
    else:
        videos = db.execute("SELECT * FROM videos ORDER BY uploaded_at DESC").fetchall()
    return render_template("index.html", videos=videos, q=q)

@main.get("/watch/<int:video_id>")
def watch(video_id):
    db = get_db()
    video = db.execute("SELECT * FROM videos WHERE id = ?", (video_id,)).fetchone()
    if video is None:
        abort(404)
    db.execute("UPDATE videos SET views = views + 1 WHERE id = ?", (video_id,))
    db.commit()
    return render_template("watch.html", video=video)

@main.get("/media/<path:filename>")
def media(filename):
    return send_from_directory(current_app.config["UPLOAD_FOLDER"], filename, conditional=True)

@main.route("/upload", methods=["GET", "POST"])
def upload():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        file = request.files.get("video")

        if not title or not file or not file.filename:
            flash("Title and video file are required.", "error")
            return redirect(url_for("main.upload"))

        if not allowed_file(file.filename):
            flash("Unsupported format. Use MP4, WebM, OGG, MOV or M4V.", "error")
            return redirect(url_for("main.upload"))

        original = secure_filename(file.filename)
        ext = Path(original).suffix.lower()
        stored = f"{secrets.token_hex(16)}{ext}"
        folder = Path(current_app.config["UPLOAD_FOLDER"])
        folder.mkdir(parents=True, exist_ok=True)
        file.save(folder / stored)

        db = get_db()
        cur = db.execute(
            "INSERT INTO videos (title, description, filename, original_name) VALUES (?, ?, ?, ?)",
            (title, description, stored, original)
        )
        db.commit()
        flash("Video uploaded successfully.", "success")
        return redirect(url_for("main.watch", video_id=cur.lastrowid))

    return render_template("upload.html")
