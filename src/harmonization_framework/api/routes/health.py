from flask import Blueprint, jsonify

health_blueprint = Blueprint("health", __name__)

@health_blueprint.route("/", methods=["GET"])
def health_check():
    return jsonify(status="ok", message="API is available"), 200
