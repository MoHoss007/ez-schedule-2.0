from __future__ import annotations
import os
from flask import Flask
from dotenv import load_dotenv

from app.config import Config
from .logging_cfg import configure_logging
from app.auth.teamsnap import bp as teamsnap_bp
from app.api.health import bp as health_bp


def create_app() -> Flask:
    # Load env before creating the app (so Config can read it)
    load_dotenv()
    configure_logging()

    app = Flask(__name__)
    app.config.from_object(Config)

    # Blueprints
    app.register_blueprint(health_bp)
    app.register_blueprint(teamsnap_bp, url_prefix="/auth/teamsnap")

    return app
