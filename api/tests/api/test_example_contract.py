"""pact test for user service client"""

import logging
import os
import requests
import asyncio

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

async def run_app(app):
    print("running the web server")
    app_config = api_app.get_app_config(app)
    openapi_files = list(
        map(lambda f: os.path.join(api_app.get_project_root_dir(), f), api_app.openapi_filenames())
    )
    # this next call is blocking. I don't know how to run it in the background
    app.run(port=app_config.port, use_reloader=True, extra_files=openapi_files)

async def run_request(app):
    print("about to wait")
    try:
        task = asyncio.wait_for(run_app(app), 50)
        await asyncio.sleep(3)
        await task
        print("waited")
        # below this line doesn't get run because the above line is blocking
        print("setup run!")
        # r = requests.get('localhost:1550/v1/status')
        # os.environ['NO_PROXY'] = '127.0.0.1'
        # r = requests.get('http://127.0.0.1:1550/v1/status')
        # r = requests.get('https://xkcd.com/1906/')
        print(r)
        assert False
        # task.cancel()
        # await task
    except asyncio.CancelledError:
        print("Task cancelled")
    except asyncio.TimeoutError:
        print('timeout!')


def test_setup(app):
    asyncio.run(run_request(app))


def test_example():
    verifier = Verifier(provider='API service', provider_base_url=PACT_URL)

    # Docs for custom provider header: https://github.com/pact-foundation/pact-python#--custom-provider-header

    output, logs = verifier.verify_pacts(PACT_FILE, verbose=False)

    assert (output == 0)
