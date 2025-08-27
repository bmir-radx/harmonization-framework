from harmonization_framework.api.app import create_app
from harmonization_framework.api.extensions import db
import os

app = create_app()

with app.app_context():
    db.create_all()
    print(app.config["SQLALCHEMY_DATABASE_URI"])
    print("Resolved path:", app.config["SQLALCHEMY_DATABASE_URI"].replace("sqlite:///", ""))
    print("Database Initialized")

    upload_path = app.config["UPLOAD_FOLDER"]
    if not os.path.exists(upload_path):
        os.makedirs(upload_path)
        print(f"Created uploads folder at: {upload_path}")
    else:
        print(f"Uploads folder already exists at: {upload_path}")
