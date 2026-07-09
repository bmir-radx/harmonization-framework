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

To use only the command-line tools (`harmonize` and `harmonization-sidecar`) without setting up a development environment, install with [pipx](https://pipx.pypa.io/), which puts the commands on your PATH in an isolated environment:

```bash
pipx install git+https://github.com/bmir-radx/harmonization-framework.git
```

To pin a specific release, append a tag (e.g. `...framework.git@v0.1.0`). To pick up the latest changes later, run `pipx reinstall harmonization-framework` — for packages installed from a git URL this is more reliable than `pipx upgrade`.

## Releases

Every pull request merged to `main` automatically bumps the version in `pyproject.toml` and tags the release (`vX.Y.Z`) via the Bump Version workflow. By default the patch version is bumped; label the PR `release:minor` or `release:major` for a larger bump, or `release:skip` to not release at all.

## Usage

The harmonization framework in an interactive Python environment like a Jupyter notebook. A demonstration is provided in `demo/integration.ipynb` or it can be used as a CLI tool.

### CLI

Run harmonization from the command line with the `harmonize` CLI.

Example:

```bash
harmonize \
  --rules rules/radx_up_rules.json \
  --rules rules/radx_rad_rules.json \
  --input data.csv \
  --output harmonized.csv \
  --on-missing warn
```

Notes:
- Rules files may be JSON or YAML; the format is chosen by file extension (`.yaml`/`.yml` for YAML, otherwise JSON). `--rules` can be given multiple times to merge files.
- Input/output format is auto-detected by file extension (`.csv`/`.tsv`).
- `--on-missing` controls what happens when a rule's source columns are absent from the input: `error` (default), `warn` (warn and skip), or `skip` (skip silently). A rule is skipped if *any* of its source columns is missing.
- By default only target columns are written. Add `--include-metadata` to include `source dataset` and `original_id`.
- Restrict outputs with `--targets nih_age,nih_sex`.
- `--dataset-name` sets the dataset name used for metadata columns (defaults to the input file name).
#### Listing the available operations

To see which primitive operations can be used in a rules file, run:

```bash
harmonize --list-operations
```

This prints every operation with a short description, for example:

```
convert_units
  Convert numeric values from `source_unit` to `target_unit` — for example
  `inch` to `cm`, or `kilogram` to `pound`.

do_nothing
  Pass the value through unchanged. Takes no settings.
```

The descriptions are taken from the primitive implementations themselves, so the listing always matches the operations the installed version actually supports. Each description names the operation's settings (in backticks), matching the fields used in rules files.

For a machine-readable listing, add `--format json`:

```bash
harmonize --list-operations --format json
```

Each entry then contains the operation name, its one-line summary, and its full help text:

```json
[
  {
    "operation": "case",
    "summary": "Choose one of several branches by switching on a selector source, ...",
    "help": "... full help text, including complete authoring examples ..."
  }
]
```

The JSON form is intended for tools and AI agents that generate or edit rules files: the `help` field carries the full documentation for each operation — including complete authoring examples for `case` and `coalesce` — so an agent can write valid operations rather than just name them.

#### Validating rules files

Check rules files (JSON or YAML) without running a harmonization by adding `--validate`; `--input` and `--output` are not required:

```bash
harmonize --validate \
  --rules rules/radx_up_rules.json \
  --rules rules/radx_rad_rules.yaml
```

Each file is checked independently and every problem is reported — syntax errors, missing or malformed `sources`/`target`/`operations`, unknown operations, invalid operation settings, duplicate targets within a file, and empty files. An unknown operation gets a did-you-mean suggestion and a pointer to `--list-operations`. Prints `OK` or `INVALID` per file and exits with a non-zero status if any file has problems, so it can gate a CI step.

## Serialization Format

Harmonization rules and primitives serialize to JSON-friendly dictionaries with a consistent schema. A rules file is a flat array of rule dicts, written as JSON or YAML depending on the file extension (`.yaml`/`.yml` for YAML, otherwise JSON) — both encode the same structure.

- Rule shape:
  - `sources` (list of source variable names)
  - `target` (target variable name)
  - `operations` (list of operation dicts)
  - `metadata` (optional dict of free-form annotations)
- Operation shape:
  - `operation` (snake_case identifier - see table below)
  - other fields are snake_case
  - numeric values are serialized as numbers (not strings)

Example (JSON):

```json
{
  "sources": ["height_in"],
  "target": "height_cm",
  "operations": [
    {"operation": "convert_units", "source_unit": "inch", "target_unit": "cm"},
    {"operation": "round", "precision": 1}
  ]
}
```

The same rule in YAML:

```yaml
- sources: [height_in]
  target: height_cm
  operations:
  - {operation: convert_units, source_unit: inch, target_unit: cm}
  - {operation: round, precision: 1}
```

## Multi-Source Rules

Most rules read one column and write one column. Sometimes, though, a single harmonized value has to be assembled from several columns. Two situations come up all the time in real datasets:

1. The same measurement lives in *different columns depending on how it was recorded* — for example, weight was entered in `weight_lbs` **or** `weight_kgs`, with a `weight_units` column saying which one was used for each row.
2. One measurement is *split across columns that must be combined* — for example, height recorded as `height_ft` plus `height_in`.

To handle these, list every column the rule needs in `sources`, and use the `case` or `coalesce` operation to say how to pick or combine them.

### `case`: pick a column based on a flag

Use `case` when the data has a flag column that says where the real value is. `case` looks at one column (the `selector`) and picks a branch by its value. Each branch reads: *when the flag has one of these values (`when`), take the value from this column (`source`) and run these operations on it.*

Here, `weight_units` is `2` when the weight was entered in pounds and `1` when it was entered in kilograms:

```yaml
- sources: [weight_units, weight_lbs, weight_kgs]
  target: nih_weight
  operations:
  - operation: case
    sources: [weight_units, weight_lbs, weight_kgs]
    selector: weight_units
    branches:
    - when: ['2']              # flag says pounds...
      operands:
      - source: weight_lbs     # ...use weight_lbs unchanged
        operations:
        - {operation: do_nothing}
    - when: ['1']              # flag says kilograms...
      operands:
      - source: weight_kgs     # ...convert weight_kgs to pounds
        operations:
        - {operation: convert_units, source_unit: kilogram, target_unit: pound}
        - {operation: round, precision: 0}
    default: null              # flag missing or unrecognized -> null
```

Row by row this means: if `weight_units` is 2, `nih_weight` is `weight_lbs` as-is (`do_nothing` marks "use unchanged"). If it is 1, `nih_weight` is `weight_kgs` converted to pounds and rounded. If the flag is blank or has any other value, `nih_weight` is null.

Flag values in `when` are written as text, but numeric flags match anyway: a `2` or `2.0` read from CSV matches `when: ['2']`.

### `coalesce`: use whichever column is filled in

Use `coalesce` when there is no flag column — each row simply has its value in one column or the other. Branches are tried in order and the first one whose column is non-empty wins:

```yaml
- sources: [weight_lbs, weight_kgs]
  target: nih_weight
  operations:
  - operation: coalesce
    sources: [weight_lbs, weight_kgs]
    branches:
    - operands:
      - source: weight_lbs     # prefer weight_lbs when present
        operations:
        - {operation: do_nothing}
    - operands:
      - source: weight_kgs     # otherwise fall back to weight_kgs
        operations:
        - {operation: convert_units, source_unit: kilogram, target_unit: pound}
        - {operation: round, precision: 0}
    default: null              # both empty -> null
```

Row by row: if `weight_lbs` has a value, use it. Otherwise, if `weight_kgs` has a value, convert it to pounds. If both are empty, `nih_weight` is null.

### Adding columns together in a branch

A branch can also combine several columns. List each column under `operands` with the operations that prepare it, and set `combine` to how the prepared values are merged (for example `sum`). Here, height was recorded as feet plus inches, and the harmonized value is total inches:

```yaml
- when: ['1']                  # flag says feet-and-inches
  combine: sum                 # add the prepared values together
  operands:
  - source: height_ft
    operations:
    - {operation: convert_units, source_unit: foot, target_unit: inch}
  - source: height_in
    operations:
    - {operation: do_nothing}
```

That is: convert `height_ft` to inches, leave `height_in` as it is, and add the two.

### Multi-source rules without branching

If every source column should get the *same* treatment and then be merged — for example, a set of 0/1 checkbox columns collapsing into one code — no branching is needed: use `map_each` to apply an operation chain to every value, followed by `reduce` to merge the results (see the Primitives Reference below).

## Primitives Reference

The table below lists the available primitives, their purpose, and settings.
All settings are provided in the operation dict for rule serialization.

| Operation | Purpose | Settings |
| --- | --- | --- |
| `bin` | Bucket numeric values into non-overlapping ranges; returns the bin label. | `bins`: list of `{label,start,end}` (ranges must not overlap; inclusive bounds) |
| `case` | Multi-source combinator: switch on a selector column to choose which branch computes the value (see [Multi-Source Rules](#multi-source-rules)). | `sources` (list of column names)<br>`selector` (must be in `sources`)<br>`branches`: list of `{when, operands, combine}`<br>`default` (optional) |
| `cast` | Convert values between primitive types. | `source`: type<br>`target`: type (`text`, `integer`, `boolean`, `decimal`, `float`); boolean casting accepts common string/number forms |
| `coalesce` | Multi-source combinator: first branch whose primary source is non-null wins (see [Multi-Source Rules](#multi-source-rules)). | `sources` (list of column names)<br>`branches`: list of `{operands, combine}` in precedence order<br>`default` (optional) |
| `convert_date` | Convert date/time strings between formats. | `source_format`, `target_format` (strftime patterns; raises if parsing fails) |
| `convert_units` | Convert numeric values between units using pint. | `source_unit`, `target_unit` (Unit enum or pint string; raises on invalid units) |
| `do_nothing` | No-op transform (pass-through). | None |
| `enum_to_enum` | Map discrete values to other values. | `mapping` (list of `{from,to}` entries; keys keep their native JSON type)<br>`strict` (bool, default `false`)<br>`default` (optional) |
| `extract_regex` | Extract a value from a string via a regex capture group. | `expression` (regex; validated)<br>`group` (int or group name, default `1`)<br>`flags` (optional list: `IGNORECASE`, `MULTILINE`, `DOTALL`)<br>`strict` (bool, default `true`)<br>`default` (optional; used when `strict=false`) |
| `format_number` | Format numeric values with fixed decimal places. | `precision` (int, >=0); output is text (string) |
| `map_each` | Apply a nested operation chain to each element of a list. | `operations` (list of operation dicts); input must be a list/tuple; null elements raise |
| `missing_code` | Map in-band missing-value codes (e.g. `-999`, `"UNK"`) to real nulls; all other values pass through. | `codes`: list of `{code,label}` entries; should be the FIRST operation in a rule's chain |
| `normalize_boolean` | Normalize truthy/falsy values to booleans. | `truthy` (list, optional; defaults below)<br>`falsy` (list, optional; defaults below)<br>`strict` (bool, default `true`)<br>`default` (optional; used when `strict=false`) |
| `normalize_text` | Apply a single text normalization. | `normalization` (`strip`, `lower`, `upper`, `remove_accents`, `remove_punctuation`, `remove_special_characters`) |
| `offset` | Add an offset to numeric values. | `offset` (number) |
| `parse_array` | Parse array-like values into a list for downstream operations. | `format` (`json` default, `delimiter`)<br>`delimiter` (string; used for `delimiter` format, default `|`, supports `\\n` for newline)<br>`item_type` (`auto`, `string`, `integer`, `float`, `boolean`)<br>`strict` (bool, default `true`)<br>`default` (optional; used when `strict=false`)<br>`allow_singleton` (bool, default `false`) |
| `reduce` | Reduce a list of values to one value. | `reduction` (`any`, `none`, `all`, `one-hot`, `sum`); expects a list/tuple input; one-hot returns index or None |
| `round` | Round numeric values to a given precision. | `precision` (int, >=0); uses Python `round` semantics |
| `scale` | Multiply numeric values by a factor. | `scaling_factor` (number) |
| `substitute` | Regex-based string substitution. | `expression` (regex; validated)<br>`substitution` (replacement) |
| `threshold` | Clamp numeric values between bounds. | `lower`, `upper` (numbers; lower <= upper; output type follows numeric promotion) |
| `truncate` | Cut strings to a max length. | `length` (int, >=0) |
| `validate_pattern` | Assert a string matches a regex; returns the original value on success. | `expression` (regex; validated)<br>`mode` (`match` default, `fullmatch`, `search`)<br>`flags` (optional list: `IGNORECASE`, `MULTILINE`, `DOTALL`)<br>`strict` (bool, default `true`; raises on mismatch)<br>`default` (optional; used when `strict=false`) |

Defaults for `normalize_boolean` (used when `truthy`/`falsy` are not provided):
- truthy: `["true","t","yes","y","1",1,true,"on"]`
- falsy: `["false","f","no","n","0",0,false,"off",""]`

### Primitive examples

Each operation is represented by a JSON-friendly dict. Examples:

| Operation | Example |
| --- | --- |
| `bin` | `{"operation":"bin","bins":[{"label":"low","start":0,"end":9},{"label":"high","start":10,"end":19}]}` |
| `case` | See [Multi-Source Rules](#multi-source-rules) |
| `cast` | `{"operation":"cast","source":"text","target":"integer"}` |
| `coalesce` | See [Multi-Source Rules](#multi-source-rules) |
| `convert_date` | `{"operation":"convert_date","source_format":"%Y-%m-%d","target_format":"%m/%d/%Y"}` |
| `convert_units` | `{"operation":"convert_units","source_unit":"inch","target_unit":"cm"}` |
| `do_nothing` | `{"operation":"do_nothing"}` |
| `enum_to_enum` | `{"operation":"enum_to_enum","mapping":[{"from":"BL","to":"baseline"},{"from":"FU","to":"follow_up"}],"strict":false,"default":"unknown"}` |
| `extract_regex` | `{"operation":"extract_regex","expression":"MRN: ([A-Z0-9-]+)","group":1}` |
| `format_number` | `{"operation":"format_number","precision":2}` |
| `map_each` | `{"operation":"map_each","operations":[{"operation":"cast","source":"text","target":"integer"}]}` |
| `missing_code` | `{"operation":"missing_code","codes":[{"code":-999,"label":"not_measured"},{"code":"UNK","label":"unknown"}]}` |
| `normalize_boolean` | `{"operation":"normalize_boolean","truthy":["yes","y","1"],"falsy":["no","n","0"],"strict":true}` |
| `normalize_text` | `{"operation":"normalize_text","normalization":"lower"}` |
| `offset` | `{"operation":"offset","offset":2.5}` |
| `parse_array` | `{"operation":"parse_array","format":"json","item_type":"integer","strict":true}` |
| `reduce` | `{"operation":"reduce","reduction":"one-hot"}` |
| `round` | `{"operation":"round","precision":2}` |
| `scale` | `{"operation":"scale","scaling_factor":0.453592}` |
| `substitute` | `{"operation":"substitute","expression":",","substitution":" "}` |
| `threshold` | `{"operation":"threshold","lower":0,"upper":100}` |
| `truncate` | `{"operation":"truncate","length":3}` |
| `validate_pattern` | `{"operation":"validate_pattern","expression":"^\\d{4}$","mode":"fullmatch"}` |

### ParseArray + Reduce for CSV data

When arrays are serialized as text in CSV (for example `"[8,8,8,8,6]"` or
`"8|8|8|8|6"`), chain `parse_array` before `reduce`:

```json
{
  "sources": ["week_hours"],
  "target": "total_hours",
  "operations": [
    {"operation": "parse_array", "format": "json", "item_type": "integer", "strict": true},
    {"operation": "reduce", "reduction": "sum"}
  ]
}
```

For delimiter input, use:

```json
{"operation": "parse_array", "format": "delimiter", "delimiter": "|", "item_type": "integer"}
```

For newline-separated input, use:

```json
{"operation": "parse_array", "format": "delimiter", "delimiter": "\\n", "item_type": "integer"}
```

## Using the framework in an Electron App

The framework can be integrated into an Electron App

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
