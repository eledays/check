from flask import Blueprint, render_template

from app.crud import get_user_projects
from app.models import Project

bp = Blueprint("main", __name__)


@bp.route("/")
def index():
    projects: list[Project] = get_user_projects(1)
    return render_template("index.html", projects=projects)


@bp.route("/project/<int:project_id>")
def project_detail(project_id: int):
    # TODO: User authentication
    project: Project | None = Project.query.get(project_id)
    if project is None:
        return "Project not found", 404
    return render_template("project_page.html", project=project)
