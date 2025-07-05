import logging
import sys

from loguru import logger


class InterceptHandler(logging.Handler):
    def emit(self, record):
        # Convert standard logging record to Loguru format
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        logger.opt(
            depth=6,
            exception=record.exc_info,
        ).log(level, record.getMessage())


def setup_loguru():
    logging.basicConfig(handlers=[InterceptHandler()], level=logging.INFO)
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        logging.getLogger(name).handlers = [InterceptHandler()]
        logging.getLogger(name).propagate = False

    logger.remove()
    logger.add(sys.stdout, level="INFO", backtrace=True, diagnose=True)

