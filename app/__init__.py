from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

from config import Config

from typing import Type

db = SQLAlchemy()
migrate = Migrate()


def create_app(config_class: Type[Config] = Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)

    from app.routes import bp as main_bp

    app.register_blueprint(main_bp)

    from app import models

    return app
