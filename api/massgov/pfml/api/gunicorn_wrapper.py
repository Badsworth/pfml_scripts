import multiprocessing

import connexion
import gunicorn.app.base


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
        # Also provide twice the number of threads, so each worker could
        # potentially handle multiple requests using its CPU if it is waiting
        # for a database (I/O) transaction to complete.
        workers = (multiprocessing.cpu_count() * 2) + 1
        threads = 2 * workers

        self.options = {
            # Bind the API to the provided port on 0.0.0.0 instead of 127.0.0.1.
            # This allows connections to originate from outside the container's network.
            "bind": "%s:%s" % ("0.0.0.0", port),
            "workers": workers,
            "threads": threads,
            # Use the gthread class to enable multi-threading.
            "worker-class": "gthread",
            "log-level": "info",
        }

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
        return self.application
