"""pact test for user service client"""

import logging
import os

from pact import Verifier
from massgov.pfml.db.models.factories import ApplicationFactory
from datetime import date, datetime
from freezegun import freeze_time



log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


# PACT_UPLOAD_URL = (
#     "http://127.0.0.1/pacts/provider/UserService/consumer"
#     "/User_ServiceClient/version"
# )
PACT_FILE = "pacts/claimant_portal-pfml_api.json"
# PACT_BROKER_URL = "http://localhost:8080"
# PACT_BROKER_USERNAME = "pactbroker"
# PACT_BROKER_PASSWORD = "pactbroker"

PACT_MOCK_HOST = 'localhost'
PACT_MOCK_PORT = 1550
PACT_URL = "http://{}:{}/v1".format(PACT_MOCK_HOST, PACT_MOCK_PORT)
PACT_DIR = os.path.dirname(os.path.realpath(__file__))

@freeze_time("2020-01-01")
def test_example(user):
    application = ApplicationFactory.create(user=user, updated_time=datetime.now())

    auth_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhIjoiYiIsImV4cCI6MTYxNTM0MTc3OSwic3ViIjoiNmY2NzZhYWMtN2U4YS00YzYwLTk4ODQtYWE0YjUzZmQwMTE2In0.vwVQ1X9Osmb1N4IEcn1W5ohoZoxA7ES0Q69lQlFiANI"
    verifier = Verifier(provider='API service', provider_base_url=PACT_URL, custom_provider_header=f"Authorization: Bearer {auth_token}")

    print(auth_token)
    output, logs = verifier.verify_pacts(PACT_FILE, verbose=False) #  provider_states_setup_url="{}/_pact/provider_states".format(PACT_URL))

    assert (output == 0)
