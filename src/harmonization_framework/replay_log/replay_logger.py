import logging
import json
from dataclasses import dataclass
from ..rule import HarmonizationRule

@dataclass
class Event:
    action: HarmonizationRule
    dataset: str

    def to_log(self):
        log = {
            "action": self.action.serialize(),
            "dataset": self.dataset,
        }
        return log

def _get_log_level(level: int):
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
    # create logger
    logger = logging.getLogger("ReplayLogger")

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
    event = Event(action, dataset)
    logger.info(json.dumps(event.to_log()))
