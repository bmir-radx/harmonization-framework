"""
Sidecar entrypoint for running the FastAPI app as a local service.

This module is intentionally small and explicit so it can be used as the
packaged executable entrypoint (e.g., via PyInstaller).
"""

import os
import sys
import logging
from typing import Optional

import uvicorn

from harmonization_framework.api.app import app

DEFAULT_HOST = "127.0.0.1"
ENV_PORT = "API_PORT"
ENV_HOST = "API_HOST"


def _parse_port(value: str) -> int:
    try:
        port = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{ENV_PORT} must be an integer, got {value!r}") from exc
    if not (1 <= port <= 65535):
        raise ValueError(f"{ENV_PORT} must be in range 1-65535, got {port}")
    return port


def _resolve_host(value: Optional[str]) -> str:
    host = (value or DEFAULT_HOST).strip()
    # Restrict to loopback by default for safety.
    if host not in {"127.0.0.1", "localhost"}:
        raise ValueError(f"{ENV_HOST} must be loopback (127.0.0.1 or localhost), got {host!r}")
    return "127.0.0.1" if host == "localhost" else host


def main() -> None:
    """
    Start the FastAPI sidecar using environment configuration.

    Required:
        API_PORT: port number to bind (chosen by the launcher).
    Optional:
        API_HOST: host to bind, defaults to 127.0.0.1.
    """
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    port_raw = os.getenv(ENV_PORT)
    if not port_raw:
        logging.error("Missing required env var: %s", ENV_PORT)
        sys.exit(2)

    try:
        host = _resolve_host(os.getenv(ENV_HOST))
        port = _parse_port(port_raw)
    except ValueError as exc:
        logging.error(str(exc))
        sys.exit(2)

    # Use uvicorn as the ASGI server for the FastAPI app.
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    main()
