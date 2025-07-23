import uuid, os
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from harmonization_framework.api.extensions import db
from harmonization_framework.api.models import DataDictionary

dictionaries_blueprint = Blueprint("dictionaries", __name__)

@dictionaries_blueprint.route("/", methods=["GET"])
def list_dictionaries():
    dictionaries = DataDictionary.query.all()
    return jsonify([d.to_dict() for d in dictionaries])

@dictionaries_blueprint.route("/<dictionary_id>", methods=["GET"])
def get_dictionary(dictionary_id):
    dictionary = DataDictionary.query.get(dictionary_id)
    if not dictionary:
        return jsonify({"error": "Dictionary not found"}), 404
    return jsonify(dictionary.to_dict())

@dictionaries_blueprint.route("/", methods=["POST"])
def upload_dictionary():
    file = request.files.get("file")
    if not file:
        return jsonify({"error": "No file uploaded"}), 400

    dictionary_id = str(uuid.uuid4())
    filename = secure_filename(file.filename)
    save_path = os.path.join(current_app.config["UPLOAD_FOLDER"], f"{dictionary_id}_{filename}")
    file.save(save_path)

    new_dict = DataDictionary(
        id=dictionary_id,
        filename=filename,
        storage_path=save_path,
        project_id=request.form.get("project_id")
    )
    db.session.add(new_dict)
    db.session.commit()
    return jsonify({"id": new_dict.id}), 201

@dictionaries_blueprint.route("/<dictionary_id>", methods=["DELETE"])
def delete_dictionary(dictionary_id):
    dictionary = DataDictionary.query.get(dictionary_id)
    if not dictionary:
        return jsonify({"error": "Dictionary not found"}), 404
    db.session.delete(dictionary)
    db.session.commit()
    return jsonify({"status": "deleted"})