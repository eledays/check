from flask import Blueprint, render_template

from app.crud import get_user_projects
from app.models import Project

bp = Blueprint("main", __name__)


@bp.route("/")
def index():
    projects: list[Project] = get_user_projects(1)
    return render_template("index.html", projects=projects)
