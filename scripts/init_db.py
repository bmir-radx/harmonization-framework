from harmonization_framework.api.app import create_app
from harmonization_framework.api.extensions import db

app = create_app()

with app.app_context():
    db.create_all()
    print(app.config["SQLALCHEMY_DATABASE_URI"])
    print("Resolved path:", app.config["SQLALCHEMY_DATABASE_URI"].replace("sqlite:///", ""))
    print("Database Initialized")
