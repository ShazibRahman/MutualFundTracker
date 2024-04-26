
import logging as log
import pathlib
import sys
from datetime import time
from logging.handlers import TimedRotatingFileHandler

from util.DesktopNotification import DesktopNotification

logger_path = (
    pathlib.Path(__file__)
    .parent.parent.joinpath( "logs", "logger.log")
    .resolve()
    .as_posix()
)

# Create the logger
logger = log.getLogger()
logger.setLevel(log.DEBUG)


class ExcludeAESFilter(log.Filter):
    def filter(self, record):
        # Check if the record comes from aes.py
        # If yes, return False to exclude it; otherwise, return True
        # print(record)
        if record.filename == "aes.py":
            return False
        return True


# Define a TimedRotatingFileHandler to rotate logs daily and keep only the last 5 days' logs
handler = TimedRotatingFileHandler(
    filename=logger_path,
    when="D",  # Rotate daily
    interval=1,  # Interval in days
    backupCount=5,  # Keep logs for the last 5 days
    atTime=time(0, 0, 0),  # Rotate at midnight
)
handler.addFilter(ExcludeAESFilter())

# Define the log format
formatter = log.Formatter(
    "%(levelname)s - (%(asctime)s): %(message)s (Line: %(lineno)d [%(filename)s]"
)
formatter.datefmt = "%m/%d/%Y %I:%M:%S %p"

# Set the formatter for the file handler
handler.setFormatter(formatter)
handler.setLevel(log.INFO)

# Add the handler to the logger
logger.addHandler(handler)

# Add a stream handler to output logs to stdout
stream_handler = log.StreamHandler(sys.stdout)
stream_handler.setLevel(log.DEBUG)
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)


# Define the function to log uncaught exceptions
def log_uncaught_exceptions(exctype, value, traceback):
    """
    Log uncaught exceptions
    :param exctype:
    :param value:
    :param traceback:
    :return:
    """

    if isinstance(value, KeyboardInterrupt):
        log.info("Keyboard Interrupt instance detected")
        print(logger.handlers)
        for loggers_handlers in logger.handlers:
            logger.removeHandler(loggers_handlers)

        return

    logger.exception("Uncaught exception", exc_info=(exctype, value, traceback))
    DesktopNotification("Error", f"{exctype} : {value}")


# Set the exception hook
sys.excepthook = log_uncaught_exceptions


# Export the logger function
def getLogger() -> log.Logger:
    return logger
