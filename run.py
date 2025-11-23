from flask.app import Flask
from flask_migrate import Migrate
from app import create_app, db
import logging
import threading
import os

app: Flask = create_app()
migrate = Migrate(app, db)

# Initialize bot if token is configured
# ВАЖНО: Запускаем бота только в основном процессе Flask, не в reloader
bot_instance = None
if app.config.get("TELEGRAM_BOT_TOKEN") and os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
    try:
        from app.bot import create_bot
        
        bot_instance = create_bot(
            token=app.config["TELEGRAM_BOT_TOKEN"],
            app=app,
            db=db,
            reminder_time=app.config.get("BOT_REMINDER_TIME", "20:00"),
            timezone=app.config.get("BOT_TIMEZONE", "UTC"),
            reminders_enabled=app.config.get("BOT_REMINDERS_ENABLED", True)
        )
        
        # Start bot in a separate thread
        bot_thread = threading.Thread(target=bot_instance.start_polling, daemon=True)
        bot_thread.start()
        
        logging.info("✅ Telegram bot started successfully")
        logging.info(f"📅 Daily reminders scheduled for {app.config.get('BOT_REMINDER_TIME', '20:00')} ({app.config.get('BOT_TIMEZONE', 'UTC')})")
    except Exception as e:
        logging.error(f"❌ Failed to start Telegram bot: {e}")
elif not app.config.get("TELEGRAM_BOT_TOKEN"):
    logging.warning("⚠️ TELEGRAM_BOT_TOKEN not configured - bot disabled")

if __name__ == "__main__":
    # Suppress SSL/TLS handshake errors in development
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.INFO)
    
    app.run(debug=True, host="0.0.0.0", port=5000)
