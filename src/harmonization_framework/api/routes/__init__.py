# src/api/routes/__init__.py

from .files import files_blueprint
from .health import health_blueprint

__all__ = [
    "files_blueprint",
    "health_blueprint",
]
