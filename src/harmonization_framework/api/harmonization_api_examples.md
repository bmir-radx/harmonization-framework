# Harmonization Framework API

The following is a demo for using `curl` to interact with the Harmonization Framework API.

> Note: Replace UUIDs with actual values returned by your API where necessary.

## Start API

```bash
./scripts/run_api.sh
```

## Example Usage

### Harmonize (RPC)

```bash
curl -X POST http://localhost:8000/api \
  -H "Content-Type: application/json" \
  -d '{
    "method": "harmonize",
    "params": {
      "data_path": "/absolute/path/to/input.csv",
      "rules_path": "/absolute/path/to/rules.json",
      "output_path": "/absolute/path/to/output.csv",
      "replay_log_path": "/absolute/path/to/replay.log",
      "mode": "pairs",
      "pairs": [
        {"source": "col_a", "target": "col_b"}
      ],
      "overwrite": false
    }
  }'
```

### Get Job Status (RPC)

```bash
curl -X POST http://localhost:8000/api \
  -H "Content-Type: application/json" \
  -d '{
    "method": "get_job",
    "params": {
      "job_id": "job-uuid"
    }
  }'
```

## Error Responses

Errors follow a stable schema:

```json
{
  "status": "error",
  "error": {
    "code": "FILE_NOT_FOUND",
    "message": "Rules file not found: /abs/path/to/rules.json",
    "details": {
      "path_type": "rules_path",
      "path": "/abs/path/to/rules.json"
    }
  }
}
```

The `code` is a small, stable set of values. Use `details` to determine
which field/path caused the error.
