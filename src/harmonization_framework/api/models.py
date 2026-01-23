import json
from datetime import datetime
from harmonization_framework.api.extensions import db

class HarmonizationRule(db.Model):
    id = db.Column(db.String, primary_key=True)
    source_target = db.Column(db.String, index=True)
    project_id = db.Column(db.String, index=True)
    version = db.Column(db.Integer, default=1)
    rule_json = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now())

    def to_dict(self):
        return {
            "id": self.id,
            "source_target": self.source_target,
            "project_id": self.project_id,
            "version": self.version,
            "rule_json": json.loads(self.rule_json),
            "created_at": self.created_at.isoformat()
        }

class DataFile(db.Model):
    id = db.Column(db.String, primary_key=True)
    filename = db.Column(db.String)
    storage_path = db.Column(db.String)
    project_id = db.Column(db.String, index=True)
    uploaded_at = db.Column(db.DateTime, default=datetime.now())
    dictionary_id = db.Column(db.String, db.ForeignKey("data_dictionary.id"))

    def to_dict(self):
        return {
            "id": self.id,
            "filename": self.filename,
            "storage_path": self.storage_path,
            "project_id": self.project_id,
            "uploaded_at": self.uploaded_at.isoformat() if self.uploaded_at else None,
            "dictionary_id": self.dictionary_id
        }

class DataDictionary(db.Model):
    id = db.Column(db.String, primary_key=True)
    filename = db.Column(db.String)
    storage_path = db.Column(db.String)
    project_id = db.Column(db.String, index=True)
    uploaded_at = db.Column(db.DateTime, default=datetime.now())

    data_files = db.relationship("DataFile", backref="dictionary", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "filename": self.filename,
            "storage_path": self.storage_path,
            "project_id": self.project_id,
            "uploaded_at": self.uploaded_at.isoformat() if self.uploaded_at else None
        }

class Project(db.Model):
    id = db.Column(db.String, primary_key=True)
    name = db.Column(db.String, nullable=False)
    description = db.Column(db.String)
    created_at = db.Column(db.DateTime, default=datetime.now())

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
