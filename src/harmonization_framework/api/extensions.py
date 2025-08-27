from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def register_extensions(app):
    CORS(app)
    db.init_app(app)
