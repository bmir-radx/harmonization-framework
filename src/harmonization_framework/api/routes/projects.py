import uuid
from flask import Blueprint, request, jsonify
from harmonization_framework.api.extensions import db
from harmonization_framework.api.models import Project

projects_blueprint = Blueprint("projects", __name__)

@projects_blueprint.route("/", methods=["GET"])
def list_projects():
    projects = Project.query.all()
    return jsonify([p.to_dict() for p in projects])

@projects_blueprint.route("/<project_id>", methods=["GET"])
def get_project(project_id):
    project = Project.query.get(project_id)
    if not project:
        return jsonify({"error": "Project not found"}), 404
    return jsonify(project.to_dict())

@projects_blueprint.route("/", methods=["POST"])
def create_project():
    data = request.get_json()
    new_project = Project(
        id=str(uuid.uuid4()),
        name=data.get("name"),
        description=data.get("description")
    )
    db.session.add(new_project)
    db.session.commit()
    return jsonify({"id": new_project.id}), 201

@projects_blueprint.route("/<project_id>", methods=["PUT"])
def update_project(project_id):
    project = Project.query.get(project_id)
    if not project:
        return jsonify({"error": "Project not found"}), 404
    data = request.get_json()
    project.name = data.get("name", project.name)
    project.description = data.get("description", project.description)
    db.session.commit()
    return jsonify({"status": "updated"})

@projects_blueprint.route("/<project_id>", methods=["DELETE"])
def delete_project(project_id):
    project = Project.query.get(project_id)
    if not project:
        return jsonify({"error": "Project not found"}), 404
    db.session.delete(project)
    db.session.commit()
    return jsonify({"status": "deleted"})
