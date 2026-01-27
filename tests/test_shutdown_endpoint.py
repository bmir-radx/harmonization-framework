from harmonization_framework.api.routes import shutdown as shutdown_module


def test_shutdown_endpoint_returns_ok(monkeypatch):
    scheduled = {"delay": None, "func": None, "started": False}

    class FakeTimer:
        def __init__(self, delay, func):
            scheduled["delay"] = delay
            scheduled["func"] = func

        def start(self):
            scheduled["started"] = True

    # Prevent real timers/signals during the test.
    monkeypatch.setattr(shutdown_module.threading, "Timer", FakeTimer)

    response = shutdown_module.shutdown()
    assert response.status == "ok"
    assert "Shutdown initiated" in response.message

    # The shutdown is scheduled asynchronously; ensure it was set up correctly.
    assert scheduled["started"] is True
    assert scheduled["delay"] == 0.1
    assert scheduled["func"] == shutdown_module._send_shutdown_signal
