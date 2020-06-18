#!/usr/bin/env python3
#
# A prototype API server.
#
# If __main__.py is present in a Python module, it will be executed by default
# if that module is executed, e.g., `python -m my.module`.
#
# https://docs.python.org/3/library/__main__.html
import os

import massgov.pfml.api.app as app
import massgov.pfml.api.authentication as authentication
import massgov.pfml.api.generate_fake_data as fake
import massgov.pfml.util.logging

logger = massgov.pfml.util.logging.get_logger(__package__)


def main():
    massgov.pfml.util.logging.init(__package__)
    start_server()


def start_server():
    try:
        connexion_app = app.create_app()
        create_fake_data()

        app_config = app.get_app_config(connexion_app)
        authentication.get_public_keys(app_config.cognito_user_pool_keys_url)

        enable_reloader = app_config.environment == "local" or app_config.environment == "dev"
        openapi_files = list(
            map(lambda f: os.path.join(app.get_project_root_dir(), f), app.openapi_filenames())
        )

        # `use_reloader` enables a filesystem watcher which will restart the
        # server whenever it detects a file change in Python code. It does not
        # track all file changes, so we add the OpenAPI spec file(s) as well,
        # since a change there does impact the application behavior.
        #
        # For more details:
        # https://werkzeug.palletsprojects.com/en/1.0.x/serving/?highlight=use_reloader#werkzeug.serving.run_simple
        logger.info("Running API Application...")
        connexion_app.run(
            port=app_config.port, use_reloader=enable_reloader, extra_files=openapi_files
        )
    except Exception:
        logger.exception("Server NOT started because of exception")
        raise


def create_fake_data():
    fake.build_fake_data_dictionaries()
    return


main()
