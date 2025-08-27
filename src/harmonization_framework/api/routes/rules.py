import json
from flask import Blueprint, jsonify, request
from harmonization_framework.api.extensions import db
from harmonization_framework.api.models import HarmonizationRule
import uuid

rules_blueprint = Blueprint("harmonization-rules", __name__)

@rules_blueprint.route("/", methods=["GET"])
def get_all_rules():
    rules = HarmonizationRule.query.all()
    return jsonify([r.to_dict() for r in rules])

@rules_blueprint.route("/<rule_id>", methods=["GET"])
def get_rule(rule_id):
    rule = HarmonizationRule.query.get(rule_id)
    if not rule:
        return jsonify({"error": "Rule not found"}), 404
    return jsonify(rule.to_dict())

@rules_blueprint.route("/", methods=["POST"])
def create_rule():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON payload received"}), 400
    new_rule = HarmonizationRule(
        id=str(uuid.uuid4()),
        source_target=data.get("source_target"),
        project_id=data.get("project_id"),
        version=data.get("version", 1),
        rule_json=json.dumps(data.get("rule_json"))
    )
    db.session.add(new_rule)
    db.session.commit()
    return jsonify({"id": new_rule.id}), 201

@rules_blueprint.route("/<rule_id>", methods=["PUT"])
def update_rule(rule_id):
    rule = HarmonizationRule.query.get(rule_id)
    if not rule:
        return jsonify({"error": "Rule not found"}), 404
    data = request.get_json()
    if "rule_json" in data:
        rule.rule_json = json.dumps(data["rule_json"])
    db.session.commit()
    return jsonify({"status": "updated"})

@rules_blueprint.route("/<rule_id>", methods=["DELETE"])
def delete_rule(rule_id):
    rule = HarmonizationRule.query.get(rule_id)
    if not rule:
        return jsonify({"error": "Rule not found"}), 404
    db.session.delete(rule)
    db.session.commit()
    return jsonify({"status": "deleted"})
