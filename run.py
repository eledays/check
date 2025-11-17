from flask.app import Flask
from flask_migrate import Migrate
from app import create_app, db
import logging

app: Flask = create_app()
migrate = Migrate(app, db)

if __name__ == "__main__":
    # Suppress SSL/TLS handshake errors in development
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    
    app.run(debug=True, host="0.0.0.0", port=5000)
