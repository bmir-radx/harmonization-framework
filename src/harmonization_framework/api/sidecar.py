"""
Sidecar entrypoint for running the FastAPI app as a local service.

This module is intentionally small and explicit so it can be used as the
packaged executable entrypoint (e.g., via PyInstaller).
"""

import os
import sys
import json
import logging
from datetime import datetime, timezone
from typing import Optional, List

import uvicorn

from harmonization_framework.api.app import app

DEFAULT_HOST = "127.0.0.1"
ENV_PORT = "API_PORT"
ENV_HOST = "API_HOST"
ENV_LOG_PATH = "API_LOG_PATH"


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


class _JsonLogFormatter(logging.Formatter):
    """Format log records as compact JSON lines for stdout/stderr capture."""
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        return json.dumps(payload, separators=(",", ":"))


def _configure_logging(log_path: Optional[str]) -> List[logging.Handler]:
    """
    Configure structured logging to stdout and optionally to a log file.
    """
    formatter = _JsonLogFormatter()
    handlers: List[logging.Handler] = []

    stream_handler = logging.StreamHandler(stream=sys.stdout)
    stream_handler.setFormatter(formatter)
    handlers.append(stream_handler)

    if log_path:
        try:
            file_handler = logging.FileHandler(log_path)
        except OSError as exc:
            raise ValueError(f"{ENV_LOG_PATH} is not writable: {log_path}") from exc
        file_handler.setFormatter(formatter)
        handlers.append(file_handler)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers = handlers

    # Ensure uvicorn loggers use the same handlers/format.
    for logger_name in ("uvicorn.error", "uvicorn.access"):
        logger = logging.getLogger(logger_name)
        logger.handlers = handlers
        logger.setLevel(logging.INFO)
        logger.propagate = False

    return handlers


def main() -> None:
    """
    Start the FastAPI sidecar using environment configuration.

    Required:
        API_PORT: port number to bind (chosen by the launcher).
    Optional:
        API_HOST: host to bind, defaults to 127.0.0.1.
    """
    log_path = os.getenv(ENV_LOG_PATH)
    try:
        _configure_logging(log_path)
    except ValueError as exc:
        logging.error(str(exc))
        sys.exit(2)

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
