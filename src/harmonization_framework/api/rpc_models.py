from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class HarmonizationPair(BaseModel):
    """Source/target column pair."""
    source: str = Field(..., description="Source column name")
    target: str = Field(..., description="Target column name")


class HarmonizeParams(BaseModel):
    """
    Parameters for the harmonize RPC call.

    Required:
        data_file_path: absolute path to the input CSV file.
        rules_file_path: absolute path to a RuleRegistry JSON file.
        replay_log_file_path: absolute path for the replay log output.
        output_file_path: absolute path for the harmonized CSV output.
        mode: "pairs" to apply a specific subset of rules, or "all" to apply all rules.

    Optional:
        harmonization_pairs: list of source/target column mappings (required when mode="pairs").
        overwrite: when True, allows output_path to be overwritten if it already exists.
    """
    data_file_path: str
    rules_file_path: str
    replay_log_file_path: str
    output_file_path: str
    mode: Literal["pairs", "all"]
    harmonization_pairs: Optional[List[HarmonizationPair]] = Field(
        None,
        alias="pairs",
        description="List of (source, target) column mappings when mode='pairs'.",
    )
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
