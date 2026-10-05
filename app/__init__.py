import os
from flask import Flask
from .db import init_db, close_db

def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get(
        "SECRET_KEY", "streamhub-development-secret-change-me"
    )
    app.config["MAX_CONTENT_LENGTH"] = 500 * 1024 * 1024
    app.config["UPLOAD_FOLDER"] = os.path.join(
        app.root_path, "static", "uploads"
    )

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    init_db(app)
    app.teardown_appcontext(close_db)

    from .routes import main
    app.register_blueprint(main)

    return app
