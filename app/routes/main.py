from app import app
from flask import Blueprint, render_template, session, redirect, url_for, request, abort
from app.forms import HabitForm
from app.crud.habits import get_habits, create_or_update_habit, delete_habit

import logging


bp = Blueprint("main", __name__)
logger = logging.getLogger(__name__)


@bp.route("/")
def index():
    user_id: int | None = session.get("user_id")

    if user_id is None:
        return render_template("about.html")

    return render_template("index.html", user_id=user_id)


@bp.route("/manage", methods=["GET", "POST"])
def manage():
    user_id: int | None = session.get("user_id")

    if user_id is None:
        return redirect(url_for("main.index"))

    if request.method == "POST":
        habit_id = request.form.get("id")
        name = request.form.get("name", "")
        delete = request.form.get("delete", False)
        submit = request.form.get("submit", False)

        if habit_id and habit_id.isdigit():
            habit_id = int(habit_id)
        else:
            logger.error('Invalid habit_id while updating or deleting habit')
            return abort(400)
        
        if not name.strip() or (not delete and not submit) or (delete and submit):
            logger.error('Invalid data while updating or deleting habit')
            return abort(400)
        
        if submit:
            habit = create_or_update_habit(habit_id, name, user_id)
        elif delete:
            delete_habit(habit_id)

        return redirect(url_for('main.manage'))

    habits = get_habits(user_id)
    result = []
    for habit in habits:
        print(habit.id, habit.name)
        form = HabitForm(id=habit.id, name=habit.name)
        result.append(form)

    return render_template("manage.html", habits=result)
