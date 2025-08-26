import uuid, os, csv
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from harmonization_framework.api.extensions import db
from harmonization_framework.api.models import DataDictionary, DataElement

dictionaries_blueprint = Blueprint("data-dictionaries", __name__)

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

@dictionaries_blueprint.route("/<dictionary_id>/extract-data-elements", methods=["POST"])
def extract_elements(dictionary_id):
    try:
        elements = extract_elements_from_dictionary(dictionary_id)
        return jsonify({"created": len(elements), "elements": elements})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def extract_elements_from_dictionary(dictionary_id):
    dictionary = DataDictionary.query.get(dictionary_id)
    if not dictionary:
        raise ValueError("Dictionary not found")

    elements = []
    with open(dictionary.storage_path, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            element = DataElement(
                id=str(uuid.uuid4()),
                name=row.get("Id"),
                description=row.get("Label"),
                datatype=row.get("Datatype"),
                permissible_values=row.get("Enumeration"),
                dictionary_id=dictionary_id,
                project_id=dictionary.project_id,
            )
            db.session.add(element)
            elements.append(element)
    
    db.session.commit()
    return [element.to_dict() for element in elements]
