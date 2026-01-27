import pytest

from harmonization_framework.api import sidecar
from harmonization_framework.api.sidecar import _parse_port, _resolve_host


def test_parse_port_accepts_valid_range():
    assert _parse_port("1") == 1
    assert _parse_port("65535") == 65535


def test_parse_port_rejects_invalid_values():
    with pytest.raises(ValueError, match="integer"):
        _parse_port("nope")
    with pytest.raises(ValueError, match="range"):
        _parse_port("0")
    with pytest.raises(ValueError, match="range"):
        _parse_port("70000")


def test_resolve_host_defaults_to_loopback():
    assert _resolve_host(None) == "127.0.0.1"
    assert _resolve_host("") == "127.0.0.1"
    assert _resolve_host("localhost") == "127.0.0.1"


def test_resolve_host_rejects_non_loopback():
    with pytest.raises(ValueError, match="loopback"):
        _resolve_host("0.0.0.0")
    with pytest.raises(ValueError, match="loopback"):
        _resolve_host("192.168.1.1")


def test_main_exits_when_port_missing(monkeypatch):
    monkeypatch.delenv("API_PORT", raising=False)
    monkeypatch.setattr(sidecar.uvicorn, "run", lambda *args, **kwargs: None)

    with pytest.raises(SystemExit) as excinfo:
        sidecar.main()

    assert excinfo.value.code == 2


def test_main_exits_on_invalid_port(monkeypatch):
    monkeypatch.setenv("API_PORT", "not-a-port")
    monkeypatch.setattr(sidecar.uvicorn, "run", lambda *args, **kwargs: None)

    with pytest.raises(SystemExit) as excinfo:
        sidecar.main()

    assert excinfo.value.code == 2


def test_main_exits_on_invalid_host(monkeypatch):
    monkeypatch.setenv("API_PORT", "54321")
    monkeypatch.setenv("API_HOST", "0.0.0.0")
    monkeypatch.setattr(sidecar.uvicorn, "run", lambda *args, **kwargs: None)

    with pytest.raises(SystemExit) as excinfo:
        sidecar.main()

    assert excinfo.value.code == 2


def test_main_runs_with_valid_env(monkeypatch):
    calls = {}

    def fake_run(app, host, port, log_level):
        calls["host"] = host
        calls["port"] = port
        calls["log_level"] = log_level

    monkeypatch.setenv("API_PORT", "54321")
    monkeypatch.setenv("API_HOST", "127.0.0.1")
    monkeypatch.setattr(sidecar.uvicorn, "run", fake_run)

    sidecar.main()

    assert calls == {"host": "127.0.0.1", "port": 54321, "log_level": "info"}
