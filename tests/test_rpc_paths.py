import os

from harmonization_framework.api.rpc_models import HarmonizeParams
from harmonization_framework.api.rpc_handlers import _validate_paths


def test_validate_paths_rejects_relative_paths(tmp_path):
    params = HarmonizeParams(
        data_file_path="relative.csv",
        rules_file_path=str(tmp_path / "rules.json"),
        output_file_path=str(tmp_path / "out.csv"),
        replay_log_file_path=str(tmp_path / "replay.log"),
        mode="all",
        overwrite=False,
    )
    response = _validate_paths(params)
    assert response is not None
    assert response.error.code == "INVALID_PATH"
    assert response.error.details["path"] == "relative.csv"
    assert response.error.details["path_type"] == "data_file_path"


def test_validate_paths_missing_inputs(tmp_path):
    data_path = tmp_path / "input.csv"
    rules_path = tmp_path / "rules.json"

    params = HarmonizeParams(
        data_file_path=str(data_path),
        rules_file_path=str(rules_path),
        output_file_path=str(tmp_path / "out.csv"),
        replay_log_file_path=str(tmp_path / "replay.log"),
        mode="all",
        overwrite=False,
    )
    response = _validate_paths(params)
    assert response is not None
    assert response.error.code == "FILE_NOT_FOUND"
    assert response.error.details["path_type"] == "data_path"


def test_validate_paths_rejects_existing_output_without_overwrite(tmp_path):
    data_path = tmp_path / "input.csv"
    rules_path = tmp_path / "rules.json"
    output_path = tmp_path / "out.csv"

    data_path.write_text("a,b\n1,2\n")
    rules_path.write_text("{}")
    output_path.write_text("already")

    params = HarmonizeParams(
        data_file_path=str(data_path),
        rules_file_path=str(rules_path),
        output_file_path=str(output_path),
        replay_log_file_path=str(tmp_path / "replay.log"),
        mode="all",
        overwrite=False,
    )
    response = _validate_paths(params)
    assert response is not None
    assert response.error.code == "ALREADY_EXISTS"
    assert response.error.details["path"] == str(output_path)


def test_validate_paths_accepts_valid_paths(tmp_path):
    data_path = tmp_path / "input.csv"
    rules_path = tmp_path / "rules.json"

    data_path.write_text("a,b\n1,2\n")
    rules_path.write_text("{}")

    params = HarmonizeParams(
        data_file_path=str(data_path),
        rules_file_path=str(rules_path),
        output_file_path=str(tmp_path / "out.csv"),
        replay_log_file_path=str(tmp_path / "replay.log"),
        mode="all",
        overwrite=False,
    )
    response = _validate_paths(params)
    assert response is None
