from flask import Blueprint, render_template, session

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    user_id: str | None = session.get('user_id')
    if user_id is None or not user_id.isdigit():
        return render_template('index.html', user_id=None)
    
    return render_template('index.html', user_id=int(user_id))