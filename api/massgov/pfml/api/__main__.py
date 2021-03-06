#!/usr/bin/env python3

#
# A prototype API server.
#
# If __main__.py is present in a Python module, it will be executed by default
# if that module is executed, e.g., `python -m my.module`.
#
# https://docs.python.org/3/library/__main__.html

# Import and initialize the NewRelic Python agent.
#
# This must be done as early as possible, even before other imports, and even if it makes style
# enforcement unhappy.
# https://docs.newrelic.com/docs/agents/python-agent/python-agent-api/initialize
from massgov.pfml.util.newrelic import init_newrelic  # isort:skip

init_newrelic()

import os

import massgov.pfml.api.api
import massgov.pfml.api.app as app
import massgov.pfml.api.authentication as authentication
import massgov.pfml.util.logging
import massgov.pfml.util.logging.audit as audit_logging
from massgov.pfml.api.gunicorn_wrapper import GunicornAppWrapper

logger = massgov.pfml.util.logging.get_logger(__package__)


def main():
    audit_logging.init_security_logging()
    massgov.pfml.util.logging.init(__package__)
    start_server()


def start_server():
    try:
        connexion_app = app.create_app()
        app_config = app.get_app_config(connexion_app)
        authentication.get_public_keys(app_config.cognito_user_pool_keys_url)
        authentication.configure_azure_ad()

        logger.info("Running API Application...")
        running_in_local = app_config.environment in ("local", "dev")

        if running_in_local:
            # If running locally, run the connexion server directly without a WSGI production-ready wrapper
            # and enable a filesystem watcher using `use_reloader`, which will restart the
            # server whenever it detects a file change in Python code.
            #
            # It does not track all file changes, so we add the OpenAPI spec file(s)
            # as well, since a change there does impact the application behavior.
            #
            # For more details:
            # https://werkzeug.palletsprojects.com/en/1.0.x/serving/?highlight=use_reloader#werkzeug.serving.run_simple
            openapi_files = list(
                map(lambda f: os.path.join(app.get_project_root_dir(), f), app.openapi_filenames())
            )
            connexion_app.run(
                port=app_config.port,
                use_reloader=True,
                extra_files=openapi_files,
                reloader_type="stat",
            )
        else:
            # If running in a deployed environment, run it with a multi-worker production-ready WSGI wrapper.
            gunicorn_app = GunicornAppWrapper(connexion_app.app, app_config.port)
            gunicorn_app.run()

    except Exception:
        logger.exception("Server NOT started because of exception")
        raise


main()
