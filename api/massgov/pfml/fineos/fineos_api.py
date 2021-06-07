import datetime
import uuid

import oauthlib.oauth2
import requests.packages.urllib3.connection
import requests_oauthlib

import massgov.pfml.fineos
import massgov.pfml.fineos.models
import massgov.pfml.util.logging

logger = massgov.pfml.util.logging.get_logger(__name__)

orig_connect = requests.packages.urllib3.connection.VerifiedHTTPSConnection.connect


def connect_log_certificate(self):
    orig_connect(self)
    cert = self.sock.getpeercert()
    logger.info("peer name %s", self.sock.getpeername())
    logger.info("peer certificate %s:%s", self.host, self.port, extra=cert)


requests.packages.urllib3.connection.VerifiedHTTPSConnection.connect = connect_log_certificate  # type: ignore


def handler():
    call_fineos()


def call_fineos():
    print("here")
    backend = oauthlib.oauth2.BackendApplicationClient(client_id="1ral5e957i0l9shul52bhk0037")
    oauth_session = requests_oauthlib.OAuth2Session(client=backend, scope="service-gateway/all")
    cps = massgov.pfml.fineos.FINEOSClient(
        integration_services_api_url="https://dt2-api.masspfml.fineos.com/integration-services/",
        customer_api_url="https://dt2-api.masspfml.fineos.com/customerapi/",
        group_client_api_url="https://dt2-api.masspfml.fineos.com/groupclientapi/",
        wscomposer_url="https://dt2-api.masspfml.fineos.com/integration-services/wscomposer/",
        wscomposer_user_id="CONTENT",
        oauth2_url="https://dt2-api.masspfml.fineos.com/oauth2/token",
        client_id="1ral5e957i0l9shul52bhk0037",
        client_secret="45qqfa12nl9gm8ts2gd6nl552o7vur83l7i34k3vv6f2l5077gg",
        oauth_session=oauth_session,
    )

    employer_fein = "457506831"

    employer_id = cps.find_employer(employer_fein)
    employer = cps.read_employer(employer_fein)
    print(employer)
    user_id = "pfml_api_{}".format(str(uuid.uuid4()))
    details = cps.read_customer_details(user_id)
