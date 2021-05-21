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
import os  # isort:skip
import newrelic.agent  # isort:skip

newrelic.agent.initialize(
    config_file=os.path.join(os.path.dirname(__file__), "../../..", "newrelic.ini"),
    environment=os.environ.get("ENVIRONMENT", "local"),
)

import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from sentry_sdk.integrations.logging import ignore_logger

import massgov.pfml.api.api
import massgov.pfml.api.app as app
import massgov.pfml.api.authentication as authentication
import massgov.pfml.util.logging
import massgov.pfml.util.logging.audit as audit_logging
from massgov.pfml.api.gunicorn_wrapper import GunicornAppWrapper
from massgov.pfml.fineos.exception import FINEOSFatalUnavailable
from massgov.pfml.util.sentry import sanitize_sentry_event

logger = massgov.pfml.util.logging.get_logger(__package__)


def main():
    audit_logging.init_security_logging()
    massgov.pfml.util.logging.init(__package__)
    initialize_flask_sentry()
    start_server()


def initialize_flask_sentry():
    if os.environ.get("ENABLE_SENTRY", "0") == "1":

        api_release = (
            ""
            if not os.environ.get("RELEASE_VERSION")
            else 'massgov-pfml-api@{os.environ.get("RELEASE_VERSION").replace("api/", "")}'
        )

        sentry_sdk.init(
            dsn="https://3d9b96c9cef846ae8cbd9630530e719c@o514801.ingest.sentry.io/5618604",
            environment=os.environ.get("ENVIRONMENT", "local"),
            integrations=[FlaskIntegration()],
            request_bodies="never",
            before_send=sanitize_sentry_event,
            # Ignore temporary unavailability from FINEOS API.
            # Outages should be captured through percentage-based New Relic alarms.
            ignore_errors=[FINEOSFatalUnavailable],
            # Disable tracing since we rely on New Relic already.
            traces_sample_rate=0,
            release=api_release,
            debug=False,
        )
        ignore_logger("massgov.pfml.util.logging.audit")


def start_server():
    try:
        connexion_app = app.create_app()
        app_config = app.get_app_config(connexion_app)
        authentication.get_public_keys(app_config.cognito_user_pool_keys_url)

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
            connexion_app.run(port=app_config.port, use_reloader=True, extra_files=openapi_files)
        else:
            # If running in a deployed environment, run it with a multi-worker production-ready WSGI wrapper.
            gunicorn_app = GunicornAppWrapper(connexion_app.app, app_config.port)
            gunicorn_app.run()

    except Exception:
        logger.exception("Server NOT started because of exception")
        raise


main()
