"""Cyber Defense Lab: local defensive event simulation, not an attack toolkit."""
import os
from datetime import timedelta

from flask import Flask, jsonify
from flask_cors import CORS

from extensions import db, jwt


def create_app(config=None):
    app = Flask(__name__)
    app.config.update(
        SQLALCHEMY_DATABASE_URI=os.getenv("DATABASE_URL", "sqlite:///cyberlab.db"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        JWT_ACCESS_TOKEN_EXPIRES=timedelta(hours=1),
        MAX_CONTENT_LENGTH=16 * 1024,
    )
    if config:
        app.config.update(config)

    # Refuse the template's hardcoded signing key. Test code provides its own.
    signing_key = app.config.get("JWT_SECRET_KEY") or os.getenv("JWT_SECRET_KEY")
    if not signing_key or len(signing_key) < 32:
        raise RuntimeError("Set JWT_SECRET_KEY to a random string of at least 32 characters.")
    app.config["JWT_SECRET_KEY"] = signing_key

    CORS(app, resources={r"/*": {"origins": [
        origin.strip() for origin in os.getenv(
            "FRONTEND_ORIGINS", "http://localhost:5173"
        ).split(",") if origin.strip()
    ]}})

    db.init_app(app)
    jwt.init_app(app)
    from models import User, SecurityEvent
    from routes import api
    app.register_blueprint(api)

    @app.get("/")
    @app.get("/health")
    def health():
        return jsonify(status="ok", environment="educational-demo")

    with app.app_context():
        # Simple local demo initialization, not a replacement for migrations.
        db.create_all()
    return app


if __name__ == "__main__":
    create_app().run(host="127.0.0.1", port=5000, debug=False)
