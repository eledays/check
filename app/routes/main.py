from flask import Blueprint, render_template, session

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    user_id: int | None = session.get('user_id')
    if user_id is None:
        return render_template('index.html', user_id=None)
    
    return render_template('index.html', user_id=int(user_id))