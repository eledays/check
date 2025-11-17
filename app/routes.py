from typing import Any
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    jsonify,
    current_app,
)

from app.crud import get_user_projects, create_project
from app.models import Project, User, Task, TaskStatus
from app.forms import ProjectForm, TaskForm
from app.auth import verify_telegram_web_app_data, get_or_create_user
from app import db
from functools import wraps

bp = Blueprint("main", __name__)


def get_current_user() -> User | None:
    """Get current user from session."""
    telegram_id: Any | None = session.get("telegram_id")
    if not telegram_id:
        return None
    return User.query.filter_by(telegram_id=telegram_id).first()


@bp.route("/api/init", methods=["POST"])
def init_webapp():
    """Initialize Telegram Mini App and authenticate user."""
    data = request.get_json()
    init_data = data.get("initData")

    if not init_data:
        return jsonify({"error": "No initData provided"}), 400

    bot_token = current_app.config.get("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        return jsonify({"error": "Bot token not configured"}), 500

    # Verify and parse user data
    user_data = verify_telegram_web_app_data(init_data, bot_token)

    if not user_data:
        return jsonify({"error": "Invalid initData"}), 403

    telegram_id = user_data.get("id")
    if not telegram_id:
        return jsonify({"error": "No user ID in data"}), 400

    # Get or create user
    user = get_or_create_user(telegram_id)

    # Store in session
    session["telegram_id"] = telegram_id
    session.permanent = True

    return jsonify(
        {"success": True, "user": {"id": user.id, "telegram_id": user.telegram_id}}
    )


@bp.route("/")
def index():
    user: User | None = get_current_user()
    if not user:
        # For Mini App, user will be authenticated via JavaScript
        projects = []
    else:
        projects = get_user_projects(user.id)

    return render_template("index.html", projects=projects)


@bp.route("/project/<int:project_id>")
def project_detail(project_id: int):
    user: User | None = get_current_user()
    if not user:
        return "Unauthorized", 401

    project: Project | None = Project.query.get(project_id)
    if project is None:
        return "Project not found", 404

    # Check if user owns this project
    if project.creator_id != user.id:
        return "Access denied", 403

    return render_template("project_page.html", project=project)


@bp.route("/project/new", methods=["GET", "POST"])
def new_project():
    user: User | None = get_current_user()
    if not user:
        return "Unauthorized", 401

    form = ProjectForm()
    if form.validate_on_submit():
        project: Project = create_project(
            name=form.name.data,
            short_name=form.short_name.data,
            description=form.description.data,
            goals=form.goals.data,
            creator_id=user.id,
        )
        return redirect(url_for("main.index"))

    return render_template("new_project.html", form=form)


@bp.route("/api/project/<int:project_id>/task", methods=["POST"])
def create_task(project_id: int):
    """Create a new task for a project via API."""
    user: User | None = get_current_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    project: Project | None = Project.query.get(project_id)
    if project is None:
        return jsonify({"error": "Project not found"}), 404

    # Check if user owns this project
    if project.creator_id != user.id:
        return jsonify({"error": "Access denied"}), 403

    # Use TaskForm for validation and CSRF protection
    form = TaskForm(data=request.get_json(), meta={'csrf': False})
    
    if not form.validate():
        # Return first validation error
        errors = form.errors
        first_error = "Validation error"
        if errors:
            for field_errors in errors.values():
                if field_errors and isinstance(field_errors, list):
                    first_error = str(field_errors[0])
                    break
        return jsonify({"error": first_error}), 400

    # Create new task with validated data
    title = form.title.data
    if not title:
        return jsonify({"error": "Title is required"}), 400
        
    task = Task()
    task.title = title
    task.status = TaskStatus.TODO
    task.project_id = project_id
    
    db.session.add(task)
    db.session.commit()

    # Return the sanitized task data
    return jsonify({
        "success": True,
        "task": {
            "id": task.id,
            "title": task.title,
            "status": task.status.value
        }
    }), 201

