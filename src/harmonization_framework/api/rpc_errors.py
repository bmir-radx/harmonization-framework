from enum import Enum
from typing import Dict, Optional

from pydantic import BaseModel


class ErrorDetail(BaseModel):
    """Structured error payload for RPC responses."""
    code: str
    message: str
    details: Optional[Dict] = None


class ErrorCode(str, Enum):
    """
    Stable error codes used across RPC responses.

    These codes are intentionally small in number; use `error.details` to identify
    the field/path/context that caused the failure.
    """
    # A required path is not absolute or is malformed.
    INVALID_PATH = "INVALID_PATH"
    # An expected file does not exist (data_path or rules_path).
    FILE_NOT_FOUND = "FILE_NOT_FOUND"
    # Output path exists and overwrite was not allowed.
    ALREADY_EXISTS = "ALREADY_EXISTS"
    # A required field is missing from the request params.
    MISSING_FIELD = "MISSING_FIELD"
    # Request params failed model validation.
    VALIDATION_ERROR = "VALIDATION_ERROR"
    # Requested rule pairs cannot be found in the registry.
    RULE_NOT_FOUND = "RULE_NOT_FOUND"
    # Job id does not correspond to a known job.
    JOB_NOT_FOUND = "JOB_NOT_FOUND"
    # Rules file could not be parsed or is invalid.
    INVALID_FORMAT = "INVALID_FORMAT"
    # Harmonization failed during execution.
    HARMONIZATION_FAILED = "HARMONIZATION_FAILED"
    # Method name is unknown.
    METHOD_NOT_FOUND = "METHOD_NOT_FOUND"


def build_error(code: ErrorCode, message: str, details: Optional[Dict] = None) -> "RpcResponse":
    """Helper to build a standardized error response."""
    from harmonization_framework.api.rpc_models import RpcResponse

    return RpcResponse(
        status="error",
        error=ErrorDetail(code=code.value, message=message, details=details),
    )
