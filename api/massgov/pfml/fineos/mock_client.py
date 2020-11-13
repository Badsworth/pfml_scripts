#
# FINEOS client - mock implementation.
#
# This implementation is intended for use in local development or in test cases. It may also be
# used in deployed environments when needed.
#

import base64
import copy
import datetime
import pathlib
import typing
from typing import List, Union

import faker
import requests

import massgov.pfml.util.logging

from . import client, exception, fineos_client, models

logger = massgov.pfml.util.logging.get_logger(__name__)

# Capture calls for unit testing.
_capture: typing.Optional[typing.List] = None

MOCK_DOCUMENT_DATA = {
    "caseId": "",
    "rootCaseId": "NTN-111",
    "documentId": 3011,
    "name": "",
    "type": "Document",
    "fileExtension": "",
    "fileName": "26e82dd7-dbfc-4e7b-9804-ea955627253d.png",
    "originalFilename": "",
    "receivedDate": "2020-09-01",
    "effectiveFrom": "2020-09-02",
    "effectiveTo": "2020-09-03",
    "description": "",
    "title": "",
    "isRead": False,
    "createdBy": "Roberto Carlos",
    "extensionAttributes": [],
}

TEST_IMAGE_FILE_PATH = pathlib.Path(__file__).parent / "mock_files" / "test.png"


def fake_date_of_birth(fake):
    """Generate a fake date of birth in a reproducible way."""
    return fake.date_between(datetime.date(1930, 1, 1), datetime.date(2010, 1, 1))


def mock_document(
    absence_id: str,
    document_type: str = "Approval Notice",
    file_name: str = "test.pdf",
    description: str = "Mock File",
) -> dict:
    mocked_document = copy.copy(MOCK_DOCUMENT_DATA)
    mocked_document.update(
        {
            "caseId": absence_id,
            "name": document_type,
            "fileExtension": pathlib.Path(file_name).suffix,
            "originalFilename": file_name,
            "description": description,
        }
    )

    return mocked_document


