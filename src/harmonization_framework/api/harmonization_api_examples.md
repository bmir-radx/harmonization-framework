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
    "method": "getJob",
    "params": {
      "job_id": "job-uuid"
    }
  }'
```
