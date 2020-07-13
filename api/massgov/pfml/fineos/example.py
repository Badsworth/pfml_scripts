#
# Example of using the FINEOS client.
#

import datetime

import requests.packages.urllib3.connection

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
    cps = massgov.pfml.fineos.FINEOSClient(
        api_url="https://dt1-api.masspfml.fineos.com",
        wscomposer_url="https://dt1-claims-webapp.masspfml.fineos.com/wscomposer/",
        client_id="4gjtcl7d0rca0jleujea0veqrg",
        client_secret="1pnhkt07uc6it0tlpp93m3s8o8i1aab7js2ha44q72od7tmga6pk",
    )

    # Send some requests.
    healthy = cps.health_check("hackathon_91")
    logger.info("healthy %s", healthy)

    user_id = "example_91"
    employee_registration = massgov.pfml.fineos.models.EmployeeRegistration(
        user_id=user_id,
        customer_number=91,
        date_of_birth=datetime.date(1960, 1, 24),
        email="ville_j@mass.gov",
        employer_id=21,
        first_name="Jackson",
        last_name="Ville",
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
        description="Elec transfer test",
        paymentMethod="Elec Funds Transfer",
        accountDetails=massgov.pfml.fineos.models.customer_api.AccountDetails(
            accountName="Test",
            accountType="checking",
            accountNo="123456789",
            routingNumber="0456789",
        ),
    )
    cps.add_payment_preference(user_id, payment_preference)


main()
