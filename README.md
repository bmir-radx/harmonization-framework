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
