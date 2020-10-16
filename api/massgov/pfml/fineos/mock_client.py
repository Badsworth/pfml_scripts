#
# FINEOS client - mock implementation.
#
# This implementation is intended for use in local development or in test cases. It may also be
# used in deployed environments when needed.
#

import datetime
import pathlib
import typing
from typing import List, Union

import faker
import requests

import massgov.pfml.util.logging

from . import client, exception, models

logger = massgov.pfml.util.logging.get_logger(__name__)

# Capture calls for unit testing.
_capture: typing.Optional[typing.List] = None


def fake_date_of_birth(fake):
    """Generate a fake date of birth in a reproducible way."""
    return fake.date_between(datetime.date(1930, 1, 1), datetime.date(2010, 1, 1))


def mock_document(
    absence_id: str,
    document_type: str = "ID Document",
    file_name: str = "test.png",
    description: str = "Mock File",
) -> dict:
    return {
        "caseId": absence_id,
        "rootCaseId": "NTN-111",
        "documentId": 3011,
        "name": document_type,
        "type": "Document",
        "fileExtension": pathlib.Path(file_name).suffix,
        "fileName": "26e82dd7-dbfc-4e7b-9804-ea955627253d.png",
        "originalFilename": file_name,
        "receivedDate": "2020-09-01",
        "effectiveFrom": "2020-09-02",
        "effectiveTo": "2020-09-03",
        "description": description,
        "title": "",
        "isRead": False,
        "createdBy": "Roberto Carlos",
        "dateCreated": "2020-09-01",
        "extensionAttributes": [],
    }


class MockFINEOSClient(client.AbstractFINEOSClient):
    """Mock FINEOS API client that returns fake responses."""

    def find_employer(self, employer_fein: str) -> str:
        _capture_call("find_employer", None, employer_fein=employer_fein)

        if employer_fein == "999999999":
            raise exception.FINEOSNotFound("Employer not found.")
        else:
            # TODO: Match the FINEOS employer id format
            return employer_fein + "1000"

    def register_api_user(self, employee_registration: models.EmployeeRegistration) -> None:
        _capture_call("register_api_user", None, employee_registration=employee_registration)

        if employee_registration.national_insurance_no == "999999999":
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

    def update_customer_details(self, user_id: str, customer: models.customer_api.Customer) -> None:
        _capture_call("update_customer_details", user_id, customer=customer)

    def start_absence(
        self, user_id: str, absence_case: models.customer_api.AbsenceCase
    ) -> models.customer_api.AbsenceCaseSummary:
        _capture_call("start_absence", user_id, absence_case=absence_case)

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
        _capture_call("complete_intake", user_id, notification_case_id=notification_case_id)

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

    def get_absence_occupations(
        self, user_id: str, absence_id: str
    ) -> List[models.customer_api.ReadCustomerOccupation]:
        _capture_call("get_absence_occupations", user_id, absence_id=absence_id)
        return [models.customer_api.ReadCustomerOccupation(occupationId=12345)]

    def add_payment_preference(
        self, user_id: str, payment_preference: models.customer_api.NewPaymentPreference
    ) -> models.customer_api.PaymentPreferenceResponse:
        return models.customer_api.PaymentPreferenceResponse(
            paymentMethod="Elec Funds Transfer", paymentPreferenceId="1201"
        )

    def upload_document(
        self,
        user_id: str,
        absence_id: str,
        document_type: str,
        file_content: bytes,
        file_name: str,
        content_type: str,
        description: str,
    ) -> models.customer_api.Document:
        document = mock_document(absence_id, document_type, file_name, description)
        return models.customer_api.Document.parse_obj(document)

    def get_documents(self, user_id: str, absence_id: str) -> List[models.customer_api.Document]:
        document = mock_document(absence_id)
        return [models.customer_api.Document.parse_obj(document)]

    def get_week_based_work_pattern(
        self, user_id: str, occupation_id: Union[str, int],
    ) -> models.customer_api.WeekBasedWorkPattern:
        _capture_call("get_week_based_work_pattern", user_id, occupation_id=occupation_id)
        return models.customer_api.WeekBasedWorkPattern(workPatternType="Fixed", workPatternDays=[])

    def add_week_based_work_pattern(
        self,
        user_id: str,
        occupation_id: Union[str, int],
        week_based_work_pattern: models.customer_api.WeekBasedWorkPattern,
    ) -> models.customer_api.WeekBasedWorkPattern:
        _capture_call(
            "add_week_based_work_pattern", user_id, week_based_work_pattern=week_based_work_pattern
        )

        if user_id == "USER_WITH_EXISTING_WORK_PATTERN":
            raise exception.FINEOSClientBadResponse(200, 403)
        else:
            return week_based_work_pattern

    def update_week_based_work_pattern(
        self,
        user_id: str,
        occupation_id: Union[str, int],
        week_based_work_pattern: models.customer_api.WeekBasedWorkPattern,
    ) -> models.customer_api.WeekBasedWorkPattern:
        _capture_call(
            "update_week_based_work_pattern",
            user_id,
            week_based_work_pattern=week_based_work_pattern,
        )
        return week_based_work_pattern

    def update_reflexive_questions(
        self,
        user_id: str,
        absence_id: typing.Optional[str],
        additional_information: models.customer_api.AdditionalInformation,
    ) -> None:
        _capture_call(
            "update_reflexive_questions",
            user_id,
            absence_id=absence_id,
            additional_information=additional_information,
        )


def start_capture():
    """Start capturing API calls made via MockFINEOSClient."""
    global _capture
    _capture = []


def _capture_call(method_name, user_id, **args):
    """Record the name and arguments of an API call."""
    global _capture
    if _capture is not None:
        _capture.append((method_name, user_id, args))


def get_capture():
    """Return the list of API calls captured since start_capture() was called."""
    global _capture
    return _capture
