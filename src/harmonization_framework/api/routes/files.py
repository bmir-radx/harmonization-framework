import pandas as pd
import uuid, os, json
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from harmonization_framework.api.extensions import db
from harmonization_framework.api.models import DataFile, HarmonizationRule
from harmonization_framework.rule import HarmonizationRule as hr
from harmonization_framework.rule_store import RuleStore
from harmonization_framework.harmonize import harmonize_dataset
from harmonization_framework.replay_log import replay_logger as rlog

files_blueprint = Blueprint("data-files", __name__)

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

@files_blueprint.route("/<file_id>/harmonize", methods=["POST"])
def harmonize_file(file_id):
    rule_ids = request.json.get("rule_ids")
    if not rule_ids or not isinstance(rule_ids, list):
        return jsonify({"error": "Missing or invalid rule_ids list"}), 400

    data_file = DataFile.query.get(file_id)
    if not data_file:
        return jsonify({"error": "Data file not found"}), 404

    try:
        df = pd.read_csv(data_file.storage_path)
    except Exception as e:
        return jsonify({"error": f"Failed to read data file: {str(e)}"}), 500

    rules = HarmonizationRule.query.filter(HarmonizationRule.id.in_(rule_ids)).all()
    if not rules:
        return jsonify({"error": "No rules found for the given IDs"}), 404

    rule_store = RuleStore()
    harmonization_pairs = []
    for rule in rules:
        try:
            harmonization_rule = hr.from_serialization(json.loads(rule.rule_json))
        except:
            return jsonify({"error": f"Failed to create harmonization rule from serialization: {rule.rule_json}"}), 500
        rule_store.add_rule(harmonization_rule)
        harmonization_pairs.append((harmonization_rule.source, harmonization_rule.target))

    result_id = str(uuid.uuid4()) # id for harmonization run
    logger = rlog.configure_logger(3, os.path.join(current_app.config["UPLOAD_FOLDER"], f"{result_id}.log"))
    try:
        harmonized_df = harmonize_dataset(df, harmonization_pairs, rule_store, data_file.id, logger)
    except:
        return jsonify({"error": "Failed to apply harmonization"}), 500

    result_filename = f"{result_id}_{data_file.filename}_harmonized.csv"
    result_path = os.path.join(current_app.config["UPLOAD_FOLDER"], result_filename)
    try:
        harmonized_df.to_csv(result_path, index=False)
    except Exception as e:
        return jsonify({"error": f"Failed to save result: {str(e)}"}), 500

    result_file = DataFile(
        id=result_id,
        filename=result_filename,
        storage_path=result_path,
        project_id=data_file.project_id,
        dictionary_id=data_file.dictionary_id
    )
    db.session.add(result_file)
    db.session.commit()
    
    return jsonify({"status": "success", "harmonized_file_id": result_id, "harmonization_log": ""})
