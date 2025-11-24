"""
Telegram Bot for check project management system.
Handles commands and sends daily reminders to users.
"""
import logging
import threading
import time
import datetime
from typing import Optional
import pytz

import telebot
from telebot import types

from app.models import User
from app.bot_service import (
    get_daily_summary, format_summary_message, get_reminder_message,
    get_users_for_reminder
)
from app.crud import get_or_create_user_settings, update_user_settings
from config import Config

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class CheckBot:
    """
    Telegram Bot for the Check project management system.
    """

    def __init__(self, token: str, app, db, reminder_time: str = "20:00",
                 timezone: str = "UTC", reminders_enabled: bool = True):
        """
        Initialize the bot.

        Args:
            token: Telegram Bot API token
            app: Flask application instance
            db: SQLAlchemy database instance
            reminder_time: Time to send daily reminders (HH:MM format)
            timezone: Timezone for reminders
            reminders_enabled: Whether to enable daily reminders
        """
        self.bot = telebot.TeleBot(token, parse_mode='html')
        self.app = app
        self.db = db
        self.reminder_time = reminder_time
        self.timezone = pytz.timezone(timezone)
        self.reminders_enabled = reminders_enabled
        self.reminder_thread: Optional[threading.Thread] = None
        self.stop_reminders = threading.Event()
        
        # Get Mini App URL from config or generate from bot username
        self.mini_app_url = self.app.config.get('MINI_APP_URL')
        if not self.mini_app_url:
            try:
                bot_username = self.bot.get_me().username
                if bot_username:
                    self.mini_app_url = f"https://t.me/{bot_username}/app"
            except Exception as e:
                logger.warning(f"Failed to get bot username: {e}")
                self.mini_app_url = None

        # Register handlers
        self._register_handlers()

    def _register_handlers(self):
        """Register bot command handlers."""

        @self.bot.message_handler(commands=['start'])
        def handle_start(message):
            """Handle /start command."""
            user_id = message.from_user.id

            # Get or create user in database
            with self.app.app_context():
                user = User.query.filter_by(telegram_id=user_id).first()
                if not user:
                    user = User()
                    user.telegram_id = user_id
                    self.db.session.add(user)
                    self.db.session.commit()

            welcome_text = (
                "<b>Привет, это check </b>— сервис для управления проектами и задачами. "
                "Давай начнем, открывай мини апп"
            )

            # Create keyboard with web app button if URL is available
            if self.mini_app_url:
                try:
                    markup = types.InlineKeyboardMarkup()
                    web_app_button = types.InlineKeyboardButton(
                        text="Открыть",
                        web_app=types.WebAppInfo(url=self.mini_app_url)
                    )
                    markup.add(web_app_button)  
                    
                    # Remove any existing keyboard and show inline buttons instead
                    self.bot.send_message(
                        message.chat.id,
                        welcome_text,
                        reply_markup=markup
                    )
                except Exception as e:
                    logger.warning(f"Failed to create WebApp button: {e}")
                    # Send without button but still remove keyboard
                    self.bot.send_message(
                        message.chat.id,
                        welcome_text,
                        reply_markup=types.ReplyKeyboardRemove()
                    )
            else:
                # Remove keyboard if no URL available
                self.bot.send_message(
                    message.chat.id,
                    welcome_text,
                    reply_markup=types.ReplyKeyboardRemove()
                )

        @self.bot.message_handler(commands=['help'])
        def handle_help(message):
            """Handle /help command."""
            help_text = (
                "<b>Команды</b>\n"
                "/start — начать работу\n"
                "/app — открыть мини апп\n"
                "/summary — получить итоги дня\n"
                "/settings — посмотреть настройки уведомлений\n"
                "/remind — управление уведомлениями\n"
                "/help — показать эту справку\n\n"
                "<b>Управление уведомлениями:</b>\n"
                "- <code>/remind on</code> — включить уведомления\n"
                "- <code>/remind off</code> — отключить уведомления\n"
                "- <code>/remind time HH:MM</code> — установить время\n"
                "- <code>/remind tz TIMEZONE</code> — установить часовой пояс\n\n"
            )

            self.bot.send_message(
                message.chat.id,
                help_text,
            )

        @self.bot.message_handler(commands=['app'])
        def handle_app(message):
            """Handle /app command."""
            if not self.mini_app_url:
                self.bot.send_message(
                    message.chat.id,
                    "❌ Mini App URL не настроен. Обратитесь к администратору.",
                )
                return

            try:
                markup = types.InlineKeyboardMarkup()
                web_app_button = types.InlineKeyboardButton(
                    text="Открыть приложение",
                    web_app=types.WebAppInfo(url=self.mini_app_url)
                )
                markup.add(web_app_button)

                self.bot.send_message(
                    message.chat.id,
                    "Нажмите кнопку ниже, чтобы открыть приложение:",
                    reply_markup=markup
                )
            except Exception as e:
                logger.error(f"Failed to send app link: {e}")
                self.bot.send_message(
                    message.chat.id,
                    f"Ссылка на приложение: {self.mini_app_url}"
                )

        @self.bot.message_handler(commands=['summary'])
        def handle_summary(message):
            """Handle /summary command - show daily summary."""
            user_id = message.from_user.id

            with self.app.app_context():
                # Find user in database
                user = User.query.filter_by(telegram_id=user_id).first()

                if not user:
                    self.bot.send_message(
                        message.chat.id,
                        "❌ Вы не зарегистрированы. Используйте /start для начала работы."
                    )
                    return

                # Get summary
                summary = get_daily_summary(user.id)
                summary_text = format_summary_message(summary)

                self.bot.send_message(
                    message.chat.id,
                    summary_text,
                )

        @self.bot.message_handler(commands=['settings'])
        def handle_settings(message):
            """Handle /settings command - show and manage user settings."""
            user_id = message.from_user.id

            with self.app.app_context():
                user = User.query.filter_by(telegram_id=user_id).first()

                if not user:
                    self.bot.send_message(
                        message.chat.id,
                        "❌ Вы не зарегистрированы. Используйте /start для начала работы."
                    )
                    return

                settings = get_or_create_user_settings(user.id)

                # Format settings message
                status = "✅ Включены" if settings.reminders_enabled else "❌ Отключены"
                time_str = settings.reminder_time if settings.reminder_time else "20:00 (по умолчанию)"
                tz_str = settings.timezone if settings.timezone else "UTC (по умолчанию)"

                settings_text = (
                    "<b>Настройки уведомлений</b>\n"
                    "Каждый день в указанное время вы будете получать уведомление с итогами дня\n\n"
                    f"<b>Статус:</b> {status}\n"
                    f"<b>Время:</b> {time_str}\n"
                    f"<b>Часовой пояс:</b> {tz_str}\n\n"
                    "<b>Команды для управления:</b>\n"
                    "- <code>/remind on</code> — включить уведомления\n"
                    "- <code>/remind off</code> — отключить уведомления\n"
                    "- <code>/remind time HH:MM</code> — установить время (например: <code>/remind time 21:30</code>)\n"
                    "- <code>/remind tz TIMEZONE</code> — установить часовой пояс (например: <code>/remind tz Europe/Moscow</code>)\n\n"
                    "Примеры часовых поясов:\n"
                    "- <code>Europe/Moscow</code> - МСК\n"
                    "- <code>Asia/Almaty</code> - Алматы\n"
                    "- <code>UTC</code> - UTC"
                )

                self.bot.send_message(
                    message.chat.id,
                    settings_text
                )

        @self.bot.message_handler(commands=['remind'])
        def handle_remind(message):
            """Handle /remind command - manage reminder settings."""
            user_id = message.from_user.id

            with self.app.app_context():
                user = User.query.filter_by(telegram_id=user_id).first()

                if not user:
                    self.bot.send_message(
                        message.chat.id,
                        "❌ Вы не зарегистрированы. Используйте /start для начала работы."
                    )
                    return

                # Parse command arguments
                args = message.text.split()

                if len(args) < 2:
                    self.bot.send_message(
                        message.chat.id,
                        "❌ Неверный формат команды.\n\n"
                        "Используйте:\n"
                        "• `/remind on` - Включить\n"
                        "• `/remind off` - Отключить\n"
                        "• `/remind time HH:MM` - Установить время\n"
                        "• `/remind tz TIMEZONE` - Установить часовой пояс",
                        parse_mode='Markdown'
                    )
                    return

                action = args[1].lower()

                if action == 'on':
                    # Enable reminders
                    update_user_settings(user.id, reminders_enabled=True)
                    self.bot.send_message(
                        message.chat.id,
                        "✅ Уведомления включены"
                    )

                elif action == 'off':
                    # Disable reminders
                    update_user_settings(user.id, reminders_enabled=False)
                    self.bot.send_message(
                        message.chat.id,
                        "❌ Уведомления отключены"
                    )

                elif action == 'time':
                    # Set reminder time
                    if len(args) < 3:
                        self.bot.send_message(
                            message.chat.id,
                            "❌ Укажите время в формате HH:MM\n"
                            "Например: `/remind time 21:30`",
                            parse_mode='Markdown'
                        )
                        return

                    time_str = args[2]

                    # Validate time format
                    try:
                        time_parts = time_str.split(':')
                        if len(time_parts) != 2:
                            raise ValueError("Invalid format")

                        hour = int(time_parts[0])
                        minute = int(time_parts[1])

                        if hour < 0 or hour > 23 or minute < 0 or minute > 59:
                            raise ValueError("Invalid time values")

                        # Update settings
                        update_user_settings(user.id, reminder_time=time_str)

                        self.bot.send_message(
                            message.chat.id,
                            f"✅ Время уведомлений установлено: *{time_str}*",
                            parse_mode='Markdown'
                        )

                    except (ValueError, IndexError):
                        self.bot.send_message(
                            message.chat.id,
                            "❌ Неверный формат времени. Используйте HH:MM (например: 21:30)",
                            parse_mode='Markdown'
                        )

                elif action == 'tz':
                    # Set timezone
                    if len(args) < 3:
                        self.bot.send_message(
                            message.chat.id,
                            "❌ Укажите часовой пояс\n"
                            "Например: `/remind tz Europe/Moscow`\n\n"
                            "Список поясов: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones",
                            parse_mode='Markdown'
                        )
                        return

                    timezone_str = args[2]

                    # Validate timezone
                    try:
                        pytz.timezone(timezone_str)

                        # Update settings
                        update_user_settings(user.id, timezone=timezone_str)

                        self.bot.send_message(
                            message.chat.id,
                            f"✅ Часовой пояс установлен: *{timezone_str}*",
                            parse_mode='Markdown'
                        )

                    except pytz.exceptions.UnknownTimeZoneError:
                        self.bot.send_message(
                            message.chat.id,
                            f"❌ Неизвестный часовой пояс: `{timezone_str}`\n\n"
                            "Примеры:\n"
                            "• Europe/Moscow\n"
                            "• Europe/Kiev\n"
                            "• Asia/Almaty\n"
                            "• UTC\n\n"
                            "Полный список: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones",
                            parse_mode='Markdown'
                        )

                else:
                    self.bot.send_message(
                        message.chat.id,
                        "❌ Неизвестная команда. Используйте:\n"
                        "• `/remind on` - Включить\n"
                        "• `/remind off` - Отключить\n"
                        "• `/remind time HH:MM` - Установить время\n"
                        "• `/remind tz TIMEZONE` - Установить часовой пояс",
                        parse_mode='Markdown'
                    )

    def _reminder_scheduler(self):
        """Background thread that checks and sends reminders based on user settings."""
        logger.info("Reminder scheduler started")

        while not self.stop_reminders.is_set():
            try:
                # Check every minute if there are users to send reminders to
                now_utc = datetime.datetime.now(datetime.timezone.utc)
                current_hour = now_utc.hour
                current_minute = now_utc.minute

                logger.debug(
                    f"Checking for reminders at {current_hour:02d}:{current_minute:02d} UTC")

                # Send reminders to users whose time has come
                if self.reminders_enabled:
                    with self.app.app_context():
                        users_for_reminder = get_users_for_reminder()

                        if users_for_reminder:
                            logger.info(
                                f"Found {len(users_for_reminder)} users for reminders at {current_hour:02d}:{current_minute:02d} UTC")

                            for user_data in users_for_reminder:
                                user = user_data['user']
                                settings = user_data['settings']

                                try:
                                    reminder_text = get_reminder_message(
                                        user.id)

                                    # Try to create inline keyboard with app button
                                    markup = None
                                    if self.mini_app_url:
                                        try:
                                            markup = types.InlineKeyboardMarkup()
                                            app_button = types.InlineKeyboardButton(
                                                text="Открыть приложение",
                                                web_app=types.WebAppInfo(url=self.mini_app_url)
                                            )
                                            markup.add(app_button)
                                        except Exception as btn_error:
                                            logger.warning(f"Failed to create app button: {btn_error}")
                                            markup = None

                                    self.bot.send_message(
                                        user.telegram_id,
                                        reminder_text,
                                        parse_mode='Markdown',
                                        reply_markup=markup
                                    )

                                    logger.info(
                                        f"Sent reminder to user {user.telegram_id} (time: {settings.reminder_time}, tz: {settings.timezone})")

                                    # Small delay to avoid hitting rate limits
                                    time.sleep(0.1)

                                except Exception as e:
                                    logger.error(
                                        f"Failed to send reminder to user {user.telegram_id}: {e}")

                # Wait for the next check interval
                if self.stop_reminders.wait(timeout=Config.REMINDER_CHECK_INTERVAL):
                    # Stop signal received
                    break

            except Exception as e:
                logger.error(f"Error in reminder scheduler: {e}")
                # Wait before retrying
                time.sleep(60)

        logger.info("Reminder scheduler stopped")

    def start_polling(self, non_stop: bool = True):
        """
        Start bot polling in a separate thread.

        Args:
            non_stop: Whether to restart polling on errors
        """
        logger.info("Starting bot polling...")

        # Start reminder scheduler in background
        if self.reminders_enabled:
            self.reminder_thread = threading.Thread(
                target=self._reminder_scheduler, daemon=True)
            self.reminder_thread.start()
            logger.info("Reminder scheduler started")

        # Start polling
        try:
            self.bot.infinity_polling(timeout=10, long_polling_timeout=5)
        except Exception as e:
            logger.error(f"Bot polling error: {e}")
            if non_stop:
                time.sleep(5)
                self.start_polling(non_stop)

    def stop(self):
        """Stop the bot and reminder scheduler."""
        logger.info("Stopping bot...")
        self.stop_reminders.set()

        if self.reminder_thread:
            self.reminder_thread.join(timeout=5)

        self.bot.stop_polling()
        logger.info("Bot stopped")


def create_bot(token: str, app, db, reminder_time: str = "20:00",
               timezone: str = "UTC", reminders_enabled: bool = True) -> CheckBot:
    """
    Create and configure a bot instance.

    Args:
        token: Telegram Bot API token
        app: Flask application instance
        db: SQLAlchemy database instance
        reminder_time: Time to send daily reminders (HH:MM format)
        timezone: Timezone for reminders
        reminders_enabled: Whether to enable daily reminders

    Returns:
        Configured CheckBot instance
    """
    return CheckBot(token, app, db, reminder_time, timezone, reminders_enabled)
