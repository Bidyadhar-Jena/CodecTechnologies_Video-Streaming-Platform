# StreamHub - Video Streaming Platform

A Flask-based video streaming platform with user authentication, video upload,
search, categories, likes, comments, watch history, profiles, and an admin dashboard.

## Features

- User registration, login and logout
- Password hashing with Werkzeug
- Admin role and protected admin dashboard
- Video upload and browser playback
- MP4, WebM, OGG, MOV and M4V support
- Search by title and description
- Categories
- Likes and comments
- Watch history
- User profiles
- Admin video deletion
- SQLite database
- Responsive interface

## Run locally

### 1. Create a virtual environment

Windows:

```bash
python -m venv venv
venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Start the application

```bash
python run.py
```

Open:

`http://127.0.0.1:5000`

## Default admin account

For first-time local setup, register a normal account and then promote it to
admin directly in SQLite if required:

```sql
UPDATE users SET is_admin = 1 WHERE username = 'your_username';
```

The database is created automatically at `instance/streamhub.db`.

## Project structure

```text
StreamHub/
├── run.py
├── requirements.txt
├── README.md
├── LICENSE
├── .gitignore
├── .env.example
└── app/
    ├── __init__.py
    ├── db.py
    ├── routes.py
    ├── templates/
    │   ├── base.html
    │   ├── index.html
    │   ├── login.html
    │   ├── register.html
    │   ├── watch.html
    │   ├── upload.html
    │   ├── admin.html
    │   └── profile.html
    └── static/
        ├── css/
        │   └── style.css
        ├── js/
        │   └── app.js
        └── .gitkeep
```
## Author

Bidyadhar Jena
