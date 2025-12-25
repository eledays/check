from app import app
from flask import Blueprint, render_template, session, redirect, url_for

bp = Blueprint("habits", __name__)


@app.route('/api/create_habit', methods=['POST'])
def create_habit():
    return redirect(url_for('habits.index'))


@app.route('/api/delete_habit', methods=['POST'])
def delete_habit():
    return redirect(url_for('habits.index'))