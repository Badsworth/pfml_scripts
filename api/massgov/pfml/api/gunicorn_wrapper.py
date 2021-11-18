import multiprocessing
import os
import platform
import pwd
import threading

import connexion
import gunicorn.app.base

import massgov.pfml.util.logging

logger = massgov.pfml.util.logging.get_logger(__name__)


class GunicornAppWrapper(gunicorn.app.base.BaseApplication):
    """
    Wrapper inspired by the Gunicorn Custom Application documentation.
    See: https://docs.gunicorn.org/en/stable/custom.html

    This wraps the core flask application configured by Connexion and
    runs it with Gunicorn.
    """

    def __init__(self, app: connexion.FlaskApp, port: int):
        # Run Gunicorn with the recommended default of (2 * num_cores) + 1.
        #
        # Also provide more than 1 thread per worker, so each worker could
        # potentially handle multiple requests using its CPU if it is waiting
        # for a database (I/O) transaction to complete.
        workers = (multiprocessing.cpu_count() * 2) + 1
        threads = 4

        self.options = {
            # Bind the API to the provided port on 0.0.0.0 instead of 127.0.0.1.
            # This allows connections to originate from outside the container's network.
            "bind": "%s:%s" % ("0.0.0.0", port),  # nosec
            "workers": workers,
            "threads": threads,
            # Use the gthread class to enable multi-threading.
            "worker-class": "gthread",
            "log-level": "info",
            # Set keepalive timeout to 355 seconds, a few seconds higher than the 350 seconds set by NLB.
            # The NLB timeout is not adjustable, so adjust the target (API) timeout instead.
            "keep-alive": 355,
            "post_request": post_request_hook,
        }
        logger.info("workers %i, threads %i", workers, threads, extra={"options": self.options})

        self.application = app
        super().__init__()

        # Disable Gunicorn's own error log formatter which sends to stdout. We configure the
        # "gunicorn.error" logger ourselves. See massgov/pfml/util/logging/__init__.py
        self.cfg.set("errorlog", None)

    def load_config(self):
        config = {
            key: value
            for key, value in self.options.items()
            if key in self.cfg.settings and value is not None
        }
        for key, value in config.items():
            self.cfg.set(key.lower(), value)

    def load(self) -> connexion.FlaskApp:
        logger.info(
            "start worker: hostname %s, pid %i, user %i(%s)",
            platform.node(),
            os.getpid(),
            os.getuid(),
            pwd.getpwuid(os.getuid()).pw_name,
            extra={"hostname": platform.node()},
        )
        return self.application


post_request_hook_lock = threading.Lock()
total_request_count = 0


def post_request_hook(_worker, _req, _environ, _resp):
    """Log some statistics for this worker process."""
    global total_request_count
    with post_request_hook_lock:
        total_request_count += 1
        request_count = total_request_count
    if (request_count % 1000) == 0:
        logger.info(
            "worker status: pid %i, request count %i, threads %i (%s)",
            os.getpid(),
            total_request_count,
            threading.active_count(),
            " ".join(thr.name for thr in threading.enumerate()),
        )
