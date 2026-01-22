# Harmonization Framework API

The following is a demo for using `curl` to interact with the Harmonization Framework API. These examples include uploading files, defining data elements, creating harmonization rules, and applying those rules to data.

> Note: Replace UUIDs with actual values returned by your API where necessary.

## Initialize Database and File Store

```bash
python scripts/init_db.py
```

## Start API

```bash
./scripts/run_flask.sh
```

## Upload a Data Dictionary

```bash
curl -X POST http://localhost:5000/data-dictionaries/ \
  -F "file=@demo/demo_dictionary2.csv" \
  -F "project_id=test_project"
```

A successful upload returns the ID of the data dictionary.

## Retrieve a Data Dictionary by ID

```bash
curl -X GET http://localhost:5000/data-dictionaries/<dictionary_id>
```

## Extract Data Elements from a Dictionary

```bash
curl -X POST http://localhost:5000/data-dictionaries/<dictionary_id>/extract-data-elements
```

## Manually Add a Data Element

```bash
curl -X POST http://localhost:5000/data-elements/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "height",
    "description": "Height of the subject in centimeters",
    "datatype": "float",
    "permissible_values": "50-250",
    "project_id": "test_project"
  }'
```

Successful creation of the data element returns its ID.

## List All Data Elements

```bash
curl -X GET http://localhost:5000/data-elements/
```

## Upload a Data File

```bash
curl -X POST http://localhost:5000/data-files/ \
  -F "file=@demo/demo_source2.csv" \
  -F "project_id=test_project" \
  -F "dictionary_id=<dictionary_id>" \
  -F "project_id=test_project"
```

## List All Data Files

```bash
curl -X GET http://localhost:5000/data-files/
```

## Create Harmonization Rules

```bash
curl -X POST http://localhost:5000/harmonization-rules/ \
  -H "Content-Type: application/json" \
  -d '{
    "source_target": "commute_distance_km-commute_distance_miles",
    "project_id": "test_project",
    "version": 1,
    "rule_json":  {
      "source": "commute_distance_km",
      "target": "commute_distance_miles",
      "operations": [
        {
          "operation": "convert_units",
          "source_unit": "kilometers",
          "target_unit": "miles"
        },
        {
          "operation": "round",
          "precision": 2
        }
      ]
    }
  }'
```

```bash
curl -X POST http://localhost:5000/harmonization-rules/ \
  -H "Content-Type: application/json" \
  -d '{
    "source_target": "employment-nih_employment",
    "project_id": "test_project",
    "version": 1,
    "rule_json":  {
      "source": "employment",
      "target": "nih_employment",
      "operations": [
        {
          "operation": "enum_to_enum",
          "mapping": {
            "1": 0,
            "2": 0,
            "3": 1
          }
        }
      ]
    }
  }'
```

## Apply Harmonization Rules to a Data File

```bash
curl -X POST http://localhost:5000/data-files/e27d1e93-bd61-4679-8903-adcee904c999/harmonize \
  -H "Content-Type: application/json" \
  -d '{
    "rule_ids": [
      "45c717bf-1103-431f-a687-5c3de631a774",
      "e7bb3be8-eaaf-444e-bbe0-f58468963a3e"
    ]
  }'
```
