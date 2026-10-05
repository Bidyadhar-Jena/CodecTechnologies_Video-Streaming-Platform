import os
import secrets
from functools import wraps
from pathlib import Path

from flask import (
    Blueprint, current_app, render_template, request, redirect,
    url_for, flash, send_from_directory, abort, session
)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

from .db import get_db

main = Blueprint("main", __name__)

ALLOWED = {"mp4", "webm", "ogg", "mov", "m4v"}
CATEGORIES = ["General", "Education", "Entertainment", "Gaming", "Music", "Technology", "Sports", "News"]

def allowed_file(name):
    return "." in name and name.rsplit(".", 1)[1].lower() in ALLOWED

def current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    return get_db().execute(
        "SELECT id, username, email, is_admin, created_at FROM users WHERE id = ?",
        (user_id,)
    ).fetchone()

@main.app_context_processor
def inject_user():
    return {"current_user": current_user(), "categories": CATEGORIES}

def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please log in to continue.", "error")
            return redirect(url_for("main.login", next=request.path))
        return view(*args, **kwargs)
    return wrapped

def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        user = current_user()
        if not user or not user["is_admin"]:
            flash("Administrator access is required.", "error")
            return redirect(url_for("main.index"))
        return view(*args, **kwargs)
    return wrapped

@main.get("/")
def index():
    q = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()
    db = get_db()

    query = """
        SELECT videos.*, COALESCE(users.username, 'Unknown') AS uploader,
               (SELECT COUNT(*) FROM likes WHERE likes.video_id = videos.id) AS like_count
        FROM videos
        LEFT JOIN users ON users.id = videos.user_id
        WHERE 1=1
    """
    params = []

    if q:
        query += " AND (videos.title LIKE ? OR videos.description LIKE ?)"
        params.extend([f"%{q}%", f"%{q}%"])
    if category and category in CATEGORIES:
        query += " AND videos.category = ?"
        params.append(category)

    query += " ORDER BY videos.uploaded_at DESC"
    videos = db.execute(query, params).fetchall()
    return render_template("index.html", videos=videos, q=q, selected_category=category)

@main.route("/register", methods=["GET", "POST"])
def register():
    if session.get("user_id"):
        return redirect(url_for("main.index"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        if not username or not email or not password:
            flash("All fields are required.", "error")
            return render_template("register.html")
        if len(username) < 3:
            flash("Username must be at least 3 characters.", "error")
            return render_template("register.html")
        if len(password) < 6:
            flash("Password must be at least 6 characters.", "error")
            return render_template("register.html")
        if password != confirm:
            flash("Passwords do not match.", "error")
            return render_template("register.html")

        db = get_db()
        exists = db.execute(
            "SELECT id FROM users WHERE username = ? OR email = ?",
            (username, email)
        ).fetchone()
        if exists:
            flash("Username or email is already registered.", "error")
            return render_template("register.html")

        db.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
            (username, email, generate_password_hash(password))
        )
        db.commit()
        flash("Registration successful. You can now log in.", "success")
        return redirect(url_for("main.login"))

    return render_template("register.html")

@main.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("main.index"))

    if request.method == "POST":
        identity = request.form.get("identity", "").strip()
        password = request.form.get("password", "")

        user = get_db().execute(
            "SELECT * FROM users WHERE username = ? OR email = ?",
            (identity, identity.lower())
        ).fetchone()

        if not user or not check_password_hash(user["password_hash"], password):
            flash("Invalid username/email or password.", "error")
            return render_template("login.html")

        session.clear()
        session["user_id"] = user["id"]
        flash(f"Welcome back, {user['username']}!", "success")

        next_url = request.args.get("next")
        if next_url and next_url.startswith("/"):
            return redirect(next_url)
        return redirect(url_for("main.index"))

    return render_template("login.html")

