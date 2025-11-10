from flask import Flask
from config import Config

from typing import Type


def create_app(config_class: Type[Config] = Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_class)

    from app.routes import bp as main_bp

    app.register_blueprint(main_bp)

    return app
