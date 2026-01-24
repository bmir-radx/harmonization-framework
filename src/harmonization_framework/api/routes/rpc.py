from fastapi import APIRouter

from harmonization_framework.api.rpc_errors import ErrorCode, build_error
from harmonization_framework.api.rpc_handlers import handle_get_job, handle_harmonize
from harmonization_framework.api.rpc_models import RpcRequest, RpcResponse

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
  Example: {"field": "rules_file_path"} or {"path_type": "rules_file_path", "path": "/abs/..."}.
"""


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


@router.post("")
def rpc_call(request: RpcRequest) -> RpcResponse:
    """
    Dispatch RPC methods and return a standardized response envelope.

    Supported methods (snake_case; camelCase aliases accepted):
    - harmonize:
        params:
          data_file_path: absolute path to input CSV
          rules_file_path: absolute path to RuleRegistry JSON
          replay_log_file_path: absolute path to write replay log
          output_file_path: absolute path to write harmonized CSV
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
        return handle_harmonize(request)

    if method == "get_job":
        return handle_get_job(request)

    return build_error(ErrorCode.METHOD_NOT_FOUND, f"Unknown method: {request.method}")
