# Harmonization Framework

## Installation

To install the harmonization framework, clone the repository, create a virtual environment with the required dependencies, and install the package into your python environment. Use of a virtual environment is recommended.

```bash
git clone git@github.com:bmir-radx/harmonization-framework.git

python3 -m venv venv 
source venv/bin/activate
pip install -r requirements.txt

pip install .
```

## Usage

We recommend using the harmonization framework in an interactive Python environment like a Jupyter notebook. A demonstration is provided in `demo/integration.ipynb`.

### Sidecar (local API service)

The package exposes a small sidecar entrypoint for running the FastAPI backend
as a local service (intended to be launched by an Electron app).

Required environment variables:
- `API_PORT` (required): port to bind.
- `API_HOST` (optional): defaults to `127.0.0.1`.

Example:

```bash
API_PORT=54321 API_HOST=127.0.0.1 harmonization-sidecar
```

When running, the health check is available at:

```
GET http://127.0.0.1:54321/health/
```

Graceful shutdown is supported via:

```
POST http://127.0.0.1:54321/shutdown/
```

Logs are written to stdout/stderr as JSON lines. Optionally, set `API_LOG_PATH`
to also write logs to a file.

### Sidecar packaging (CI)

The repository includes a GitHub Actions workflow that builds the sidecar
executable for macOS, Windows, and Linux. The workflow outputs artifacts:

- `harmonization-sidecar-mac` (tar.gz)
- `harmonization-sidecar-win` (zip)
- `harmonization-sidecar-linux` (tar.gz)

Artifacts are built under:

```
dist/sidecar/<os_short>/
```

## Serialization Format

Harmonization rules and primitives serialize to JSON-friendly dictionaries with a consistent schema:

- Rule shape:
  - `source` (string)
  - `target` (string)
  - `operations` (list of operation dicts)
- Operation shape:
  - `operation` (snake_case identifier)
  - other fields are snake_case
  - numeric values are serialized as numbers (not strings)

Example:

```json
{
  "source": "height_in",
  "target": "height_cm",
  "operations": [
    {"operation": "convert_units", "source_unit": "inch", "target_unit": "cm"},
    {"operation": "round", "precision": 1}
  ]
}
```
