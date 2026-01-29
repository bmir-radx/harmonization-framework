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

### Electron consumption (high level)

Electron should consume the per-OS artifact produced by the packaging workflow,
unpack it into the app's bundled resources, and launch the sidecar binary at
runtime. The launcher sets `API_PORT` (and optionally `API_HOST`) and then polls
`/health/` before issuing API calls.

See `docs/electron_sidecar.md` for the full packaging and launch guide.

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

## Primitives Reference

The table below lists the available primitives, their purpose, and settings.
All settings are provided in the operation dict for rule serialization.

| Operation | Purpose | Settings |
| --- | --- | --- |
| `bin` | Bucket numeric values into non-overlapping ranges; returns the bin label. | `bins`: list of `{label,start,end}` (ranges must not overlap; inclusive bounds) |
| `cast` | Convert values between primitive types. | `source`: type<br>`target`: type (`text`, `integer`, `boolean`, `decimal`, `float`); boolean casting accepts common string/number forms |
| `convert_date` | Convert date/time strings between formats. | `source_format`, `target_format` (strftime patterns; raises if parsing fails) |
| `convert_units` | Convert numeric values between units using pint. | `source_unit`, `target_unit` (Unit enum or pint string; raises on invalid units) |
| `do_nothing` | No-op transform (pass-through). | None |
| `enum_to_enum` | Map discrete values to other values. | `mapping` (dict)<br>`strict` (bool, default `false`)<br>`default` (optional) |
| `format_number` | Format numeric values with fixed decimal places. | `precision` (int, >=0); output is text (string) |
| `normalize_boolean` | Normalize truthy/falsy values to booleans. | `truthy` (list, optional; defaults below)<br>`falsy` (list, optional; defaults below)<br>`strict` (bool, default `true`)<br>`default` (optional; used when `strict=false`) |
| `normalize_text` | Apply a single text normalization. | `normalization` (`strip`, `lower`, `upper`, `remove_accents`, `remove_punctuation`, `remove_special_characters`) |
| `offset` | Add an offset to numeric values. | `offset` (number) |
| `reduce` | Reduce a list of values to one value. | `reduction` (`any`, `none`, `all`, `one-hot`, `sum`); expects a list/tuple input; one-hot returns index or None |
| `round` | Round numeric values to a given precision. | `precision` (int, >=0); uses Python `round` semantics |
| `scale` | Multiply numeric values by a factor. | `scaling_factor` (number) |
| `substitute` | Regex-based string substitution. | `expression` (regex; validated)<br>`substitution` (replacement) |
| `threshold` | Clamp numeric values between bounds. | `lower`, `upper` (numbers; lower <= upper; output type follows numeric promotion) |
| `truncate` | Cut strings to a max length. | `length` (int, >=0) |

Defaults for `normalize_boolean` (used when `truthy`/`falsy` are not provided):
- truthy: `["true","t","yes","y","1",1,true,"on"]`
- falsy: `["false","f","no","n","0",0,false,"off",""]`

### Primitive examples

Each operation is represented by a JSON-friendly dict. Examples:

| Operation | Example |
| --- | --- |
| `bin` | `{"operation":"bin","bins":[{"label":"low","start":0,"end":9},{"label":"high","start":10,"end":19}]}` |
| `cast` | `{"operation":"cast","source":"text","target":"integer"}` |
| `convert_date` | `{"operation":"convert_date","source_format":"%Y-%m-%d","target_format":"%m/%d/%Y"}` |
| `convert_units` | `{"operation":"convert_units","source_unit":"inch","target_unit":"cm"}` |
| `do_nothing` | `{"operation":"do_nothing"}` |
| `enum_to_enum` | `{"operation":"enum_to_enum","mapping":{"BL":"baseline","FU":"follow_up"},"strict":false,"default":"unknown"}` |
| `format_number` | `{"operation":"format_number","precision":2}` |
| `normalize_boolean` | `{"operation":"normalize_boolean","truthy":["yes","y","1"],"falsy":["no","n","0"],"strict":true}` |
| `normalize_text` | `{"operation":"normalize_text","normalization":"lower"}` |
| `offset` | `{"operation":"offset","offset":2.5}` |
| `reduce` | `{"operation":"reduce","reduction":"one-hot"}` |
| `round` | `{"operation":"round","precision":2}` |
| `scale` | `{"operation":"scale","scaling_factor":0.453592}` |
| `substitute` | `{"operation":"substitute","expression":",","substitution":" "}` |
| `threshold` | `{"operation":"threshold","lower":0,"upper":100}` |
| `truncate` | `{"operation":"truncate","length":3}` |

### NormalizeBoolean defaults

If you use the `normalize_boolean` primitive without specifying `truthy` or
`falsy` lists, the following defaults are applied:

- truthy: `["true", "t", "yes", "y", "1", 1, true, "on"]`
- falsy: `["false", "f", "no", "n", "0", 0, false, "off", ""]`
