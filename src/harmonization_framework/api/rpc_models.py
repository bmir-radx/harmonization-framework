from typing import Dict, Optional

from pydantic import BaseModel, ConfigDict


class HarmonizeParams(BaseModel):
    """
    Parameters for the harmonize RPC call.

    Required:
        data_file_path: absolute path to the input CSV file.
        rules_file_path: absolute path to a RuleSet JSON file.
        replay_log_file_path: absolute path for the replay log output.
        output_file_path: absolute path for the harmonized CSV output.

    Optional:
        overwrite: when True, allows output_path to be overwritten if it already exists.

    All rules in the rules file are applied. To restrict which rules run,
    construct a rules file containing only the desired targets.
    """
    data_file_path: str
    rules_file_path: str
    replay_log_file_path: str
    output_file_path: str
    overwrite: bool = False

    model_config = ConfigDict(populate_by_name=True)


class RpcRequest(BaseModel):
    """RPC request envelope with method name and parameters payload."""
    method: str
    params: Dict


class RpcResponse(BaseModel):
    """RPC response envelope."""
    status: str
    result: Optional[Dict] = None
    error: Optional["ErrorDetail"] = None
    job_id: Optional[str] = None


from harmonization_framework.api.rpc_errors import ErrorDetail  # noqa: E402
