import os
import threading
import uuid
from typing import Dict, List, Optional, Tuple

import pandas as pd

from harmonization_framework.harmonize import harmonize_dataset
from harmonization_framework.replay_log import replay_logger as rlog
from harmonization_framework.rule_registry import RuleRegistry
from harmonization_framework.api.rpc_errors import ErrorCode, build_error
from harmonization_framework.api.rpc_jobs import (
    JobId,
    JobInfo,
    get_job,
    register_job,
    update_job_status,
    update_progress,
)
from harmonization_framework.api.rpc_models import HarmonizeParams, RpcRequest, RpcResponse


def _validate_paths(params: HarmonizeParams) -> Optional[RpcResponse]:
    """
    Validate input/output/replay paths and overwrite behavior.

    Rules:
    - All paths must be absolute.
    - data_file_path and rules_file_path must exist.
    - output_file_path must not exist unless overwrite=True.
    - replay_log_file_path may be a new file and will be created if needed.
    """
    for path_name, path_value in [
        ("data_file_path", params.data_file_path),
        ("rules_file_path", params.rules_file_path),
        ("output_file_path", params.output_file_path),
        ("replay_log_file_path", params.replay_log_file_path),
    ]:
        if not os.path.isabs(path_value):
            return build_error(
                ErrorCode.INVALID_PATH,
                f"{path_name} must be an absolute path",
                details={"path": path_value, "path_type": path_name},
            )

    if not os.path.exists(params.data_file_path):
        return build_error(
            ErrorCode.FILE_NOT_FOUND,
            f"Data file not found: {params.data_file_path}",
            details={"path": params.data_file_path, "path_type": "data_path"},
        )
    if not os.path.exists(params.rules_file_path):
        return build_error(
            ErrorCode.FILE_NOT_FOUND,
            f"Rules file not found: {params.rules_file_path}",
            details={"path": params.rules_file_path, "path_type": "rules_path"},
        )

    if os.path.exists(params.output_file_path) and not params.overwrite:
        return build_error(
            ErrorCode.ALREADY_EXISTS,
            f"Output path already exists: {params.output_file_path}",
            details={"path": params.output_file_path, "path_type": "output_path"},
        )

    return None


def _load_rules(params: HarmonizeParams) -> Tuple[Optional[RuleRegistry], Optional[RpcResponse]]:
    """Load a RuleRegistry from a rules JSON file."""
    registry = RuleRegistry()
    try:
        registry.load(params.rules_file_path, clean=True)
    except Exception as exc:
        return None, build_error(ErrorCode.INVALID_FORMAT, f"Failed to load rules: {exc}")
    return registry, None


def _resolve_harmonization_pairs(
    params: HarmonizeParams, registry: RuleRegistry
) -> Tuple[Optional[List[Tuple[str, str]]], Optional[RpcResponse]]:
    """
    Resolve requested (source, target) pairs based on mode and availability.

    - mode="all": return all pairs from the rules registry (error if empty).
    - mode="pairs": validate that requested pairs exist in the registry.

    Returns (pairs, error). On error, pairs is None and error is a RpcResponse.
    """
    if params.mode == "all":
        pairs = registry.list_pairs()
        if not pairs:
            return None, build_error(
                ErrorCode.RULE_NOT_FOUND,
                "No rules found in rules file",
                details={"path": params.rules_file_path},
            )
        return pairs, None

    if not params.harmonization_pairs:
        return None, build_error(
            ErrorCode.MISSING_FIELD,
            "pairs is required when mode is 'pairs'",
            details={"field": "pairs"},
        )

    pairs = [(pair.source, pair.target) for pair in params.harmonization_pairs]
    for source, target in pairs:
        try:
            registry.query(source, target)
        except Exception:
            return None, build_error(
                ErrorCode.RULE_NOT_FOUND,
                f"Rule not found for source={source} target={target}",
                details={"source": source, "target": target},
            )
    return pairs, None


def _run_harmonize(job_id: JobId, params: HarmonizeParams) -> None:
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
    update_job_status(job_id, status="running", progress=0.0)

    validation_error = _validate_paths(params)
    if validation_error:
        update_job_status(job_id, status="failed", error=validation_error.error.model_dump())
        return

    registry, error = _load_rules(params)
    if error:
        update_job_status(job_id, status="failed", error=error.error.model_dump())
        return

    pairs, error = _resolve_harmonization_pairs(params, registry)
    if error:
        update_job_status(job_id, status="failed", error=error.error.model_dump())
        return

    os.makedirs(os.path.dirname(params.output_file_path), exist_ok=True)
    os.makedirs(os.path.dirname(params.replay_log_file_path), exist_ok=True)

    dataset = pd.read_csv(params.data_file_path)
    logger = rlog.configure_logger(3, params.replay_log_file_path)

    def progress_callback(processed: int, total: int) -> None:
        update_progress(job_id, processed, total)

    try:
        harmonized = harmonize_dataset(
            dataset=dataset,
            harmonization_pairs=pairs,
            rules=registry,
            dataset_name=os.path.basename(params.data_file_path),
            logger=logger,
            progress_callback=progress_callback,
        )
        harmonized.to_csv(params.output_file_path, index=False)
    except Exception as exc:
        update_job_status(
            job_id,
            status="failed",
            error={
                "code": ErrorCode.HARMONIZATION_FAILED.value,
                "message": str(exc),
            },
        )
        return

    update_job_status(
        job_id,
        status="completed",
        progress=1.0,
        result={
            "output_path": params.output_file_path,
            "replay_log_path": params.replay_log_file_path,
        },
    )


def handle_harmonize(request: RpcRequest) -> RpcResponse:
    """Handle the harmonize RPC method."""
    try:
        params = HarmonizeParams(**request.params)
    except Exception as exc:
        return build_error(ErrorCode.VALIDATION_ERROR, str(exc), details={"params": request.params})

    job_id = JobId(str(uuid.uuid4()))
    job = JobInfo(
        job_id=job_id,
        status="queued",
        progress=0.0,
        output_path=params.output_file_path,
        replay_log_path=params.replay_log_file_path,
    )
    register_job(job)

    thread = threading.Thread(target=_run_harmonize, args=(job_id, params), daemon=True)
    thread.start()
    return RpcResponse(status="accepted", job_id=job_id)


def handle_get_job(request: RpcRequest) -> RpcResponse:
    """Handle the get_job RPC method."""
    job_id_value = request.params.get("job_id")
    if not job_id_value:
        return build_error(
            ErrorCode.MISSING_FIELD,
            "job_id is required",
            details={"field": "job_id"},
        )
    job_id = JobId(job_id_value)
    job = get_job(job_id)
    if not job:
        return build_error(
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
