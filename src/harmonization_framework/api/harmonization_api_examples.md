# Harmonization Framework API

The following is a demo for using `curl` to interact with the Harmonization Framework API. These examples include uploading files and applying harmonization rules to data.

> Note: Replace UUIDs with actual values returned by your API where necessary.

## Initialize Database and File Store

```bash
python scripts/init_db.py
```

## Start API

```bash
./scripts/run_flask.sh
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
