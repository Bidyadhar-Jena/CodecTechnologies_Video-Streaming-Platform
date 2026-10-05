# StreamHub — Video Streaming Platform

A clean, original full-stack video streaming platform built with Python, Flask, SQLite, HTML, CSS and JavaScript.

## Features

- Video upload with file-type validation
- Browser-based video playback
- HTTP range/conditional delivery through Flask
- Search by title and description
- View counter
- Responsive dark UI
- SQLite database
- Secure randomized stored filenames
- Flash notifications and basic validation

## Tech Stack

- **Backend:** Python + Flask
- **Database:** SQLite
- **Frontend:** HTML5, CSS3, vanilla JavaScript
- **Video:** HTML5 `<video>` with server-side conditional/range responses

## Project Structure

```text
own-video-streaming-platform/
├── app/
│   ├── __init__.py
│   ├── db.py
│   ├── routes.py
│   ├── templates/
│   │   ├── base.html
│   │   ├── index.html
│   │   ├── upload.html
│   │   └── watch.html
│   └── static/
│       ├── css/style.css
│       ├── js/app.js
│       └── uploads/
├── instance/
├── requirements.txt
├── run.py
├── .gitignore
└── README.md
```

## Run locally

### 1. Create a virtual environment

**Windows**
```bash
python -m venv .venv
.venv\Scripts\activate
```

**Linux/macOS**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Start the server

```bash
python run.py
```

Open `http://127.0.0.1:5000`.

## GitHub setup

Create a new repository, then:

```bash
git init
git add .
git commit -m "Initial StreamHub video streaming platform"
git branch -M main
git remote add origin YOUR_GITHUB_REPOSITORY_URL
git push -u origin main
```

## Production notes

This is a project/demo MVP, not a production YouTube clone. For production deployment, add authentication, object storage such as S3-compatible storage, a background transcoding pipeline, HLS/DASH adaptive streaming, rate limiting, CSRF protection, moderation, thumbnails, and a production WSGI server.

## Author

Bidyadhar Jena
