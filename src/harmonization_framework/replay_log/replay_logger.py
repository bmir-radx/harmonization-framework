import logging
import json
from dataclasses import dataclass
from ..harmonization_rule import HarmonizationRule

@dataclass
class Event:
    action: HarmonizationRule
    dataset: str

    def to_log(self):
        """
        Serialize an event to a JSON-compatible dict.

        Returns:
            dict with keys:
            - action: serialized harmonization rule
            - dataset: dataset identifier
        """
        log = {
            "action": self.action.serialize(),
            "dataset": self.dataset,
        }
        return log

def _get_log_level(level: int):
    """
    Map a numeric log level to a logging module constant.

    Args:
        level: integer in the range 1-4.
            1 -> CRITICAL
            2 -> ERROR
            3 -> INFO
            4 -> DEBUG

    Returns:
        A logging level constant.
    """
    match level:
        case 1:
            return logging.CRITICAL
        case 2: 
            return logging.ERROR
        case 3:
            return logging.INFO
        case 4:
            return logging.DEBUG
        case _:
            return ValueError(f"Invalid log level: {level}")

def configure_logger(level: int, log_file: str):
    """
    Configure a replay logger that writes JSON lines to a file.

    Args:
        level: integer log level (1-4).
        log_file: path to the output log file.

    Returns:
        A configured logger instance.
    """
    # create logger
    logger = logging.getLogger("ReplayLogger")

    # clear any existing handlers to avoid duplicate log entries
    logger.handlers.clear()

    # set logging level
    log_level = _get_log_level(level)
    logger.setLevel(log_level)

    # formatting. we care only about the message for replay logging.
    formatter = logging.Formatter("%(message)s")

    # file handler for saving logs to disk
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger

def log_operation(logger, action, dataset):
    """
    Log a single replay event for a given harmonization action and dataset.
    """
    event = Event(action, dataset)
    logger.info(json.dumps(event.to_log()))
