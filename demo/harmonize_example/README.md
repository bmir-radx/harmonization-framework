# Harmonization Example

This folder contains a **minimal, self‑contained** example of how to use the harmonization framework.
It includes a small input CSV, a rules JSON file, and a Python script that performs the harmonization.

## Files
- `input.csv` — The raw input data.
- `rules.json` — Harmonization rules saved in the framework’s JSON format.
- `run_example.py` — Loads the rules, applies them, and writes `output.csv`.
- `output.csv` — Generated when you run the script.

## What the example does
- Renames `age` to `age_years` (pass-through).
- Converts `weight_lbs` to `weight_kg` (multiply by 0.453592).
- Splits `name` (stored as `"Last, First"`) into two new columns:
  - `given_name`
  - `family_name`
- Maps `visit_type_code` (numeric codes) to `visit_type_label` using an enum-to-enum rule.

## Run it
From the repository root:

```bash
python demo/harmonize_example/run_example.py
```

This writes `demo/harmonize_example/output.csv`.

## Expected output columns
The output CSV includes:
- `age_years`
- `weight_kg`
- `given_name`
- `family_name`
- `visit_type_label`
- `source dataset` (set to `"demo"` for each row)
- `original_id` (the original row index)

## Notes
- The rules in `rules.json` are loaded into a `RuleRegistry` via `rules.load(...)`.
- The `(source, target)` pairs in `run_example.py` must match the keys in `rules.json`.
