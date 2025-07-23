from flask import Blueprint, jsonify, request
from harmonization_framework.utils.transformations import harmonize_dataset
from harmonization_framework.api.models import HarmonizationRule, DataFile

harmonize_blueprint = Blueprint("harmonize", __name__)

@harmonize_blueprint.route('/execute', methods=['POST'])
def execute_harmonization():
    data = request.get_json()
    rule_ids = data.get('rules', [])
    file_ids = data.get('data_files', [])

    rules = HarmonizationRule.query.filter(HarmonizationRule.id.in_(rule_ids)).all()
    files = DataFile.query.filter(DataFile.id.in_(file_ids)).all()

    if not rules or not files:
        return jsonify({'error': 'Rules or files not found'}), 400

    # TODO: real harmonization here
    result = {
        'applied_rules': [r.id for r in rules],
        'target_files': [f.id for f in files],
        'status': 'harmonization complete'
    }
    return jsonify(result), 200
