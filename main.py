from core import app, db

from db.crud import create_habit, get_user_by_telegram_id
from db.models import User

import web.routes


if __name__ == "__main__":
    app.run(debug=True)
