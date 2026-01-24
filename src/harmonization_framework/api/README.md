# Harmonization Framework RPC API

This document describes the RPC-style API used by the Electron app. It explains
the request/response schema, method semantics, and expected call order.

## Base URL

```
http://localhost:8000
```

## Endpoints

### `GET /health/`

Health check endpoint.

**Response**
```json
{
  "status": "ok",
  "message": "API is available"
}
```

---

### `POST /api`

Single RPC endpoint. Each request specifies a `method` and a `params` object.

**Request envelope**
```json
{
  "method": "method_name",
  "params": { }
}
```

**Response envelope (success)**
```json
{
  "status": "success",
  "result": { }
}
```

**Response envelope (accepted / async)**
```json
{
  "status": "accepted",
  "job_id": "job-uuid"
}
```

**Response envelope (error)**
```json
{
  "status": "error",
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable error message",
    "details": { }
  }
}
```

Method names use **snake_case**. The server also accepts camelCase aliases
(e.g., `getJob`) because this is often more convenient for JavaScript clients.

## Error Codes

Error codes are intentionally small and stable. Use `error.details` to identify
the specific field/path/context.

| Code | Meaning | Common details |
|------|---------|----------------|
| `INVALID_PATH` | A required path is not absolute or malformed | `{ "path_type": "...", "path": "..." }` |
| `FILE_NOT_FOUND` | Data or rules file does not exist | `{ "path_type": "...", "path": "..." }` |
| `ALREADY_EXISTS` | Output path exists and overwrite is false | `{ "path_type": "output_file_path", "path": "..." }` |
| `MISSING_FIELD` | Required request field missing | `{ "field": "..." }` |
| `VALIDATION_ERROR` | Request params failed validation | `{ "params": { ... } }` |
| `RULE_NOT_FOUND` | Requested rule pair not found or rules file empty | `{ "source": "...", "target": "..." }` or `{ "path": "..." }` |
| `JOB_NOT_FOUND` | Job ID not found | `{ "job_id": "..." }` |
| `INVALID_FORMAT` | Rules file is invalid JSON/format | `{}` |
| `HARMONIZATION_FAILED` | Harmonization failed during execution | `{}` |
| `METHOD_NOT_FOUND` | Unknown RPC method | `{}` |

## Methods

### 1) `harmonize`

Asynchronously harmonize a CSV dataset using rules from a RuleRegistry JSON file.

**Request**
```json
{
  "method": "harmonize",
  "params": {
    "data_file_path": "/abs/input.csv",
    "rules_file_path": "/abs/rules.json",
    "replay_log_file_path": "/abs/replay.log",
    "output_file_path": "/abs/output.csv",
    "mode": "pairs",
    "pairs": [
      { "source": "col_a", "target": "col_b" }
    ],
    "overwrite": false
  }
}
```

**Parameters**
- `data_file_path` (string, required): Absolute path to input CSV.
- `rules_file_path` (string, required): Absolute path to RuleRegistry JSON file
  produced by `RuleRegistry.save()`.
- `replay_log_file_path` (string, required): Absolute path for replay log output.
- `output_file_path` (string, required): Absolute path for harmonized CSV output.
- `mode` (string, required): `"pairs"` or `"all"`.
  - `"pairs"`: apply only specified pairs.
  - `"all"`: apply every rule in the registry file.
- `pairs` (array, required when `mode="pairs"`): List of `{source, target}` mappings.
- `overwrite` (boolean, optional, default `false`): Whether to overwrite existing output.

**Response**
```json
{
  "status": "accepted",
  "job_id": "job-uuid"
}
```

**Possible errors**

- `INVALID_PATH` — one or more provided paths are not absolute.
  - `details.path_type`: `data_file_path` | `rules_file_path` | `output_file_path` | `replay_log_file_path`
  - `details.path`: the invalid path value
- `FILE_NOT_FOUND` — input file or rules file does not exist.
  - `details.path_type`: `data_file_path` or `rules_file_path`
  - `details.path`: missing file path
- `ALREADY_EXISTS` — output file exists and `overwrite=false`.
  - `details.path_type`: `output_file_path`
  - `details.path`: existing output path
