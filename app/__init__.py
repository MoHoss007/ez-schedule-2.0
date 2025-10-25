from __future__ import annotations
import os
from flask import Flask
from dotenv import load_dotenv

from app.config import Config
from .logging_cfg import configure_logging
from flask_cors import CORS


def create_app() -> Flask:
    # Load env before creating the app (so Config can read it)
    load_dotenv()
    configure_logging()

    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Configure CORS to handle AWS Signature V4 headers and credentials
    CORS(app, 
         supports_credentials=True)

    # Blueprints
    from app.api.clubs import bp as clubs_bp
    from app.api.health import bp as health_bp
    from app.api.teamsnap import bp as teamsnap_bp
    from app.api.users import bp as users_bp

    app.register_blueprint(clubs_bp, url_prefix=f"{Config.API_PREFIX}/clubs")
    app.register_blueprint(health_bp, url_prefix=f"{Config.API_PREFIX}/health")
    app.register_blueprint(teamsnap_bp, url_prefix=f"{Config.API_PREFIX}/auth/teamsnap")
    app.register_blueprint(users_bp, url_prefix=f"{Config.API_PREFIX}/users")

    return app
