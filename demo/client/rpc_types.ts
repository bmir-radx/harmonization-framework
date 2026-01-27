// Status values returned by the get_job endpoint for an in-flight or finished job.
export const JOB_STATUS = {
  QUEUED: "queued",
  RUNNING: "running",
  COMPLETED: "completed",
  FAILED: "failed",
} as const;

export type JobStatus = (typeof JOB_STATUS)[keyof typeof JOB_STATUS];



// Params accepted by the harmonize RPC method.
export interface HarmonizeRequest {
  // Absolute path to the input CSV file.
  data_file_path: string;
  // Absolute path to the rules JSON file (RuleRegistry.save()).
  rules_file_path: string;
  // Absolute path where the replay log should be written.
  replay_log_file_path: string;
  // Absolute path where the output CSV should be written.
  output_file_path: string;
  // "pairs" applies only the specified pairs; "all" uses all rules in the registry.
  mode: "pairs" | "all";
  // Explicit list of (source, target) pairs to harmonize.
  pairs?: Array<{ source: string; target: string }>;
  // Overwrite output and replay log files if they already exist.
  overwrite?: boolean;
}

// Response returned by the harmonize RPC method.
export interface HarmonizeResponse {
  // Always "accepted" for a successful request.
  status: string;
  // Opaque job identifier used to poll progress and results.
  job_id: string;
}

// Details for a harmonization job returned by get_job.
export interface JobInfo {
  // The same job_id returned by the harmonize call.
  job_id: string;
  // Job lifecycle status.
  status: JobStatus;
  // Progress as a fraction from 0.0 to 1.0.
  progress: number;
  // Path to the output CSV on success.
  output_path?: string;
  // Path to the replay log on success.
  replay_log_path?: string;
  // Optional result payload (if provided by the server).
  result?: unknown;
  // Error payload (if the job failed).
  error?: unknown;
}

// Response returned by the get_job RPC method.
export interface GetJobResponse {
  // Always "success" for a successful request.
  status: string;
  // Job details payload.
  result: JobInfo;
}

// Standard error payload returned by the RPC API.
export interface RpcError {
  // Error code string (e.g., FILE_NOT_FOUND, JOB_NOT_FOUND).
  code: string;
  // Human-readable error message.
  message: string;
  // Optional error details (field/path/job_id/etc).
  details?: Record<string, unknown> | null;
}
