import os

from dotenv import load_dotenv

load_dotenv()


class Config:

    SECRET_KEY = os.getenv("SECRET_KEY", "")
    SECRET_KEY = os.getenv("SECRET_KEY", "")
    SQLALCHEMY_DATABASE_URI = "sqlite:///instance/app.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Yandex OAuth
    YANDEX_CLIENT_ID = os.environ.get('YANDEX_CLIENT_ID')
    YANDEX_CLIENT_SECRET = os.environ.get('YANDEX_CLIENT_SECRET')
    YANDEX_REDIRECT_URI = 'http://localhost:5000/oauth/yandex/callback'