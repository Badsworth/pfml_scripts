#!/usr/bin/env python3
#
# A prototype API server.
#
# If __main__.py is present in a Python module, it will be executed by default
# if that module is executed, e.g., `python -m my.module`.
#
# https://docs.python.org/3/library/__main__.html

import logging
import sys

import pytest

import massgov.pfml.api
import massgov.pfml.api.generate_fake_data as fake

logging.basicConfig(level=logging.INFO)


def main():
    start_server()


def self_test():
    logging.info("self test start")
    result = pytest.main(args=["--verbose"])
    logging.info("self test done, result %r", result)
    if result != 0:
        sys.exit(result)


def start_server():
    app = massgov.pfml.api.create_app()
    create_fake_data()
    app.run(port=1550)


def create_fake_data():
    fake.build_fake_data_dictionaries()
    return


main()
