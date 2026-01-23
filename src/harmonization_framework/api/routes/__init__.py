# src/api/routes/__init__.py

from .health import router as health_router

__all__ = [
    "health_router",
]
