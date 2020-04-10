#!/usr/bin/env python3
#
# A prototype API server.
#
# If __main__.py is present in a Python module, it will be executed by default
# if that module is executed, e.g., `python -m my.module`.
#
# https://docs.python.org/3/library/__main__.html

import massgov.pfml.api
import massgov.pfml.api.generate_fake_data as fake
import massgov.pfml.util.logging

logger = massgov.pfml.util.logging.get_logger(__package__)


def main():
    massgov.pfml.util.logging.init(__package__)
    start_server()


def start_server():
    try:
        app = massgov.pfml.api.create_app()
        create_fake_data()
        app.run(port=1550)
    except Exception:
        logger.exception("Server NOT started because of exception")
        raise


def create_fake_data():
    fake.build_fake_data_dictionaries()
    return


main()