@main.get("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("main.index"))

@main.get("/profile/<username>")
def profile(username):
    db = get_db()
    user = db.execute(
        "SELECT id, username, email, is_admin, created_at FROM users WHERE username = ?",
        (username,)
    ).fetchone()
    if not user:
        abort(404)

    videos = db.execute(
        "SELECT * FROM videos WHERE user_id = ? ORDER BY uploaded_at DESC",
        (user["id"],)
    ).fetchall()
    return render_template("profile.html", profile=user, videos=videos)

@main.get("/watch/<int:video_id>")
def watch(video_id):
    db = get_db()
    video = db.execute("""
        SELECT videos.*, COALESCE(users.username, 'Unknown') AS uploader,
               (SELECT COUNT(*) FROM likes WHERE likes.video_id = videos.id) AS like_count
        FROM videos
        LEFT JOIN users ON users.id = videos.user_id
        WHERE videos.id = ?
    """, (video_id,)).fetchone()

    if video is None:
        abort(404)

    db.execute("UPDATE videos SET views = views + 1 WHERE id = ?", (video_id,))

    user_id = session.get("user_id")
    if user_id:
        db.execute("""
            INSERT INTO history (user_id, video_id)
            VALUES (?, ?)
            ON CONFLICT(user_id, video_id)
            DO UPDATE SET watched_at = CURRENT_TIMESTAMP
        """, (user_id, video_id))

    db.commit()

    comments = db.execute("""
        SELECT comments.*, users.username
        FROM comments
        JOIN users ON users.id = comments.user_id
        WHERE comments.video_id = ?
        ORDER BY comments.created_at DESC
    """, (video_id,)).fetchall()

    liked = False
    if user_id:
        liked = db.execute(
            "SELECT 1 FROM likes WHERE user_id = ? AND video_id = ?",
            (user_id, video_id)
        ).fetchone() is not None

    return render_template("watch.html", video=video, comments=comments, liked=liked)

@main.get("/media/<path:filename>")
def media(filename):
    return send_from_directory(current_app.config["UPLOAD_FOLDER"], filename, conditional=True)

@main.route("/upload", methods=["GET", "POST"])
@login_required
def upload():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        category = request.form.get("category", "General").strip()
        file = request.files.get("video")

        if not title or not file or not file.filename:
            flash("Title and video file are required.", "error")
            return redirect(url_for("main.upload"))

        if category not in CATEGORIES:
            category = "General"

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
        cur = db.execute("""
            INSERT INTO videos
            (title, description, category, filename, original_name, user_id)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            title, description, category, stored, original, session["user_id"]
        ))
        db.commit()

        flash("Video uploaded successfully.", "success")
        return redirect(url_for("main.watch", video_id=cur.lastrowid))

    return render_template("upload.html")

@main.post("/video/<int:video_id>/like")
@login_required
def like_video(video_id):
    db = get_db()
    video = db.execute("SELECT id FROM videos WHERE id = ?", (video_id,)).fetchone()
    if not video:
        abort(404)

    existing = db.execute(
        "SELECT id FROM likes WHERE user_id = ? AND video_id = ?",
        (session["user_id"], video_id)
    ).fetchone()

    if existing:
        db.execute("DELETE FROM likes WHERE id = ?", (existing["id"],))
    else:
        db.execute(
            "INSERT INTO likes (user_id, video_id) VALUES (?, ?)",
            (session["user_id"], video_id)
        )
    db.commit()
    return redirect(url_for("main.watch", video_id=video_id))

@main.post("/video/<int:video_id>/comment")
@login_required
def comment_video(video_id):
    content = request.form.get("content", "").strip()
    if content:
        db = get_db()
        exists = db.execute("SELECT id FROM videos WHERE id = ?", (video_id,)).fetchone()
        if not exists:
            abort(404)
        db.execute(
            "INSERT INTO comments (user_id, video_id, content) VALUES (?, ?, ?)",
            (session["user_id"], video_id, content)
        )
        db.commit()
    return redirect(url_for("main.watch", video_id=video_id))

@main.get("/history")
@login_required
def history():
    videos = get_db().execute("""
        SELECT videos.*, history.watched_at,
               COALESCE(users.username, 'Unknown') AS uploader
        FROM history
        JOIN videos ON videos.id = history.video_id
        LEFT JOIN users ON users.id = videos.user_id
        WHERE history.user_id = ?
        ORDER BY history.watched_at DESC
    """, (session["user_id"],)).fetchall()
    return render_template("index.html", videos=videos, q="", selected_category="",
                           page_title="Watch History")

@main.get("/admin")
@admin_required
def admin():
    db = get_db()
    total_users = db.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    total_videos = db.execute("SELECT COUNT(*) FROM videos").fetchone()[0]
    total_views = db.execute("SELECT COALESCE(SUM(views), 0) FROM videos").fetchone()[0]

    users = db.execute("""
        SELECT users.*,
               (SELECT COUNT(*) FROM videos WHERE videos.user_id = users.id) AS video_count
        FROM users ORDER BY users.created_at DESC
    """).fetchall()

    videos = db.execute("""
        SELECT videos.*, COALESCE(users.username, 'Unknown') AS uploader,
               (SELECT COUNT(*) FROM likes WHERE likes.video_id = videos.id) AS like_count
        FROM videos
        LEFT JOIN users ON users.id = videos.user_id
        ORDER BY videos.uploaded_at DESC
    """).fetchall()

    return render_template(
        "admin.html",
        total_users=total_users,
        total_videos=total_videos,
        total_views=total_views,
        active_users=total_users,
        users=users,
        videos=videos
    )

@main.post("/admin/delete/<int:video_id>")
@admin_required
def delete_video(video_id):
    db = get_db()
    video = db.execute(
        "SELECT filename FROM videos WHERE id = ?", (video_id,)
    ).fetchone()
    if not video:
        abort(404)

    file_path = Path(current_app.config["UPLOAD_FOLDER"]) / video["filename"]
    if file_path.exists():
        file_path.unlink()

    db.execute("DELETE FROM videos WHERE id = ?", (video_id,))
    db.commit()
    flash("Video deleted.", "success")
    return redirect(url_for("main.admin"))
