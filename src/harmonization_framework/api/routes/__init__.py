# src/api/routes/__init__.py

from .rules import rules_blueprint
from .files import files_blueprint
from .harmonize import harmonize_blueprint
from .elements import elements_blueprint
from .dictionaries import dictionaries_blueprint
from .health import health_blueprint

__all__ = [
    "rules_blueprint",
    "files_bp",
    "harmonize_bp",
    "elements_bp",
]
