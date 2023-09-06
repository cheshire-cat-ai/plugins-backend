import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Configure the logger
logging.basicConfig(
    filename='error.log',
    level=logging.DEBUG,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%d/%m/%Y-%H:%M:%S'
)


def error_log(message, log_level="DEBUG"):
    if log_level == "DEBUG":
        logger.debug(message)
    elif log_level == "INFO":
        logger.info(message)
    elif log_level == "WARNING":
        logger.warning(message)
    elif log_level == "ERROR":
        logger.error(message)
    elif log_level == "CRITICAL":
        logger.critical(message)
    else:
        raise ValueError("Invalid log level specified")
