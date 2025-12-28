from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask.logging import default_handler

import logging
from logging.handlers import RotatingFileHandler, SMTPHandler
import sys
import os

from config import Config

db = SQLAlchemy()
migrate = Migrate()
logger = logging.getLogger(__name__)

formatter = logging.Formatter(
    '[%(asctime)s] '
    '%(levelname)s in %(module)s: %(message)s'
)

# Консольный хендлер
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(formatter)

# Файловый хендлер
if not os.path.exists('logs'):
    os.makedirs('logs')
file_handler = RotatingFileHandler(
    'logs/app.log', 
    maxBytes=10485760,  # 10MB
    backupCount=10,
    encoding='utf-8'
)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(formatter)

# Добавляем хендлеры к своему логгеру
logger.addHandler(console_handler)
logger.addHandler(file_handler)

app = Flask(__name__)
app.config.from_object(Config)

# Удаляем стандартный хендлер Flask
app.logger.removeHandler(default_handler)

# Добавляем наши хендлеры к логгеру Flask
app.logger.addHandler(console_handler)
app.logger.addHandler(file_handler)
app.logger.setLevel(logging.DEBUG)

db.init_app(app)
migrate.init_app(app, db)

from app.routes.main import bp as main_bp
from app.routes.auth import bp as auth_bp
from app.routes.habits import bp as habits_bp

app.register_blueprint(main_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(habits_bp)
