from flask import Blueprint, render_template, request, redirect, url_for, flash

from app.crud import get_user_projects, create_project
from app.models import Project
from app.forms import ProjectForm
from app import db

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


@bp.route("/project/new", methods=["GET", "POST"])
def new_project():
    # TODO: User authentication
    form = ProjectForm()
    if form.validate_on_submit():
        project = create_project(
            name=form.name.data,
            short_name=form.short_name.data,
            description=form.description.data,
            goals=form.goals.data,
            creator_id=1,
        )
        return redirect(url_for("main.index"))

    return render_template("new_project.html", form=form)