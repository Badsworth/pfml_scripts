#
# FINEOS client - mock implementation.
#
# This implementation is intended for use in local development or in test cases. It may also be
# used in deployed environments when needed.
#

import datetime
import typing

import faker
import requests

import massgov.pfml.util.logging

from . import client, exception, models

logger = massgov.pfml.util.logging.get_logger(__name__)


def fake_date_of_birth(fake):
    """Generate a fake date of birth in a reproducible way."""
    return fake.date_between(datetime.date(1930, 1, 1), datetime.date(2010, 1, 1))


class MockFINEOSClient(client.AbstractFINEOSClient):
    """Mock FINEOS API client that returns fake responses."""

    def find_employer(self, employer_fein: int) -> str:
        if employer_fein == 999999999:
            raise exception.FINEOSNotFound("Employer not found.")
        else:
            return "15"

    def register_api_user(self, employee_registration: models.EmployeeRegistration) -> None:
        if employee_registration.national_insurance_no == 999999999:
            raise exception.FINEOSClientBadResponse(requests.codes.ok, 400)
        else:
            pass

    def health_check(self, user_id: str) -> bool:
        return True

    def read_customer_details(self, user_id: str) -> models.customer_api.Customer:
        fake = faker.Faker()
        fake.seed_instance(user_id)
        date_of_birth = fake_date_of_birth(fake)
        first_name = fake.first_name()
        last_name = fake.last_name()
        return models.customer_api.Customer(
            dateOfBirth=date_of_birth, firstName=first_name, lastName=last_name
        )

    def start_absence(
        self, user_id: str, absence_case: models.customer_api.AbsenceCase
    ) -> models.customer_api.AbsenceCaseSummary:
        absence_case_summary = models.customer_api.AbsenceCaseSummary(
            absenceId="NTN-259-ABS-01", notificationCaseId="NTN-259"
        )
        logger.info(
            "mock: %r %r => %r %r",
            user_id,
            absence_case.additionalComments,
            absence_case_summary.absenceId,
            absence_case_summary.notificationCaseId,
        )
        return absence_case_summary

    def complete_intake(
        self, user_id: str, notification_case_id: str
    ) -> models.customer_api.NotificationCaseSummary:
        notification_case_summary = models.customer_api.NotificationCaseSummary(
            notificationCaseId=notification_case_id
        )
        logger.info(
            "mock: %r %r => %r",
            user_id,
            notification_case_id,
            notification_case_summary.notificationCaseId,
        )
        return notification_case_summary

    def get_absences(self, user_id: str) -> typing.List[models.customer_api.AbsenceCaseSummary]:
        return [models.customer_api.AbsenceCaseSummary()]

    def get_absence(self, user_id: str, absence_id: str) -> models.customer_api.AbsenceDetails:
        return models.customer_api.AbsenceDetails()

    def add_payment_preference(
        self, user_id: str, payment_preference: models.customer_api.NewPaymentPreference
    ) -> models.customer_api.PaymentPreferenceResponse:
        return models.customer_api.PaymentPreferenceResponse(
            paymentMethod="Elec Funds Transfer", paymentPreferenceId="1201"
        )
