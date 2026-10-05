from flask import Flask
from .db import init_db

def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "change-this-secret-key"
    app.config["MAX_CONTENT_LENGTH"] = 500 * 1024 * 1024
    app.config["UPLOAD_FOLDER"] = "app/static/uploads"

    init_db(app)

    from .routes import main
    app.register_blueprint(main)

    return app