def mock_absence_periods():
    return {
        "startDate": "2021-06-24",
        "endDate": "2021-10-28",
        "decisions": [
            {
                "absence": {"id": "NTN-61-ABS-01", "caseReference": "NTN-61-ABS-01"},
                "employee": {"id": "1079", "name": "ZZ: Olaf Aufderhar"},
                "period": {
                    "periodReference": "PL-14449-0000000152",
                    "parentPeriodReference": "",
                    "relatedToEpisodic": "false",
                    "startDate": "2021-06-24",
                    "endDate": "2021-06-25",
                    "balanceDeduction": 0.4,
                    "timeRequested": "16:00",
                    "timeDeducted": "16:00",
                    "timeDeductedBasis": "Hours",
                    "timeDecisionStatus": "Approved",
                    "timeDecisionReason": "Leave Request Approved",
                    "type": "Time off period",
                    "status": "Known",
                    "leavePlan": {
                        "id": "abdc368f-ace6-4d6a-b697-f1016fe8a314",
                        "name": "MA PFML - Employee",
                        "shortName": "MA PFML - Employee",
                        "applicabilityStatus": "Applicable",
                        "eligibilityStatus": "Met",
                        "availabilityStatus": "Approved",
                        "adjudicationStatus": "Accepted",
                        "evidenceStatus": "Satisfied",
                        "category": "Paid",
                        "calculationPeriodMethod": "Rolling Forward - Sunday",
                        "timeBankMethod": "Length / Duration",
                        "timeWithinPeriod": 52,
                        "timeWithinPeriodBasis": "Weeks",
                        "fixedYearStartDay": 0,
                        "fixedYearStartMonth": "Please Select",
                        "timeEntitlement": 20,
                        "timeEntitlementBasis": "Weeks",
                        "paidLeaveCaseId": "PL ABS-542",
                    },
                    "leaveRequest": {
                        "id": "PL-14432-0000000137",
                        "reasonName": "Serious Health Condition - Employee",
                        "qualifier1": "Not Work Related",
                        "qualifier2": "Sickness",
                        "decisionStatus": "Approved",
                        "approvalReason": "Fully Approved",
                        "denialReason": "Please Select",
                    },
                },
            },
            {
                "absence": {"id": "NTN-61-ABS-01", "caseReference": "NTN-61-ABS-01"},
                "employee": {"id": "1079", "name": "ZZ: Olaf Aufderhar"},
                "period": {
                    "periodReference": "PL-14449-0000000152",
                    "parentPeriodReference": "",
                    "relatedToEpisodic": "false",
                    "startDate": "2021-06-26",
                    "endDate": "2021-06-27",
                    "balanceDeduction": 0,
                    "timeRequested": "",
                    "timeDeducted": "",
                    "timeDeductedBasis": "",
                    "timeDecisionStatus": "",
                    "timeDecisionReason": "",
                    "type": "Time off period",
                    "status": "Known",
                    "leavePlan": {
                        "id": "abdc368f-ace6-4d6a-b697-f1016fe8a314",
                        "name": "MA PFML - Employee",
                        "shortName": "MA PFML - Employee",
                        "applicabilityStatus": "Applicable",
                        "eligibilityStatus": "Met",
                        "availabilityStatus": "Approved",
                        "adjudicationStatus": "Accepted",
                        "evidenceStatus": "Satisfied",
                        "category": "Paid",
                        "calculationPeriodMethod": "Rolling Forward - Sunday",
                        "timeBankMethod": "Length / Duration",
                        "timeWithinPeriod": 52,
                        "timeWithinPeriodBasis": "Weeks",
                        "fixedYearStartDay": 0,
                        "fixedYearStartMonth": "Please Select",
                        "timeEntitlement": 20,
                        "timeEntitlementBasis": "Weeks",
                        "paidLeaveCaseId": "PL ABS-542",
                    },
                    "leaveRequest": {
                        "id": "PL-14432-0000000137",
                        "reasonName": "Serious Health Condition - Employee",
                        "qualifier1": "Not Work Related",
                        "qualifier2": "Sickness",
                        "decisionStatus": "Approved",
                        "approvalReason": "Fully Approved",
                        "denialReason": "Please Select",
                    },
                },
            },
        ],
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

    def get_absence_period_decisions(
        self, user_id: str, absence_id: str
    ) -> models.group_client_api.PeriodDecisions:
        return models.group_client_api.PeriodDecisions.parse_obj(mock_absence_periods())

    def get_customer_info(
        self, user_id: str, customer_id: str
    ) -> models.group_client_api.CustomerInfo:
        return models.group_client_api.CustomerInfo()

    def get_eform_summary(
        self, user_id: str, absence_id: str
    ) -> List[models.group_client_api.EFormSummary]:
        return [
            models.group_client_api.EFormSummary(
                eformId=12345, eformType="Mocked Other Leave EForm"
            )
        ]

    def get_eform(
        self, user_id: str, absence_id: str, eform_id: str
    ) -> models.group_client_api.EForm:
        return models.group_client_api.EForm(eformId=12345)

    def get_case_occupations(
        self, user_id: str, case_id: str
    ) -> List[models.customer_api.ReadCustomerOccupation]:
        _capture_call("get_case_occupations", user_id, case_id=case_id)
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
        return [
            models.customer_api.Document.parse_obj(
                fineos_client.fineos_document_empty_dates_to_none(document)
            )
        ]

    def group_client_get_documents(
        self, user_id: str, absence_id: str
    ) -> List[models.group_client_api.GroupClientDocument]:
        document = mock_document(absence_id)
        return [
            models.group_client_api.GroupClientDocument.parse_obj(
                fineos_client.fineos_document_empty_dates_to_none(document)
            )
        ]

    def download_document(
        self, user_id: str, absence_id: str, fineos_document_id: str
    ) -> models.customer_api.Base64EncodedFileData:
        file_bytes = open(str(TEST_IMAGE_FILE_PATH), "rb").read()
        encoded_file_contents_str = base64.b64encode(file_bytes).decode("ascii")

        return models.customer_api.Base64EncodedFileData.parse_obj(
            {
                "fileName": "test.pdf",
                "fileExtension": "pdf",
                "contentType": "application/pdf",
                "base64EncodedFileContents": encoded_file_contents_str,
                "fileSizeInBytes": len(file_bytes),
            }
        )

    def mark_document_as_received(
        self, user_id: str, absence_id: str, fineos_document_id: str
    ) -> None:
        _capture_call(
            "mark_document_as_received",
            user_id,
            absence_id=absence_id,
            fineos_document_id=fineos_document_id,
        )

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

    def create_or_update_employer(
        self, employer_create_or_update: models.CreateOrUpdateEmployer
    ) -> typing.Tuple[str, int]:
        _capture_call(
            "create_or_update_employer", None, employer_create_or_update=employer_create_or_update
        )

        if employer_create_or_update.employer_fein == "999999999":
            raise exception.FINEOSClientError(
                Exception(
                    "Employer not created. Response Code: 422, "
                    "Party alias pfml_api_21ecb120-9a9a-4f8d-968d-e710b120e148 for alias "
                    "type Unknown already exists for customer 2569"
                )
            )

        return employer_create_or_update.fineos_customer_nbr, 250

    def create_or_update_leave_admin(
        self, leave_admin_create_or_update: models.CreateOrUpdateLeaveAdmin
    ) -> None:
        _capture_call("create_or_update_leave_admin", None)

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

    def create_service_agreement_for_employer(
        self, fineos_employee_id: int, leave_plans: str
    ) -> str:
        _capture_call(
            "create_service_agreement_for_employer", None, fineos_employee_id=fineos_employee_id
        )

        return "SA-123"


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
