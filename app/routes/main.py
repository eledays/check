from app import app
from flask import Blueprint, render_template, session, redirect, url_for
from app.forms import HabitForm
from app.crud.habits import get_habits

bp = Blueprint("main", __name__)


@bp.route("/")
def index():
    user_id: int | None = session.get("user_id")

    if user_id is None:
        return render_template("about.html")

    return render_template("index.html", user_id=user_id)


@app.route("/manage")
def manage():
    user_id: int | None = session.get("user_id")

    if user_id is None:
        return redirect(url_for("main.index"))
    
    habits = get_habits(user_id)
    result = []
    for habit in habits:
        form = HabitForm(id=habit.id, name=habit.name)
        result.append(form)

    return render_template("manage.html", habits=result)