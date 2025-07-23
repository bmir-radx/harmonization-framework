import uuid
from flask import Blueprint, request, jsonify
from harmonization_framework.api.extensions import db
from harmonization_framework.api.models import DataElement

elements_blueprint = Blueprint("elements", __name__)

@elements_blueprint.route("/", methods=["GET"])
def list_elements():
    dictionary_id = request.args.get("dictionary_id")
    if dictionary_id:
        elements = DataElement.query.filter_by(dictionary_id=dictionary_id).all()
    else:
        elements = DataElement.query.all()
    return jsonify([e.to_dict() for e in elements])

@elements_blueprint.route("/<element_id>", methods=["GET"])
def get_element(element_id):
    element = DataElement.query.get(element_id)
    if not element:
        return jsonify({"error": "Element not found"}), 404
    return jsonify(element.to_dict())

@elements_blueprint.route("/", methods=["POST"])
def create_element():
    data = request.get_json()
    element = DataElement(
        id=str(uuid.uuid4()),
        name=data.get("name"),
        description=data.get("description"),
        datatype=data.get("datatype"),
        permissible_values=data.get("permissible_values"),
        dictionary_id=data.get("dictionary_id")
    )
    db.session.add(element)
    db.session.commit()
    return jsonify({"id": element.id}), 201

@elements_blueprint.route("/<element_id>", methods=["DELETE"])
def delete_element(element_id):
    element = DataElement.query.get(element_id)
    if not element:
        return jsonify({"error": "Element not found"}), 404
    db.session.delete(element)
    db.session.commit()
    return jsonify({"status": "deleted"})
