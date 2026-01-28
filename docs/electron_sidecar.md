# Electron Sidecar Packaging & Launch Guide

This document explains how to package, bundle, and launch the FastAPI sidecar
from an Electron app. It is intended for the Electron engineer integrating the
backend sidecar.

## 1) What to package (per OS)
Use the GitHub Actions **Sidecar Packaging** workflow artifacts:

- **macOS**: `harmonization-sidecar-mac` (tar.gz)
- **Windows**: `harmonization-sidecar-win` (zip)
- **Linux**: `harmonization-sidecar-linux` (tar.gz)

Each artifact contains a PyInstaller **onedir** bundle:
```
harmonization-sidecar/
  harmonization-sidecar[.exe]
  _internal/    (runtime + dependencies)
```

Do **not** delete `_internal`. It is required at runtime.

## 2) Where to place it in the Electron app
Unpack into your app resources, e.g.:
```
<app_root>/resources/sidecar/<os>/
  harmonization-sidecar/
    harmonization-sidecar(.exe)
    _internal/
```

## 3) How to launch the sidecar (env + process)
The launcher must set environment variables and then spawn the binary.

**Required env vars**
- `API_PORT` (required): port chosen by the launcher
- `API_HOST` (optional): defaults to `127.0.0.1`
- `API_LOG_PATH` (optional): file path for logs in addition to stdout/stderr

**How Electron sets env vars and starts the process**
Electron’s main process uses Node.js process APIs. To pass env vars, use
`child_process.spawn()` (or similar) and pass an `env` object that extends
`process.env`. This is standard Node.js behavior; see the Node.js `child_process`
documentation for details. citeturn0search6

Note: On Windows, environment variable keys are case-insensitive. Avoid
duplicating keys with different casing (e.g., `PATH` vs `Path`). citeturn0search6

## 4) Readiness
After spawn, poll:
```
GET http://127.0.0.1:<API_PORT>/health/
```
Ready when HTTP 200 is returned.

## 5) Shutdown
Preferred:
```
POST http://127.0.0.1:<API_PORT>/shutdown/
```
Fallback: terminate the process (SIGTERM on mac/Linux, CTRL_BREAK on Windows).

## 6) Logging
Logs are JSON lines to stdout/stderr (capturable by Electron). Optionally set
`API_LOG_PATH` to write logs to a file.
