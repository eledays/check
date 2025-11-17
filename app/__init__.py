from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.middleware.proxy_fix import ProxyFix

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

    return app
