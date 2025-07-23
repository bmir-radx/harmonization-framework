import uuid, os
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from harmonization_framework.api.extensions import db
from harmonization_framework.api.models import DataFile

files_blueprint = Blueprint("files", __name__)

@files_blueprint.route("/", methods=["POST"])
def upload_file():
    file = request.files.get("file")
    if not file:
        return jsonify({"error": "No file uploaded"}), 400

    file_id = str(uuid.uuid4())
    filename = secure_filename(file.filename)
    path = os.path.join(current_app.config["UPLOAD_FOLDER"], f"{file_id}_{filename}")
    file.save(path)

    data_file = DataFile(
        id=file_id,
        filename=filename,
        storage_path=path,
        project_id=request.form.get("project_id"),
        dictionary_id=request.form.get("dictionary_id")
    )
    db.session.add(data_file)
    db.session.commit()
    return jsonify({"id": file_id}), 201

@files_blueprint.route("/<file_id>", methods=["GET"])
def get_file(file_id):
    f = DataFile.query.get(file_id)
    if not f:
        return jsonify({"error": "File not found"}), 404
    return jsonify(f.to_dict())

@files_blueprint.route("/", methods=["GET"])
def list_files():
    files = DataFile.query.all()
    return jsonify([f.to_dict() for f in files])

@files_blueprint.route("/<file_id>", methods=["DELETE"])
def delete_file(file_id):
    f = DataFile.query.get(file_id)
    if not f:
        return jsonify({"error": "File not found"}), 404
    try:
        if os.path.exists(f.storage_path):
            os.remove(f.storage_path)
    except Exception as e:
        return jsonify({"error": f"Failed to delete file: {str(e)}"}), 500
    db.session.delete(f)
    db.session.commit()
    return jsonify({"status": "deleted"})
