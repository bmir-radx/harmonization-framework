import os
import threading
import uuid
from dataclasses import dataclass
from typing import Dict, List, Literal, Optional, Tuple

import pandas as pd
from fastapi import APIRouter
from pydantic import BaseModel

from harmonization_framework.harmonize import harmonize_dataset
from harmonization_framework.replay_log import replay_logger as rlog
from harmonization_framework.rule_registry import RuleRegistry


router = APIRouter()


class Pair(BaseModel):
    source: str
    target: str


class HarmonizeParams(BaseModel):
    data_path: str
    rules_path: str
    output_path: str
    replay_log_path: str
    mode: Literal["pairs", "all"]
    pairs: Optional[List[Pair]] = None
    overwrite: bool = False


class RpcRequest(BaseModel):
    method: str
    params: Dict


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Optional[Dict] = None


class RpcResponse(BaseModel):
    status: str
    result: Optional[Dict] = None
    error: Optional[ErrorDetail] = None
    job_id: Optional[str] = None


@dataclass
class JobInfo:
    job_id: str
    status: str
    progress: float
    output_path: str
    replay_log_path: str
    error: Optional[Dict] = None
    result: Optional[Dict] = None


_jobs: Dict[str, JobInfo] = {}
_jobs_lock = threading.Lock()


def _error(code: str, message: str, details: Optional[Dict] = None) -> RpcResponse:
    return RpcResponse(
        status="error",
        error=ErrorDetail(code=code, message=message, details=details),
    )


def _validate_paths(params: HarmonizeParams) -> Optional[RpcResponse]:
    for path_name, path_value in [
        ("data_path", params.data_path),
        ("rules_path", params.rules_path),
        ("output_path", params.output_path),
        ("replay_log_path", params.replay_log_path),
    ]:
        if not os.path.isabs(path_value):
            return _error("INVALID_PATH", f"{path_name} must be an absolute path")

    if not os.path.exists(params.data_path):
        return _error("FILE_NOT_FOUND", f"Data file not found: {params.data_path}")
    if not os.path.exists(params.rules_path):
        return _error("FILE_NOT_FOUND", f"Rules file not found: {params.rules_path}")

    if os.path.exists(params.output_path) and not params.overwrite:
        return _error("ALREADY_EXISTS", f"Output path already exists: {params.output_path}")

    return None


def _load_rules(params: HarmonizeParams) -> Tuple[Optional[RuleRegistry], Optional[RpcResponse]]:
    registry = RuleRegistry()
    try:
        registry.load(params.rules_path, clean=True)
    except Exception as exc:
        return None, _error("INVALID_FORMAT", f"Failed to load rules: {exc}")
    return registry, None


def _resolve_pairs(
    params: HarmonizeParams, registry: RuleRegistry
) -> Tuple[Optional[List[Tuple[str, str]]], Optional[RpcResponse]]:
    if params.mode == "all":
        pairs = registry.list_pairs()
        if not pairs:
            return None, _error("NOT_FOUND", "No rules found in rules file")
        return pairs, None

    if not params.pairs:
        return None, _error("MISSING_FIELD", "pairs is required when mode is 'pairs'")

    pairs = [(pair.source, pair.target) for pair in params.pairs]
    for source, target in pairs:
        try:
            registry.query(source, target)
        except Exception:
            return None, _error(
                "RULE_NOT_FOUND",
                f"Rule not found for source={source} target={target}",
            )
    return pairs, None


def _update_progress(job_id: str, processed: int, total: int) -> None:
    with _jobs_lock:
        job = _jobs.get(job_id)
        if not job:
            return
        if total == 0:
            job.progress = 1.0
        else:
            job.progress = min(1.0, processed / total)


def _run_harmonize(job_id: str, params: HarmonizeParams) -> None:
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
                "code": "HARMONIZATION_FAILED",
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
    if request.method == "harmonize":
        try:
            params = HarmonizeParams(**request.params)
        except Exception as exc:
            return _error("VALIDATION_ERROR", str(exc))

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

    if request.method == "getJob":
        job_id = request.params.get("job_id")
        if not job_id:
            return _error("MISSING_FIELD", "job_id is required")
        with _jobs_lock:
            job = _jobs.get(job_id)
        if not job:
            return _error("NOT_FOUND", f"Job not found: {job_id}")
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

    return _error("METHOD_NOT_FOUND", f"Unknown method: {request.method}")
