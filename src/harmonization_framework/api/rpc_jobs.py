from dataclasses import dataclass
from typing import Dict, Optional, NewType
import threading


JobId = NewType("JobId", str)


@dataclass
class JobInfo:
    """
    In-memory job state for async operations.

    Fields:
        job_id: Unique identifier for the job.
        status: One of queued|running|completed|failed.
        progress: Float in [0.0, 1.0] representing completion.
        output_path: Target CSV path for the harmonized output.
        replay_log_path: Path where the replay log is written.
        error: Optional structured error payload (matches ErrorDetail schema).
        result: Optional result payload (e.g., output/replay paths).
    """
    job_id: JobId
    status: str
    progress: float
    output_path: str
    replay_log_path: str
    error: Optional[Dict] = None
    result: Optional[Dict] = None


# In-memory job registry guarded by a lock for thread-safe updates.
_jobs: Dict[JobId, JobInfo] = {}
_jobs_lock = threading.Lock()


def register_job(job: JobInfo) -> None:
    with _jobs_lock:
        _jobs[job.job_id] = job


def get_job(job_id: JobId) -> Optional[JobInfo]:
    with _jobs_lock:
        return _jobs.get(job_id)


def update_progress(job_id: JobId, processed: int, total: int) -> None:
    with _jobs_lock:
        job = _jobs.get(job_id)
        if not job:
            return
        if total == 0:
            job.progress = 1.0
        else:
            job.progress = min(1.0, processed / total)


def update_job_status(
    job_id: JobId,
    status: str,
    progress: Optional[float] = None,
    error: Optional[Dict] = None,
    result: Optional[Dict] = None,
) -> None:
    with _jobs_lock:
        job = _jobs.get(job_id)
        if not job:
            return
        job.status = status
        if progress is not None:
            job.progress = progress
        if error is not None:
            job.error = error
        if result is not None:
            job.result = result
