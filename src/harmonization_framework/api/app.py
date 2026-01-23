from flask import Flask
from harmonization_framework.api.extensions import register_extensions
from harmonization_framework.api.routes.health import health_blueprint

def create_app(config_name=None):
    app = Flask(__name__, instance_relative_config=True)
    
    register_extensions(app)

    app.register_blueprint(health_blueprint, url_prefix="/health")
    return app
