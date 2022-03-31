#
# Example of using the FINEOS client.
#

import datetime
import uuid

import oauthlib.oauth2
import requests.packages.urllib3.connection
import requests_oauthlib

import massgov.pfml.fineos
import massgov.pfml.fineos.models
import massgov.pfml.util.logging

logger = massgov.pfml.util.logging.get_logger("massgov.pfml.fineos.example")

orig_connect = requests.packages.urllib3.connection.VerifiedHTTPSConnection.connect


def connect_log_certificate(self):
    orig_connect(self)
    cert = self.sock.getpeercert()
    logger.info("peer name %s", self.sock.getpeername())
    logger.info("peer certificate %s:%s", self.host, self.port, extra=cert)


requests.packages.urllib3.connection.VerifiedHTTPSConnection.connect = connect_log_certificate  # type: ignore


def main():
    massgov.pfml.util.logging.init(__package__)

    # Create the client.
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

    # Send some requests.
    # healthy = cps.health_check("hackathon_91")
    # logger.info("healthy %s", healthy)


    user_id = 'pfml_api_2ab897cd-d401-48ab-a95c-a44fa1dc57d7'
    absence_id = 'NTN-216201-ABS-01'
    paid_leave_id = 'PL ABS-216212'

    x = cps.get_absence(user_id, absence_id)
    print(x)

    print()
    print()
    print()
    print()

    cps.get_payments(user_id, paid_leave_id)

    print()
    print()
    print()
    print()

main()
