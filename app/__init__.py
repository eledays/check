from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

from logging import Logger, getLogger

from config import Config

db = SQLAlchemy()
migrate = Migrate()
logger: Logger = getLogger(__name__)

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
migrate.init_app(app, db)

from app.routes.main import bp as main_bp
from app.routes.auth import bp as auth_bp
from app.routes.habits import bp as habits_bp

app.register_blueprint(main_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(habits_bp)
