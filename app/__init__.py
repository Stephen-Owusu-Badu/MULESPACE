from flask import Flask
from flask_cors import CORS
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

from config import config

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()


def create_app(config_name="default"):
    """Application factory pattern."""
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    CORS(app)

    # Login manager configuration
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please log in to access this page."
    login_manager.login_message_category = "info"

    # Import models
    from app import models  # noqa: F401
    from app.routes.admin import admin_bp
    from app.routes.attendance import attendance_bp

    # Register blueprints (REST API)
    from app.routes.auth import auth_bp
    from app.routes.calendar import calendar_bp
    from app.routes.events import events_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(events_bp, url_prefix="/api/events")
    app.register_blueprint(calendar_bp, url_prefix="/api/calendar")
    app.register_blueprint(attendance_bp, url_prefix="/api/attendance")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")

    # Create database tables
    with app.app_context():
        db.create_all()

    return app
