"""pact test for user service client"""

import logging
import os
import requests

import massgov.pfml.api.app as api_app
from pact import Verifier
from massgov.pfml.db.models.factories import ApplicationFactory
from datetime import date, datetime
from freezegun import freeze_time


log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

PACT_FILE = "pacts/claimant_portal-pfml_api.json"

PACT_MOCK_HOST = 'localhost'
PACT_MOCK_PORT = 1550
PACT_URL = "http://{}:{}/v1".format(PACT_MOCK_HOST, PACT_MOCK_PORT)
PACT_DIR = os.path.dirname(os.path.realpath(__file__))

def test_setup(app):
    app_config = api_app.get_app_config(app)
    openapi_files = list(
        map(lambda f: os.path.join(api_app.get_project_root_dir(), f), api_app.openapi_filenames())
    )
    # this next call is blocking. I don't know how to run it in the background
    app.run(port=app_config.port, use_reloader=True, extra_files=openapi_files)

    # below this line doesn't get run because the above line is blocking
    print("setup run!")
    r = requests.get('http://localhost:1550/v1/status')
    # r = requests.get('https://xkcd.com/1906/')
    print(r)
    assert False


def test_example():
    verifier = Verifier(provider='API service', provider_base_url=PACT_URL)

    # Docs for custom provider header: https://github.com/pact-foundation/pact-python#--custom-provider-header

    output, logs = verifier.verify_pacts(PACT_FILE, verbose=False)

    assert (output == 0)
