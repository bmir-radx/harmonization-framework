# src/api/routes/__init__.py

from .health import router as health_router
from .rpc import router as rpc_router

__all__ = [
    "health_router",
    "rpc_router",
]
