from typing import Any
import datetime
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

from app.crud import get_user_projects, create_project, update_project, update_task, delete_task, delete_project
from app.models import Project, User, Task, TaskStatus
from app.forms import ProjectForm, EditProjectForm, TaskForm
from app.auth import verify_telegram_web_app_data, get_or_create_user
from app import db
from functools import wraps
import logging

bp = Blueprint("main", __name__)
logger = logging.getLogger(__name__)


# Cache for mock user to avoid repeated database queries in development
_mock_user_cache = None


def get_first_form_error(form) -> str:
    """
    Extract the first validation error from a form.
    
    :param form: WTForms form instance
    :return: First error message or generic message if no errors
    """
    errors = form.errors
    if errors:
        for field_errors in errors.values():
            if field_errors and isinstance(field_errors, list):
                return str(field_errors[0])
    return "Validation error"


def get_current_user() -> User | None:
    """Get current user from session."""
    global _mock_user_cache
    
    telegram_id: Any | None = session.get("telegram_id")
    if not telegram_id:
        # In mock mode, auto-authenticate with mock user for development
        if current_app.config.get("TELEGRAM_MOCK", False):
            # Use cached mock user to avoid repeated database queries
            if _mock_user_cache is None:
                mock_telegram_id = 123456789
                _mock_user_cache = get_or_create_user(mock_telegram_id)
                session["telegram_id"] = mock_telegram_id
                session.permanent = True
                logger.info(f"[DEV] Auto-authenticated mock user: {mock_telegram_id}")
            return _mock_user_cache
        return None
    return User.query.filter_by(telegram_id=telegram_id).first()


@bp.route("/api/init", methods=["POST"])
def init_webapp():
    """Initialize Telegram Mini App and authenticate user."""
    try:
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
    except Exception as e:
        logger.error(f"Failed to initialize webapp: {e}")
        return jsonify({"error": "Internal server error"}), 500


@bp.route("/")
def index():
    user: User | None = get_current_user()
    if not user:
        # For Mini App, user will be authenticated via JavaScript
        projects = []
    else:
        projects = get_user_projects(user.id)
    
    # Calculate staleness for each project with pre-calculated last activity dates
    # to avoid N+1 query problem
    if projects:
        # Batch query: get max completed_at for all projects at once
        project_ids = [p.id for p in projects]
        last_activities = db.session.query(
            Task.project_id,
            db.func.max(Task.completed_at).label('last_completed')
        ).filter(
            Task.project_id.in_(project_ids),
            Task.completed_at.isnot(None)
        ).group_by(Task.project_id).all()
        
        # Create lookup dict
        last_activity_map = {proj_id: last_comp for proj_id, last_comp in last_activities}
        
        projects_with_staleness = []
        for project in projects:            
            last_activity = last_activity_map.get(project.id)
            staleness = project.get_staleness_ratio(last_activity)
            projects_with_staleness.append({
                'project': project,
                'staleness_ratio': staleness
            })
    else:
        projects_with_staleness = []

    return render_template("index.html", projects=projects_with_staleness)


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

    # Sort tasks efficiently in SQL: completed tasks first (by completed_at asc - oldest first),
    # then incomplete tasks (by order)
    from sqlalchemy import case
    
    sorted_tasks = Task.query.filter_by(project_id=project_id).order_by(
        # First: sort by completion status (DONE=0, others=1, so DONE comes first)
        case((Task.status == TaskStatus.DONE, 0), else_=1),
        # Second: for completed tasks, sort by completed_at (oldest first)
        # Use a large value for NULL to push them to the end within their group
        case((Task.completed_at.isnot(None), Task.completed_at), else_=datetime.datetime.max.replace(tzinfo=datetime.timezone.utc)),
        # Third: for incomplete tasks, sort by order
        Task.order
    ).all()

    return render_template("project_page.html", project=project, sorted_tasks=sorted_tasks)


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
            periodicity=form.periodicity.data,
        )
        return redirect(url_for("main.index"))

    return render_template("new_project.html", form=form)


@bp.route("/project/<int:project_id>/edit", methods=["GET", "POST"])
def edit_project(project_id: int):
    """Edit an existing project."""
    user: User | None = get_current_user()
    if not user:
        return "Unauthorized", 401

    project: Project | None = Project.query.get(project_id)
    if project is None:
        return "Project not found", 404

    # Check if user owns this project
    if project.creator_id != user.id:
        return "Access denied", 403

    form = EditProjectForm(obj=project)

    if form.validate_on_submit():
        # Update project with validated and sanitized data from form
        updated_project = update_project(
            project_id=project_id,
            name=form.name.data,
            short_name=form.short_name.data,
            description=form.description.data,
            goals=form.goals.data,
            periodicity=form.periodicity.data,
        )

        if updated_project:
            return redirect(url_for("main.project_detail", project_id=project_id))
        else:
            flash("Ошибка при обновлении проекта", "error")

    return render_template("edit_project.html", form=form, project=project)


@bp.route("/project/<int:project_id>/delete", methods=["POST"])
def delete_project_endpoint(project_id: int):
    """Delete a project."""
    user: User | None = get_current_user()
    if not user:
        return "Unauthorized", 401

    project: Project | None = Project.query.get(project_id)
    if project is None:
        return "Project not found", 404

    # Check if user owns this project
    if project.creator_id != user.id:
        return "Access denied", 403

    # Delete the project
    success = delete_project(project_id)
    if success:
        return redirect(url_for("main.index"))
    else:
        return redirect(url_for("main.edit_project", project_id=project_id))


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
        return jsonify({"error": get_first_form_error(form)}), 400

    # Create new task with validated data
    title = form.title.data
    if not title:
        return jsonify({"error": "Title is required"}), 400

    # Get the highest order value for incomplete tasks in this project
    max_order = db.session.query(db.func.max(Task.order)).filter(
        Task.project_id == project_id,
        Task.status != TaskStatus.DONE
    ).scalar() or -1

    task = Task()
    task.title = title
    task.status = TaskStatus.TODO
    task.project_id = project_id
    task.order = max_order + 1  # Add at the end

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


