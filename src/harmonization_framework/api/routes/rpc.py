import os
import threading
import uuid
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Literal, Optional, Tuple

import pandas as pd
from fastapi import APIRouter
from pydantic import BaseModel

from harmonization_framework.harmonize import harmonize_dataset
from harmonization_framework.replay_log import replay_logger as rlog
from harmonization_framework.rule_registry import RuleRegistry


router = APIRouter()


"""
RPC API router.

Implements a single POST /api endpoint with method dispatch. Currently supported:
- harmonize: async CSV harmonization with row-based progress tracking
- get_job: retrieve status/progress/result for a job

Method names use snake_case. The router also accepts camelCase aliases
(e.g., getJob) for convenience.

Error handling:
- Error codes are intentionally small and stable (e.g., MISSING_FIELD, INVALID_PATH,
  FILE_NOT_FOUND, INVALID_FORMAT, VALIDATION_ERROR, RULE_NOT_FOUND, JOB_NOT_FOUND).
- Callers should use the `details` object to identify which field/path caused the error.
  Example: {"field": "rules_path"} or {"path_type": "rules_path", "path": "/abs/..."}.
"""


class Pair(BaseModel):
    """Source/target column pair."""
    source: str
    target: str


class HarmonizeParams(BaseModel):
    """Parameters for the harmonize RPC call."""
    data_path: str
    rules_path: str
    output_path: str
    replay_log_path: str
    mode: Literal["pairs", "all"]
    pairs: Optional[List[Pair]] = None
    overwrite: bool = False


class RpcRequest(BaseModel):
    """RPC request envelope."""
    method: str
    params: Dict


class ErrorDetail(BaseModel):
    """Structured error payload for RPC responses."""
    code: str
    message: str
    details: Optional[Dict] = None


class RpcResponse(BaseModel):
    """RPC response envelope."""
    status: str
    result: Optional[Dict] = None
    error: Optional[ErrorDetail] = None
    job_id: Optional[str] = None


class ErrorCode(str, Enum):
    INVALID_PATH = "INVALID_PATH"
    FILE_NOT_FOUND = "FILE_NOT_FOUND"
    ALREADY_EXISTS = "ALREADY_EXISTS"
    MISSING_FIELD = "MISSING_FIELD"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    RULE_NOT_FOUND = "RULE_NOT_FOUND"
    JOB_NOT_FOUND = "JOB_NOT_FOUND"
    INVALID_FORMAT = "INVALID_FORMAT"
    HARMONIZATION_FAILED = "HARMONIZATION_FAILED"
    METHOD_NOT_FOUND = "METHOD_NOT_FOUND"


@dataclass
class JobInfo:
    """In-memory job state for async operations."""
    job_id: str
    status: str
    progress: float
    output_path: str
    replay_log_path: str
    error: Optional[Dict] = None
    result: Optional[Dict] = None


_jobs: Dict[str, JobInfo] = {}
_jobs_lock = threading.Lock()


def _error(code: ErrorCode, message: str, details: Optional[Dict] = None) -> RpcResponse:
    """Helper to build a standardized error response."""
    return RpcResponse(
        status="error",
        error=ErrorDetail(code=code.value, message=message, details=details),
    )


def _normalize_method(method: str) -> str:
    """
    Normalize method names to snake_case and support legacy/camelCase aliases.
    """
    aliases = {
        "getJob": "get_job",
        "harmonize": "harmonize",
        "get_job": "get_job",
    }
    return aliases.get(method, method)


def _validate_paths(params: HarmonizeParams) -> Optional[RpcResponse]:
    """
    Validate input/output/replay paths and overwrite behavior.

    Rules:
    - All paths must be absolute.
    - data_path and rules_path must exist.
    - output_path must not exist unless overwrite=True.
    - replay_log_path may be a new file and will be created if needed.
    """
    for path_name, path_value in [
        ("data_path", params.data_path),
        ("rules_path", params.rules_path),
        ("output_path", params.output_path),
        ("replay_log_path", params.replay_log_path),
    ]:
        if not os.path.isabs(path_value):
            return _error(
                ErrorCode.INVALID_PATH,
                f"{path_name} must be an absolute path",
                details={"path": path_value, "path_type": path_name},
            )

    if not os.path.exists(params.data_path):
        return _error(
            ErrorCode.FILE_NOT_FOUND,
            f"Data file not found: {params.data_path}",
            details={"path": params.data_path, "path_type": "data_path"},
        )
    if not os.path.exists(params.rules_path):
        return _error(
            ErrorCode.FILE_NOT_FOUND,
            f"Rules file not found: {params.rules_path}",
            details={"path": params.rules_path, "path_type": "rules_path"},
        )

    if os.path.exists(params.output_path) and not params.overwrite:
        return _error(
            ErrorCode.ALREADY_EXISTS,
            f"Output path already exists: {params.output_path}",
            details={"path": params.output_path, "path_type": "output_path"},
        )

    return None


def _load_rules(params: HarmonizeParams) -> Tuple[Optional[RuleRegistry], Optional[RpcResponse]]:
    """Load a RuleRegistry from a rules JSON file."""
    registry = RuleRegistry()
    try:
        registry.load(params.rules_path, clean=True)
    except Exception as exc:
        return None, _error(ErrorCode.INVALID_FORMAT, f"Failed to load rules: {exc}")
    return registry, None


