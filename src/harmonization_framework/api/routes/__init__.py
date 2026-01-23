# src/api/routes/__init__.py

from .rules import rules_blueprint
from .files import files_blueprint
from .health import health_blueprint
from .projects import projects_blueprint

__all__ = [
    "rules_blueprint",
    "files_blueprint",
    "health_blueprint",
    "projects_blueprint",
]