@bp.route("/api/project/<int:project_id>/task/<int:task_id>", methods=["PUT"])
def update_task_endpoint(project_id: int, task_id: int):
    """Update a task title via API."""
    user: User | None = get_current_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    project: Project | None = Project.query.get(project_id)
    if project is None:
        return jsonify({"error": "Project not found"}), 404

    # Check if user owns this project
    if project.creator_id != user.id:
        return jsonify({"error": "Access denied"}), 403

    # Get the task and verify it belongs to this project
    task: Task | None = Task.query.get(task_id)
    if task is None:
        return jsonify({"error": "Task not found"}), 404

    if task.project_id != project_id:
        return jsonify({"error": "Task does not belong to this project"}), 403

    # Use TaskForm for validation
    form = TaskForm(data=request.get_json(), meta={'csrf': False})

    if not form.validate():
        return jsonify({"error": get_first_form_error(form)}), 400

    title = form.title.data
    if not title:
        return jsonify({"error": "Title is required"}), 400

    # Update task
    updated_task = update_task(task_id, title)
    if updated_task is None:
        return jsonify({"error": "Failed to update task"}), 500

    return jsonify({
        "success": True,
        "task": {
            "id": updated_task.id,
            "title": updated_task.title,
            "status": updated_task.status.value
        }
    })


@bp.route("/api/project/<int:project_id>/task/<int:task_id>/status", methods=["PATCH"])
def toggle_task_status(project_id: int, task_id: int):
    """Toggle task status between TODO and DONE."""
    user: User | None = get_current_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    project: Project | None = Project.query.get(project_id)
    if project is None:
        return jsonify({"error": "Project not found"}), 404

    # Check if user owns this project
    if project.creator_id != user.id:
        return jsonify({"error": "Access denied"}), 403

    # Get the task and verify it belongs to this project
    task: Task | None = Task.query.get(task_id)
    if task is None:
        return jsonify({"error": "Task not found"}), 404

    if task.project_id != project_id:
        return jsonify({"error": "Task does not belong to this project"}), 403

    try:
        # Toggle status: TODO <-> DONE (skip IN_PROGRESS for simple toggle)
        if task.status == TaskStatus.DONE:
            task.status = TaskStatus.TODO
            task.completed_at = None  # Clear completion time when unmarking as done
        else:
            task.status = TaskStatus.DONE
            task.completed_at = datetime.datetime.now(
                datetime.timezone.utc)  # Set completion time in UTC

        db.session.commit()

        # Format completed_at with explicit UTC timezone for JavaScript
        completed_at_iso: str | None = None
        if task.completed_at is not None:
            # Ensure timezone-aware datetime and format with Z suffix
            dt = task.completed_at
            if dt.tzinfo is None:  # type: ignore[union-attr]
                # If stored datetime is naive, treat it as UTC
                completed_at_iso = dt.replace(  # type: ignore[union-attr]
                    tzinfo=datetime.timezone.utc).isoformat()
            else:
                completed_at_iso = dt.isoformat()  # type: ignore[union-attr]

        return jsonify({
            "success": True,
            "task": {
                "id": task.id,
                "title": task.title,
                "status": task.status.value,
                "completed_at": completed_at_iso
            }
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to toggle task status for task {task_id}: {e}")
        return jsonify({"error": "Failed to update task status"}), 500


@bp.route("/api/project/<int:project_id>/task/<int:task_id>", methods=["DELETE"])
def delete_task_endpoint(project_id: int, task_id: int):
    """Delete a task via API."""
    user: User | None = get_current_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    project: Project | None = Project.query.get(project_id)
    if project is None:
        return jsonify({"error": "Project not found"}), 404

    # Check if user owns this project
    if project.creator_id != user.id:
        return jsonify({"error": "Access denied"}), 403

    # Get the task and verify it belongs to this project
    task: Task | None = Task.query.get(task_id)
    if task is None:
        return jsonify({"error": "Task not found"}), 404

    if task.project_id != project_id:
        return jsonify({"error": "Task does not belong to this project"}), 403

    # Delete task
    success = delete_task(task_id)
    if not success:
        return jsonify({"error": "Failed to delete task"}), 500

    return jsonify({"success": True})


@bp.route("/api/project/<int:project_id>/tasks/reorder", methods=["POST"])
def reorder_tasks(project_id: int):
    """Reorder incomplete tasks for a project."""
    user: User | None = get_current_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    project: Project | None = Project.query.get(project_id)
    if project is None:
        return jsonify({"error": "Project not found"}), 404

    # Check if user owns this project
    if project.creator_id != user.id:
        return jsonify({"error": "Access denied"}), 403

    data = request.get_json()
    task_ids = data.get("task_ids", [])

    if not task_ids or not isinstance(task_ids, list):
        return jsonify({"error": "Invalid task_ids"}), 400

    try:
        # Update order for each task
        for index, task_id in enumerate(task_ids):
            task: Task | None = Task.query.get(task_id)
            if task and task.project_id == project_id:
                task.order = index

        db.session.commit()
        return jsonify({"success": True})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to reorder tasks for project {project_id}: {e}")
        return jsonify({"error": "Failed to reorder tasks"}), 500
