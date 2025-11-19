from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.middleware.proxy_fix import ProxyFix
import datetime

from config import Config

from typing import Type

db = SQLAlchemy()
migrate = Migrate()


def create_app(config_class: Type[Config] = Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Enable proxy fix for HTTPS support (VS Code Ports, ngrok, etc.)
    app.wsgi_app = ProxyFix(
        app.wsgi_app,
        x_for=1,
        x_proto=1,
        x_host=1,
        x_prefix=1
    )

    db.init_app(app)

    from app.routes import bp as main_bp

    app.register_blueprint(main_bp)

    from app import models

    # Register custom Jinja2 filters
    @app.template_filter('utc_iso')
    def utc_iso_filter(dt: datetime.datetime | None) -> str:
        """Convert datetime to UTC ISO format with Z suffix for JavaScript."""
        if dt is None:
            return ''
        
        # If datetime is naive, treat it as UTC
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=datetime.timezone.utc)
        
        return dt.isoformat()

    return app