def _resolve_pairs(
    params: HarmonizeParams, registry: RuleRegistry
) -> Tuple[Optional[List[Tuple[str, str]]], Optional[RpcResponse]]:
    """Resolve requested (source, target) pairs based on mode and availability."""
    if params.mode == "all":
        pairs = registry.list_pairs()
        if not pairs:
            return None, _error(
                ErrorCode.RULE_NOT_FOUND,
                "No rules found in rules file",
                details={"path": params.rules_path},
            )
        return pairs, None

    if not params.pairs:
        return None, _error(
            ErrorCode.MISSING_FIELD,
            "pairs is required when mode is 'pairs'",
            details={"field": "pairs"},
        )

    pairs = [(pair.source, pair.target) for pair in params.pairs]
    for source, target in pairs:
        try:
            registry.query(source, target)
        except Exception:
            return None, _error(
                ErrorCode.RULE_NOT_FOUND,
                f"Rule not found for source={source} target={target}",
                details={"source": source, "target": target},
            )
    return pairs, None


def _update_progress(job_id: str, processed: int, total: int) -> None:
    """Update job progress in the in-memory registry."""
    with _jobs_lock:
        job = _jobs.get(job_id)
        if not job:
            return
        if total == 0:
            job.progress = 1.0
        else:
            job.progress = min(1.0, processed / total)


def _run_harmonize(job_id: str, params: HarmonizeParams) -> None:
    """
    Worker that performs harmonization and updates job state.

    Workflow:
    1) Validate paths and overwrite behavior.
    2) Load rules from the registry JSON file.
    3) Resolve rule pairs based on the requested mode.
    4) Create output/log directories as needed.
    5) Read input CSV, apply harmonization with row-based progress callbacks.
    6) Write output CSV and finalize job state.

    On failure, sets job status to "failed" and records a structured error.
    """
    with _jobs_lock:
        job = _jobs[job_id]
        job.status = "running"
        job.progress = 0.0

    validation_error = _validate_paths(params)
    if validation_error:
        with _jobs_lock:
            job.status = "failed"
            job.error = validation_error.error.model_dump()
        return

    registry, error = _load_rules(params)
    if error:
        with _jobs_lock:
            job.status = "failed"
            job.error = error.error.model_dump()
        return

    pairs, error = _resolve_pairs(params, registry)
    if error:
        with _jobs_lock:
            job.status = "failed"
            job.error = error.error.model_dump()
        return

    os.makedirs(os.path.dirname(params.output_path), exist_ok=True)
    os.makedirs(os.path.dirname(params.replay_log_path), exist_ok=True)

    dataset = pd.read_csv(params.data_path)
    logger = rlog.configure_logger(3, params.replay_log_path)

    def progress_callback(processed: int, total: int) -> None:
        _update_progress(job_id, processed, total)

    try:
        harmonized = harmonize_dataset(
            dataset=dataset,
            harmonization_pairs=pairs,
            rules=registry,
            dataset_name=os.path.basename(params.data_path),
            logger=logger,
            progress_callback=progress_callback,
        )
        harmonized.to_csv(params.output_path, index=False)
    except Exception as exc:
        with _jobs_lock:
            job.status = "failed"
            job.error = {
                "code": ErrorCode.HARMONIZATION_FAILED.value,
                "message": str(exc),
            }
        return

    with _jobs_lock:
        job.status = "completed"
        job.progress = 1.0
        job.result = {
            "output_path": params.output_path,
            "replay_log_path": params.replay_log_path,
        }


@router.post("")
def rpc_call(request: RpcRequest) -> RpcResponse:
    """
    Dispatch RPC methods and return a standardized response envelope.

    Supported methods (snake_case; camelCase aliases accepted):
    - harmonize:
        params:
          data_path: absolute path to input CSV
          rules_path: absolute path to RuleRegistry JSON
          output_path: absolute path to write harmonized CSV
          replay_log_path: absolute path to write replay log
          mode: "pairs" | "all"
          pairs: optional list of {source, target} when mode="pairs"
          overwrite: boolean (default false)

        response:
          status: "accepted"
          job_id: string

    - get_job:
        params:
          job_id: string

        response:
          status: "success"
          result: {
            job_id, status, progress, output_path, replay_log_path, result, error
          }
    """
    method = _normalize_method(request.method)

    if method == "harmonize":
        try:
            params = HarmonizeParams(**request.params)
        except Exception as exc:
            return _error(ErrorCode.VALIDATION_ERROR, str(exc), details={"params": request.params})

        job_id = str(uuid.uuid4())
        job = JobInfo(
            job_id=job_id,
            status="queued",
            progress=0.0,
            output_path=params.output_path,
            replay_log_path=params.replay_log_path,
        )
        with _jobs_lock:
            _jobs[job_id] = job

        thread = threading.Thread(target=_run_harmonize, args=(job_id, params), daemon=True)
        thread.start()
        return RpcResponse(status="accepted", job_id=job_id)

    if method == "get_job":
        job_id = request.params.get("job_id")
        if not job_id:
            return _error(
                ErrorCode.MISSING_FIELD,
                "job_id is required",
                details={"field": "job_id"},
            )
        with _jobs_lock:
            job = _jobs.get(job_id)
        if not job:
            return _error(
                ErrorCode.JOB_NOT_FOUND,
                f"Job not found: {job_id}",
                details={"job_id": job_id},
            )
        return RpcResponse(
            status="success",
            result={
                "job_id": job.job_id,
                "status": job.status,
                "progress": job.progress,
                "output_path": job.output_path,
                "replay_log_path": job.replay_log_path,
                "result": job.result,
                "error": job.error,
            },
        )

    return _error(ErrorCode.METHOD_NOT_FOUND, f"Unknown method: {request.method}")
