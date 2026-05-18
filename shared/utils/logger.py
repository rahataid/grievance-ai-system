import logging
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
LOG_DIR = ROOT_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
QUEUE_LOG_FILE = LOG_DIR / "queue.log"


def get_queue_logger(name: str = "queue_logger") -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    if not any(
        isinstance(handler, logging.FileHandler) and handler.baseFilename == str(QUEUE_LOG_FILE)
        for handler in logger.handlers
    ):
        handler = logging.FileHandler(QUEUE_LOG_FILE, encoding="utf-8")
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
        )
        logger.addHandler(handler)
        logger.propagate = False
    return logger
