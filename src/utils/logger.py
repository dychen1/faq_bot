import logging
import queue
import sys
import threading
from logging.handlers import QueueHandler, QueueListener

from src.settings import settings


def get_queue_logger(
    app_name: str = "app",
    queue_size: int = 10000,
) -> tuple[logging.Logger, QueueListener]:
    """
    Sets up a queue-based logger for asynchronous logging.

    Args:
        file_path (Path): Directory path for log files
        app_name (str): Name of the application/logger

    Returns:
        tuple[logging.Logger, QueueListener]: Configured logger and its queue listener
    """
    logger: logging.Logger = logging.getLogger(app_name)
    level: str = ("debug" if settings.debug else "info").upper()
    logger.setLevel(level)

    # The format string already includes correlation_id
    log_format: str = "%(name)s - %(correlation_id)s - %(asctime)s - %(funcName)s - %(levelname)s - %(message)s"
    formatter: logging.Formatter = logging.Formatter(log_format)

    # Create handlers
    handlers: list[logging.Handler] = []

    console_handler = logging.StreamHandler(stream=sys.stdout)
    console_handler.setFormatter(formatter)
    handlers.append(console_handler)

    # Setup queue
    log_queue: queue.Queue = queue.Queue(queue_size)
    queue_handler = QueueHandler(log_queue)
    logger.addHandler(queue_handler)

    # Setup listener
    listener = QueueListener(
        log_queue,
        *handlers,
        respect_handler_level=True,  # Ensures handlers only receive records they're configured for
    )
    listener.start()  # Spawns new thread for logging operations

    print(f"Initialized queue logger on {level} level")
    print(f"Active threads: {[t.name for t in threading.enumerate()]}")

    return logger, listener


def get_app_logger(app_name: str = "app") -> logging.Logger:
    """
    Returns a logger for the application. Used to fetch single queue logger for the application.
    """
    return logging.getLogger(app_name)
