import os
from flask import Flask
from harmonization_framework.api.extensions import db, register_extensions
from harmonization_framework.api.routes.elements import elements_blueprint
from harmonization_framework.api.routes.files import files_blueprint
from harmonization_framework.api.routes.harmonize import harmonize_blueprint
from harmonization_framework.api.routes.rules import rules_blueprint
from harmonization_framework.api.routes.health import health_blueprint
from harmonization_framework.api.routes.dictionaries import dictionaries_blueprint
from harmonization_framework.api.routes.projects import projects_blueprint

basedir = os.getcwd()
db_path = os.path.join(basedir, "harmonization.db")

def create_app(config_name=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["UPLOAD_FOLDER"] = "uploads"
    
    register_extensions(app)

    app.register_blueprint(rules_blueprint, url_prefix="/harmonization-rules")
    app.register_blueprint(files_blueprint, url_prefix="/data-files")
    app.register_blueprint(harmonize_blueprint, url_prefix="/harmonize")
    app.register_blueprint(elements_blueprint, url_prefix="/data-elements")
    app.register_blueprint(health_blueprint, url_prefix="/health")
    app.register_blueprint(dictionaries_blueprint, url_prefix="/data-dictionaries")
    app.register_blueprint(projects_blueprint, url_prefix="/projects")
    return app