- `MISSING_FIELD` — required field missing (e.g., `pairs` when `mode="pairs"`).
  - `details.field`: missing field name
- `RULE_NOT_FOUND` — requested pairs not found or no rules in file.
  - `details.source` / `details.target` for missing pairs, or `details.path` for empty rules file
- `INVALID_FORMAT` — rules file could not be parsed.
  - `details` may be empty
- `VALIDATION_ERROR` — request params failed validation.
  - `details.params`: original params object

**Behavior**
- Paths must be absolute.
- `data_file_path` and `rules_file_path` must exist.
- `output_file_path` must not exist unless `overwrite=true`.
- `replay_log_file_path` will be created if needed.
- Work runs asynchronously; track with `get_job`.

---

### 2) `get_job`

Retrieve status and progress for an async job.

**Request**
```json
{
  "method": "get_job",
  "params": { "job_id": "job-uuid" }
}
```

**Response**
```json
{
  "status": "success",
  "result": {
    "job_id": "job-uuid",
    "status": "queued|running|completed|failed",
    "progress": 0.42,
    "output_path": "/abs/output.csv",
    "replay_log_path": "/abs/replay.log",
    "result": {
      "output_path": "/abs/output.csv",
      "replay_log_path": "/abs/replay.log"
    },
    "error": {
      "code": "HARMONIZATION_FAILED",
      "message": "...",
      "details": {}
    }
  }
}
```

**Possible errors**

- `MISSING_FIELD` — `job_id` is missing.
  - `details.field`: `"job_id"`
- `JOB_NOT_FOUND` — job id not found.
  - `details.job_id`: requested job id

**Progress**
- Progress is **row-based** and reported as a float in `[0.0, 1.0]`.
- Computed as `(processed cells) / (rows * number_of_pairs)`.

## Call Order

1. Submit a `harmonize` request.
2. Poll `get_job` using the returned `job_id`.
3. When `status == "completed"`, read `output_path` and `replay_log_path`.

## Example Call Flow

The typical client flow is:

1. Submit a `harmonize` request with absolute paths and the desired rule mode.
2. Receive a `job_id` immediately (the work runs asynchronously).
3. Poll `get_job` until the status is `completed` or `failed`.
4. On completion, read the output CSV and replay log from the returned paths.

```bash
curl -X POST http://localhost:8000/api \\
  -H "Content-Type: application/json" \\
  -d '{
    "method": "harmonize",
    "params": {
      "data_file_path": "/abs/input.csv",
      "rules_file_path": "/abs/rules.json",
      "replay_log_file_path": "/abs/replay.log",
      "output_file_path": "/abs/output.csv",
      "mode": "all",
      "overwrite": true
    }
  }'
```

The server responds with a `job_id` you can use to query progress:

```json
{
  "status": "accepted",
  "job_id": "0c4f5c44-9c2a-4d11-9a8d-1b3e71df4b4a"
}
```

```bash
curl -X POST http://localhost:8000/api \\
  -H "Content-Type: application/json" \\
  -d '{
    "method": "get_job",
    "params": { "job_id": "job-uuid" }
  }'
```

Example response while the job is still running:

```json
{
  "status": "success",
  "result": {
    "job_id": "0c4f5c44-9c2a-4d11-9a8d-1b3e71df4b4a",
    "status": "running",
    "progress": 0.37,
    "output_path": "/abs/output.csv",
    "replay_log_path": "/abs/replay.log",
    "result": null,
    "error": null
  }
}
```

When `status` becomes `completed`, the `result` object includes the final
`output_path` and `replay_log_path`. If `status` is `failed`, inspect the
`error` object for a stable error code and contextual details.

```json
{
  "status": "success",
  "result": {
    "job_id": "0c4f5c44-9c2a-4d11-9a8d-1b3e71df4b4a",
    "status": "completed",
    "progress": 1.0,
    "output_path": "/abs/output.csv",
    "replay_log_path": "/abs/replay.log",
    "result": {
      "output_path": "/abs/output.csv",
      "replay_log_path": "/abs/replay.log"
    },
    "error": null
  }
}
```
