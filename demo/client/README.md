# RPC Client Demo (TypeScript + fetch)

This folder contains a minimal client that calls the Harmonization Framework RPC API
and polls for completion. It uses **plain Node + fetch** (no extra dependencies required
if you are on Node 18+).

> Note: This is a demo client intended for learning and quick validation, not a production-ready SDK.

## Prerequisites
- The harmonization API server is running:

```bash
./scripts/run_api.sh
```

- Node 18+ (for built-in `fetch`)
- TypeScript users may need Node type definitions:
  `npm i --save-dev @types/node`

If you want a quick setup in this folder, run:

```bash
cd demo/client
npm install
```

## Run the demo
From the `demo/client` directory:

```bash
node harmonize_example_client.ts
```

If you prefer to run with ts-node:

```bash
npx ts-node harmonize_example_client.ts
```

## What it does
- Sends a `harmonize` RPC request using the same input and rules as
  `demo/harmonize_example/`.
- Polls `get_job` until the job completes or fails.
- Prints progress and output paths.
- RPC response shapes are documented in `rpc_types.ts`.
- Error responses include an error code, message, and optional details.

## Reusable client
`rpc_client.ts` contains a small `RpcClient` class that can be reused by other
scripts or integrations. It wraps the `/api` RPC calls, handles timeouts, and
raises rich errors when the server returns an error payload.

## Outputs
The demo writes the harmonized CSV and replay log to:

- `demo/harmonize_example/output.csv`
- `demo/harmonize_example/replay.log`

## Notes
- The client uses absolute paths resolved from the script location (`demo/client`).
- If the output files already exist, the demo sets `overwrite: true`.
