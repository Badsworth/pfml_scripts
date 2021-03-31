"""pact test for user service client"""

import logging
import os

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

def test_example():
    verifier = Verifier(provider='API service', provider_base_url=PACT_URL)

    # Docs for custom provider header: https://github.com/pact-foundation/pact-python#--custom-provider-header

    output, logs = verifier.verify_pacts(PACT_FILE, verbose=False)

    assert (output == 0)
