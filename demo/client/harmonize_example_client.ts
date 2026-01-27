/*
  Minimal RPC client example (Node + fetch).

  This script shows how to call the Harmonization Framework RPC API from a
  simple Node/TypeScript client and poll for completion.

  Assumptions:
  - The harmonization server is already running on http://localhost:8000
  - You run this script from the repo root so relative paths resolve

  Run (Node 18+):
    node demo/client/harmonize_example_client.ts
  or with ts-node:
    npx ts-node demo/client/harmonize_example_client.ts
*/

import * as path from "node:path";
import { fileURLToPath } from "node:url";
import { GetJobResponse, HarmonizeRequest, HarmonizeResponse, JOB_STATUS } from "./rpc_types.ts";
import { RpcClient } from "./rpc_client.js";

// The single RPC endpoint exposed by the server.
const API_URL = "http://localhost:8000/api";
const HARMONIZE_TIMEOUT_MS = 20_000;
const GET_JOB_TIMEOUT_MS = 5_000;

// Simple delay helper used for polling.
function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

// Build an absolute path from this script's directory.
// This lets the script run from demo/client without relying on process.cwd().
const clientDir = path.dirname(fileURLToPath(import.meta.url));
function buildAbsPath(...parts: string[]): string {
  return path.resolve(clientDir, ...parts);
}

// Generic RPC caller. All methods are POSTs to /api with { method, params }.
async function main() {
  const client = new RpcClient(API_URL);
  // Use the demo inputs/rules from demo/harmonize_example.
  // This script lives in demo/client, so go up one level to demo/.
  const dataFilePath = buildAbsPath("..", "harmonize_example", "input.csv");
  const rulesFilePath = buildAbsPath("..", "harmonize_example", "rules.json");
  const replayLogFilePath = buildAbsPath("..", "harmonize_example", "replay.log");
  const outputFilePath = buildAbsPath("..", "harmonize_example", "output.csv");

  // Start harmonization. The server returns a job_id you can poll.
  const harmonizeParams: HarmonizeRequest = {
    data_file_path: dataFilePath,
    rules_file_path: rulesFilePath,
    replay_log_file_path: replayLogFilePath,
    output_file_path: outputFilePath,
    mode: "pairs",
    pairs: [
      { source: "age", target: "age_years" },
      { source: "weight_lbs", target: "weight_kg" },
      { source: "name", target: "given_name" },
      { source: "name", target: "family_name" },
      { source: "visit_type_code", target: "visit_type_label" },
    ],
    overwrite: true,
  };

  const startResponse = await client.call<HarmonizeResponse>({
    method: "harmonize",
    params: harmonizeParams,
    timeoutMs: HARMONIZE_TIMEOUT_MS,
  });

  const jobId = startResponse.job_id;
  console.log(`Harmonization started. job_id=${jobId}`);

  // Poll until completion.
  while (true) {
    const statusResponse = await client.call<GetJobResponse>({
      method: "get_job",
      params: { job_id: jobId },
      timeoutMs: GET_JOB_TIMEOUT_MS,
    });

    const job = statusResponse.result;
    const percent = Math.round(job.progress * 100);
    console.log(`Progress: ${percent}%`);

    if (job.status === JOB_STATUS.COMPLETED) {
      console.log("Harmonization completed.");
      console.log(`Output: ${job.output_path}`);
      console.log(`Replay log: ${job.replay_log_path}`);
      break;
    }

    if (job.status === JOB_STATUS.FAILED) {
      console.error("Harmonization failed.");
      console.error(job.error ?? "Unknown error");
      break;
    }

    await sleep(500);
  }
}

main().catch((err) => {
  if (err && typeof err === "object" && "message" in err) {
    console.error((err as Error).message);
    const details = (err as Error & { details?: unknown }).details;
    if (details) {
      console.error("Details:", details);
    }
  } else {
    console.error(err);
  }
  process.exit(1);
});
