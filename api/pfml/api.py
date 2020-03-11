#!/usr/bin/env python3
#
# A prototype API server.
#

import logging
import sys
import pytest

logging.basicConfig(level=logging.INFO)
sys.path.append("./src")

def main():
    self_test()
    if "--test-only" in sys.argv:
        return
    start_server()

def self_test():
    logging.info("self test start")
    result = pytest.main(args=["--verbose"])
    logging.info("self test done, result %r", result)
    if result != 0:
        sys.exit(result)

def start_server():
    import pfml

    app = pfml.create_app()
    create_fake_data()
    app.run(port=1550)

def create_fake_data():
    import pfml.generate_fake_data as fake

    fake.build_fake_data_dictionaries()
    return


main()
