import os
from dotenv import load_dotenv
load_dotenv()


class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///check.db")
    # Secret key required by Flask-WTF for CSRF protection. In production, set via env var.
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
    PREFERRED_URL_SCHEME = "https"
    
    # Telegram Bot Token for Mini App authentication
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    
    # Mini App URL (optional, will be auto-generated from bot username if not set)
    MINI_APP_URL = os.getenv("MINI_APP_URL", "")
    
    # Enable Telegram Mock for local development (disable with TELEGRAM_MOCK=false)
    TELEGRAM_MOCK = os.getenv("TELEGRAM_MOCK", "false").lower() == "true"
    
    # Bot reminder settings
    # Time to send daily reminders (format: "HH:MM" in 24-hour format, timezone-aware)
    DEFAULT_BOT_REMINDER_TIME = os.getenv("BOT_REMINDER_TIME", "20:00")
    
    # Timezone for reminders (default: UTC)
    BOT_TIMEZONE = os.getenv("BOT_TIMEZONE", "UTC")
    
    # Enable/disable bot reminders
    BOT_REMINDERS_ENABLED = os.getenv("BOT_REMINDERS_ENABLED", "true").lower() == "true"

    REMINDER_CHECK_INTERVAL = 60  # Check for reminders every 60 seconds
