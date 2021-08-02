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
from massgov.pfml.types import Fein

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

    employer_fein = "179892886"

    employer_id = cps.find_employer(Fein(employer_fein))
    logger.info("Employer ID is {}".format(employer_id))

    user_id = "pfml_api_{}".format(str(uuid.uuid4()))
    logger.info("FINEOS Web ID to register is {}".format(user_id))

    employee_registration = massgov.pfml.fineos.models.EmployeeRegistration(
        user_id=user_id,
        customer_number=None,
        date_of_birth=datetime.date(1753, 1, 1),
        email=None,
        employer_id=employer_id,
        first_name=None,
        last_name=None,
        national_insurance_no=784569632,
    )
    cps.register_api_user(employee_registration)

    details = cps.read_customer_details(user_id)
    logger.info("details %s %s", details.firstName, details.lastName)

    absence_case = massgov.pfml.fineos.models.customer_api.AbsenceCase(
        additionalComments="Test " + str(datetime.datetime.now()),
        intakeSource="Self-Service",
        notifiedBy="Employee",
        reason="Child Bonding",
        reasonQualifier1="Foster Care",
        reasonQualifier2="",
        notificationReason="Bonding with a new child (adoption/ foster care/ newborn)",
        timeOffLeavePeriods=[
            massgov.pfml.fineos.models.customer_api.TimeOffLeavePeriod(
                startDate=datetime.date(2020, 8, 2),
                endDate=datetime.date(2020, 10, 2),
                lastDayWorked=datetime.date(2020, 7, 30),
                expectedReturnToWorkDate=datetime.date(2020, 10, 24),
                startDateFullDay=True,
                endDateFullDay=True,
                status="Known",
            )
        ],
    )
    new_case = cps.start_absence(user_id, absence_case)
    cps.complete_intake(user_id, str(new_case.notificationCaseId))

    absences = cps.get_absences(user_id)
    for absence in absences:
        logger.info("absence %s %s %s", absence.absenceId, absence.reason, absence.startDate)

    payment_preference = massgov.pfml.fineos.models.customer_api.NewPaymentPreference(
        description="Print Check",
        paymentMethod="Check",
        effectiveFrom=datetime.date(2020, 7, 16),
        isDefault=True,
        chequeDetails=massgov.pfml.fineos.models.customer_api.ChequeDetails(
            nameToPrintOnCheck="Michelle Jones2"
        ),
    )
    cps.add_payment_preference(user_id, payment_preference)


main()
