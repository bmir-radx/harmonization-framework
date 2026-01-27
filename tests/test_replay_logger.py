import logging

from harmonization_framework.replay_log import replay_logger as rlog


def test_configure_logger_clears_handlers(tmp_path):
    log1 = tmp_path / "log1.jsonl"
    log2 = tmp_path / "log2.jsonl"

    logger1 = rlog.configure_logger(3, str(log1))
    assert len(logger1.handlers) == 1

    logger2 = rlog.configure_logger(3, str(log2))
    assert logger2 is logger1
    assert len(logger2.handlers) == 1

    # Ensure the active handler points to the most recent log file
    handler = logger2.handlers[0]
    assert isinstance(handler, logging.FileHandler)
    assert handler.baseFilename == str(log2)
