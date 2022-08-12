import logging
import structlog
from os import environ

logging.basicConfig(
    level=getattr(logging, environ.get("ZNAYKO_LOG_LEVEL", "INFO")), format=None
)


logger = structlog.wrap_logger(
    logger=logging.getLogger("znayko"),
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
        structlog.processors.TimeStamper(fmt="ZNAYKO %m/%d|%H:%M.%S"),
        structlog.dev.ConsoleRenderer(),
    ],
)
