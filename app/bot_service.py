"""
Service for generating daily summaries and reports for Telegram bot.
"""
import datetime
from typing import List, Dict, Any
from app.models import User, Project, Task, TaskStatus, UserSettings
from app import db
from config import Config
from app.crud import get_or_create_user_settings


def get_daily_summary(user_id: int) -> Dict[str, Any]:
    """
    Generate daily summary for a user.

    Args:
        user_id: User ID in the database

    Returns:
        Dictionary with summary data
    """
    from sqlalchemy.orm import joinedload

    user = User.query.get(user_id)
    if not user:
        return {"error": "User not found"}

    # Get today's start (UTC timezone)
    today_start = datetime.datetime.now(datetime.timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    )

    # Single query to get all projects with their tasks (eager loading)
    projects = Project.query.filter_by(creator_id=user_id)\
        .options(joinedload(Project.tasks))\
        .all()

    if not projects:
        return {
            "user": user,
            "total_projects": 0,
            "completed_today": [],
            "projects_with_pending": [],
            "stale_projects": [],
            "summary_date": datetime.datetime.now(datetime.timezone.utc)
        }

    completed_today = []
    projects_with_pending = []
    stale_projects = []

    for project in projects:
        # Separate tasks by status (tasks already loaded via joinedload)
        completed_today_tasks = [
            t for t in project.tasks
            if t.status == TaskStatus.DONE and t.completed_at and \
            ((t.completed_at if t.completed_at.tzinfo is not None else t.completed_at.replace(tzinfo=datetime.timezone.utc)) >= today_start)
        ]
        pending_tasks_count = sum(
            1 for t in project.tasks if t.status != TaskStatus.DONE)

        # Add to completed list if has completed tasks today
        if completed_today_tasks:
            completed_today.append({
                "project": project,
                "tasks": completed_today_tasks
            })

        # Add to pending list if has pending tasks
        if pending_tasks_count > 0:
            projects_with_pending.append({
                "project": project,
                "pending_count": pending_tasks_count
            })

        # Check staleness
        staleness = project.get_staleness_ratio()
        if staleness >= 0.8:
            stale_projects.append({
                "project": project,
                "staleness_ratio": staleness
            })

    # Sort stale projects by staleness (most stale first)
    stale_projects.sort(key=lambda x: x["staleness_ratio"], reverse=True)

    return {
        "user": user,
        "total_projects": len(projects),
        "completed_today": completed_today,
        "projects_with_pending": projects_with_pending,
        "stale_projects": stale_projects,
        "summary_date": datetime.datetime.now(datetime.timezone.utc)
    }


def format_summary_message(summary: Dict[str, Any]) -> str:
    """
    Format summary data into a readable Telegram message.

    Args:
        summary: Summary data from get_daily_summary()

    Returns:
        Formatted message string
    """
    if "error" in summary:
        return f"❌ {summary['error']}"

    lines = []
    lines.append("📊 *Итоги дня*\n")

    # Completed tasks today
    completed_today = summary.get("completed_today", [])
    if completed_today:
        lines.append("✅ *Выполнено сегодня:*")
        for item in completed_today:
            project = item["project"]
            tasks = item["tasks"]
            lines.append(f"\n*{project.short_name}* ({len(tasks)} задач)")
            for task in tasks[:5]:  # Show max 5 tasks per project
                lines.append(f"  • {task.title}")
            if len(tasks) > 5:
                lines.append(f"  • ... и ещё {len(tasks) - 5}")
        lines.append("")
    else:
        lines.append("Сегодня задачи не выполнялись\n")

    # Projects with pending tasks
    projects_with_pending = summary.get("projects_with_pending", [])
    if projects_with_pending:
        lines.append("📝 *Проекты с незавершёнными задачами:*")
        for item in projects_with_pending:
            project = item["project"]
            count = item["pending_count"]
            lines.append(f"  • *{project.short_name}*: {count} задач")
        lines.append("")

    # Stale projects needing attention
    stale_projects = summary.get("stale_projects", [])
    if stale_projects:
        lines.append("⚠️ *Требуют внимания:*")
        for item in stale_projects[:5]:  # Show max 5 stale projects
            project = item["project"]
            staleness = item["staleness_ratio"]

            # Emoji based on staleness
            if staleness >= 2.0:
                emoji = "🔴"
            elif staleness >= 1.5:
                emoji = "🟠"
            elif staleness >= 1.0:
                emoji = "🟡"
            else:
                emoji = "🟢"

            last_activity = project.get_last_activity_date()
            days_ago = (datetime.datetime.now(datetime.timezone.utc) -
                        last_activity.replace(tzinfo=datetime.timezone.utc)).days

            lines.append(
                f"  {emoji} *{project.short_name}* (последняя активность: {days_ago} дн. назад)")
        lines.append("")

    # Summary stats
    total_completed = sum(len(item["tasks"]) for item in completed_today)
    total_pending = sum(item["pending_count"]
                        for item in projects_with_pending)

    lines.append("📈 *Статистика:*")
    lines.append(f"  • Проектов: {summary['total_projects']}")
    lines.append(f"  • Выполнено сегодня: {total_completed}")
    lines.append(f"  • Осталось задач: {total_pending}")

    return "\n".join(lines)


