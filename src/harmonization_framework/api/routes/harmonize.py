import pandas as pd

from flask import Blueprint, jsonify, request
from harmonization_framework.utils.transformations import replay
from harmonization_framework.api.models import HarmonizationRule, DataFile
from werkzeug.utils import secure_filename

harmonize_blueprint = Blueprint("harmonize", __name__)

@harmonize_blueprint.route('/execute', methods=['POST'])
def execute_harmonization():
    """
    Receives request to apply a set of harmonization rules (a 
    harmonization protocol) to a file. Retrieve the file, apply
    the harmonization protocol, save the harmonized result to
    file, return the ID of the harmonized file.
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON payload received"}), 400
    
    f = DataFile.query.get(file_id)
    protocol = data.get("harmonization_protocol")
    harmonized = replay(protocol, {file_id: pd.load_csv(f.storage_path)})

    # save harmonized file
    file_id = str(uuid.uuid4())
    filename = secure_filename(f.filename)
    path = os.path.join(current_app.config["UPLOAD_FOLDER"], f"{file_id}_harmonized_{filename}")
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
