import os
from dotenv import load_dotenv
load_dotenv()


class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///check.db")
    # Secret key required by Flask-WTF for CSRF protection. In production, set via env var.
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