def get_reminder_message(user_id: int) -> str:
    """
    Generate a reminder message for the user.

    Args:
        user_id: User ID in the database

    Returns:
        Formatted reminder message
    """
    summary = get_daily_summary(user_id)

    if "error" in summary:
        return "❌ Не удалось получить данные"

    # Check if there are any completed tasks or pending work
    completed_today = summary.get("completed_today", [])
    projects_with_pending = summary.get("projects_with_pending", [])
    stale_projects = summary.get("stale_projects", [])

    if not completed_today and not projects_with_pending and not stale_projects:
        return "👋 Время подвести итоги дня!\n\nОткройте приложение и посмотрите свои проекты."

    lines = []
    lines.append("👋 *Время подвести итоги дня!*\n")

    total_completed = sum(len(item["tasks"]) for item in completed_today)
    if total_completed > 0:
        lines.append(f"Сегодня вы выполнили *{total_completed}* задач!")

    if stale_projects:
        lines.append(
            f"\n⚠️ *{len(stale_projects)}* проектов требуют вашего внимания")

    total_pending = sum(item["pending_count"]
                        for item in projects_with_pending)
    if total_pending > 0:
        lines.append(f"\n📝 Осталось *{total_pending}* незавершённых задач")

    lines.append("\nОткройте приложение, чтобы увидеть подробности!")

    return "\n".join(lines)


def get_users_for_reminder() -> List[Dict[str, Any]]:
    """
    Get list of users who should receive reminders at the current time.

    Args:
        current_hour: Current hour in UTC (0-23)
        current_minute: Current minute (0-59)

    Returns:
        List of dictionaries with user and settings
    """
    import pytz

    # Single query with eager loading of settings
    users_with_settings = db.session.query(User, UserSettings)\
        .outerjoin(UserSettings, User.id == UserSettings.user_id)\
        .all()

    users_to_notify = []
    utc_now = datetime.datetime.now(pytz.UTC)

    for user, settings in users_with_settings:
        # Create default settings if not exist
        if not settings:
            settings = get_or_create_user_settings(user.id)

        # Skip if reminders are disabled
        if not settings.reminders_enabled:
            continue

        # Parse reminder time with default fallback
        try:
            reminder_hour, reminder_minute = map(
                int, (settings.reminder_time or Config.DEFAULT_BOT_REMINDER_TIME).split(':'))
        except (ValueError, AttributeError):
            reminder_hour, reminder_minute = 20, 0

        # Get user's timezone with fallback to UTC
        try:
            user_tz = pytz.timezone(settings.timezone or "UTC")
        except pytz.exceptions.UnknownTimeZoneError:
            user_tz = pytz.UTC

        # Convert current UTC time to user's timezone
        user_now = utc_now.astimezone(user_tz)

        # Check if it's time to send reminder
        if user_now.hour == reminder_hour and user_now.minute == reminder_minute:
            users_to_notify.append({
                'user': user,
                'settings': settings
            })

    return users_to_notify
