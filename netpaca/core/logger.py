"""
This file contains logging support for asyncio based applications.  As of Python3.8 the standard logging package does
not natively support asyncio.  The Caller is expected to call `start_background_logging()` and provide a logging
configuration dictionary, as defined in
https://docs.python.org/3.8/library/logging.config.html#logging.config.dictConfig. From this data, the handlers will be
redirected to a backgroun Thread using the native logging LocalQueueHandler.

When background logging is no longer required, for example when all asyncio code has completed, the Caller can then
execute the `stop_background_logging()` function to stop the Thread and flush stdout so that all records are finished
being processed.

References
----------
This implementation was adapted from:
https://www.zopatista.com/python/2019/05/11/asyncio-logging/
"""

# -----------------------------------------------------------------------------
# System Imports
# -----------------------------------------------------------------------------

from typing import Set
import sys
import asyncio
from queue import SimpleQueue as Queue

from logging.config import dictConfig
from logging import getLogger
import logging
import logging.handlers


__all__ = ["start_background_logging", "stop_background_logging", "get_logger"]


_g_quelgr_listener: logging.handlers.QueueListener


class LocalQueueHandler(logging.handlers.QueueHandler):
    def emit(self, record: logging.LogRecord) -> None:
        try:
            self.enqueue(record)

        except asyncio.CancelledError:
            raise

        except asyncio.QueueFull:
            self.handleError(record)


def setup_logging_queue(logger_names) -> None:
    """
    Move log handlers to a separate thread.

    Replace all configured handlers with a LocalQueueHandler, and start a
    logging.QueueListener holding the original handlers.
    """
    global _g_quelgr_listener
    queue = Queue()
    handlers: Set[logging.Handler] = set()
    que_handler = LocalQueueHandler(queue)

    for lname in logger_names:
        lgr = logging.getLogger(lname)
        lgr.addHandler(que_handler)
        for h in lgr.handlers[:]:
            if h is not que_handler:
                lgr.removeHandler(h)
                handlers.add(h)

    _g_quelgr_listener = logging.handlers.QueueListener(
        queue, *handlers, respect_handler_level=True
    )
    _g_quelgr_listener.start()


def start_background_logging(config):
    config["version"] = 1
    dictConfig(config)
    setup_logging_queue(config.get("loggers") or [])


def stop_background_logging():
    _g_quelgr_listener.stop()
    sys.stdout.flush()


def get_logger():
    return getLogger(__package__)
