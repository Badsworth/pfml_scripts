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
from decimal import Decimal
from typing import Any, Iterable, List, Optional, Tuple, Union

import faker
import requests
from requests.models import Response

import massgov.pfml.util.logging
import massgov.pfml.util.logging.wrapper
from massgov.pfml.fineos.transforms.to_fineos.base import EFormBody

from ..db.models.applications import PhoneType
from . import client, exception, fineos_client, models
from .mock.eform import MOCK_CUSTOMER_EFORMS, MOCK_EFORMS
from .mock.field import fake_customer_no
from .models.customer_api import ChangeRequestPeriod
from .models.customer_api import EForm as CustomerEForm
from .models.group_client_api import EForm

logger = massgov.pfml.util.logging.get_logger(__name__)

# Capture calls for unit testing.
_capture: Optional[List] = None

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
            "fileExtension": pathlib.Path(file_name).suffix.lower(),
            "originalFilename": file_name,
            "description": description,
        }
    )

    return mocked_document


def mock_absence_periods(absence_id: str) -> Any:
    employee_id = "1000" if absence_id == "int_fake_hours_worked_per_week" else "1079"
    type = "Time off period" if absence_id == "NTN-100-ABS-01" else "Reduced Schedule"
    return {
        "startDate": "2021-06-24",
        "endDate": "2021-10-28",
        "decisions": [
            {
                "absence": {"id": absence_id, "caseReference": absence_id},
                "employee": {"id": employee_id, "name": "ZZ: Olaf Aufderhar"},
                "period": {
                    "periodReference": "PL-14449-0000000152",
                    "parentPeriodReference": "",
                    "relatedToEpisodic": "false",
                    "startDate": "2021-06-24",
                    "endDate": "2021-06-25",
                    "balanceDeduction": 0,
                    "timeRequested": "",
                    "timeDeducted": "",
                    "timeDeductedBasis": "Hours",
                    "timeDecisionStatus": "Approved",
                    "timeDecisionReason": "Leave Request Approved",
                    "type": type,
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


def mock_customer_info():
    # The FINEOS response includes more fields than this,
    # but I've only included what is currently relevant to us
    return {
        "firstName": "Bud",
        "lastName": "Baxter",
        "secondName": "",
        "initials": "",
        "dateOfBirth": "1970-12-25",
        "idNumber": "123121234",
        "address": {
            "premiseNo": "",
            "addressLine1": "55 Trinity Ave.",
            "addressLine2": "Suite 3450",
            "addressLine3": "",
            "addressLine4": "Atlanta",
            "addressLine5": "",
            "addressLine6": "GA",
            "addressLine7": "",
            "postCode": "30303",
            "country": {"name": "USA", "domainName": "Country", "domainId": 1, "fullId": 2},
            "extensions": {
                "ConsenttoShareData": True,
                "Confirmed": True,
                "MassachusettsID": "",
                "OutOfStateID": "",
            },
        },
    }


def mock_customer_details():
    # Similar to mock_customer_info, The FINEOS response includes more fields than this
    return {
        "firstName": "Samantha",
        "lastName": "Jorgenson",
        "secondName": "",
        "initials": "",
        "dateOfBirth": "1996-01-11",
        "idNumber": "123121232",
        "gender": "Neutral",
        "customerAddress": {
            "address": {
                "addressLine1": "37 Mather Drive",
                "addressLine2": "#22",
                "addressLine3": "",
                "addressLine4": "Amherst",
                "addressLine5": "",
                "addressLine6": "MA",
                "addressLine7": "",
                "postCode": "01003",
                "country": "USA",
            }
        },
        "classExtensionInformation": [
            {"name": "MassachusettsID", "stringValue": "123456789"},
            {"name": "OutOfStateID", "stringValue": "123"},
        ],
    }


def mock_customer_contact_details():
    # Mocks FINEOS response for customer contact details
    # This includes all the FINEOS fields from this endpoint
    return {
        "phoneNumbers": [
            {
                "id": 0,
                "preferred": False,
                "phoneNumberType": "Cell",
                "intCode": "1",
                "areaCode": "123",
                "telephoneNo": "4567890",
            },
            {
                "id": 1,
                "preferred": True,
                "phoneNumberType": "Cell",
                "intCode": "1",
                "areaCode": "321",
                "telephoneNo": "4567890",
            },
        ],
        "emailAddresses": [
            {"id": 0, "preferred": False, "emailAddress": "testemail1@test.com"},
            {"id": 1, "preferred": True, "emailAddress": "testemail2@test.com"},
        ],
        "preferredContactMethod": 1,
    }


def mock_managed_requirements():
    return [
        {
            "managedReqId": 123,
            "category": "Employer Confirmation",
            "type": "Employer Confirmation of Leave Data",
            "followUpDate": datetime.date(2021, 2, 1),
            "documentReceived": True,
            "creator": "Fake Creator",
            "status": "Open",
            "subjectPartyName": "Fake Name",
            "sourceOfInfoPartyName": "Fake Sourcee",
            "creationDate": datetime.date(2020, 1, 1),
            "dateSuppressed": datetime.date(2020, 3, 1),
        },
        {
            "managedReqId": 124,
            "category": "Employer Confirmation",
            "type": "Employer Confirmation of Leave Data",
            "followUpDate": datetime.date(2021, 2, 1),
            "documentReceived": True,
            "creator": "Fake Creator",
            "status": "Complete",
            "subjectPartyName": "Fake Name",
            "sourceOfInfoPartyName": "Fake Sourcee",
            "creationDate": datetime.date(2020, 1, 1),
            "dateSuppressed": datetime.date(2020, 3, 1),
        },
    ]


def mock_managed_requirements_parsed():
    return [
        models.group_client_api.ManagedRequirementDetails.parse_obj(r)
        for r in mock_managed_requirements()
    ]


class MockFINEOSClient(client.AbstractFINEOSClient):
    """Mock FINEOS API client that returns fake responses."""

    def __init__(
        self,
        mock_eforms: Iterable[EForm] = MOCK_EFORMS,
        mock_customer_eforms: Iterable[CustomerEForm] = MOCK_CUSTOMER_EFORMS,
    ):
        self.mock_eforms = mock_eforms
        self.mock_eform_map = {eform.eformId: eform for eform in mock_eforms}
        self.mock_customer_eforms = mock_customer_eforms
        self.mock_customer_eform_map = {eform.eformId: eform for eform in mock_customer_eforms}

    def read_employer(self, employer_fein: str) -> models.OCOrganisation:
        _capture_call("read_employer", None, employer_fein=employer_fein)

        if employer_fein == "999999999":
            raise exception.FINEOSEntityNotFound("Employer not found.")

        organisationUnits = None
        if employer_fein == "999999998":
            organisationUnits = models.OCOrganisationUnit(
                OrganisationUnit=[
                    models.OCOrganisationUnitItem(OID="PE:00001:0000000001", Name="OrgUnitOne"),
                    models.OCOrganisationUnitItem(OID="PE:00001:0000000002", Name="OrgUnitTwo"),
                ]
            )

        if employer_fein == "999999997":
            organisationUnits = models.OCOrganisationUnit(
                OrganisationUnit=[
                    models.OCOrganisationUnitItem(OID="PE:00002:0000000001", Name="OrgUnitThree"),
                    models.OCOrganisationUnitItem(OID="PE:00002:0000000002", Name="OrgUnitFour"),
                ]
            )

        return models.OCOrganisation(
            OCOrganisation=[
                models.OCOrganisationItem(
                    CustomerNo=str(fake_customer_no(employer_fein)),
                    CorporateTaxNumber=employer_fein,
                    Name="Foo",
                    organisationUnits=organisationUnits,
                )
            ]
        )

    def find_employer(self, employer_fein: str) -> str:
        _capture_call("find_employer", None, employer_fein=employer_fein)

        if employer_fein == "999999999":
            raise exception.FINEOSEntityNotFound("Employer not found.")
        else:
            return str(fake_customer_no(employer_fein))

    def register_api_user(self, employee_registration: models.EmployeeRegistration) -> None:
        _capture_call("register_api_user", None, employee_registration=employee_registration)

        if employee_registration.national_insurance_no == "999999999":
            raise exception.FINEOSClientBadResponse("register_api_user", requests.codes.ok, 400)
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

    def read_customer_contact_details(self, user_id: str) -> models.customer_api.ContactDetails:
        _capture_call("update_customer_contact_details", user_id)

        return models.customer_api.ContactDetails(
            phoneNumbers=[
                models.customer_api.PhoneNumber(
                    id=1,
                    intCode="1",
                    areaCode="321",
                    telephoneNo="4567890",
                    phoneNumberType=PhoneType.PHONE.phone_type_description,
                )
            ]
        )

    def update_customer_contact_details(
        self, user_id: str, contact_details: models.customer_api.ContactDetails
    ) -> models.customer_api.ContactDetails:
        _capture_call("update_customer_contact_details", user_id, contact_details=contact_details)

        if contact_details.phoneNumbers is not None and len(contact_details.phoneNumbers) > 0:
            if contact_details.phoneNumbers[0].id is None:
                contact_details.phoneNumbers[0].id = 1

        return contact_details

    def start_absence(
        self, user_id: str, absence_case: models.customer_api.AbsenceCase
    ) -> models.customer_api.AbsenceCaseSummary:
        call_count = (
            len([capture for capture in get_capture() if capture[0] == "start_absence"])
            if get_capture()
            else 0
        )
        _capture_call("start_absence", user_id, absence_case=absence_case)
        fineos_case_id_number = 259 + call_count

        start_date = None
        end_date = None

        if absence_case.timeOffLeavePeriods:
            start_date = absence_case.timeOffLeavePeriods[0].startDate
            end_date = absence_case.timeOffLeavePeriods[0].endDate
        elif absence_case.reducedScheduleLeavePeriods:
            start_date = absence_case.reducedScheduleLeavePeriods[0].startDate
            end_date = absence_case.reducedScheduleLeavePeriods[0].endDate
        elif absence_case.episodicLeavePeriods:
            start_date = absence_case.episodicLeavePeriods[0].startDate
            end_date = absence_case.episodicLeavePeriods[0].endDate

        absence_case_summary = models.customer_api.AbsenceCaseSummary(
            absenceId=f"NTN-{fineos_case_id_number}-ABS-01",
            notificationCaseId=f"NTN-{fineos_case_id_number}",
            startDate=start_date,
            endDate=end_date,
        )
        return absence_case_summary

    def complete_intake(
        self, user_id: str, notification_case_id: str
    ) -> models.customer_api.NotificationCaseSummary:
        _capture_call("complete_intake", user_id, notification_case_id=notification_case_id)

        notification_case_summary = models.customer_api.NotificationCaseSummary(
            notificationCaseId=notification_case_id
        )
        return notification_case_summary

    def get_absences(self, user_id: str) -> List[models.customer_api.AbsenceCaseSummary]:
        return [models.customer_api.AbsenceCaseSummary()]

    def get_absence(self, user_id: str, absence_id: str) -> models.customer_api.AbsenceDetails:
        if absence_id == "NTN-304363-ABS-01":
            absence_details = models.customer_api.AbsenceDetails()
            absence_details.absenceId = "NTN-304363-ABS-01"
            absence_period = models.customer_api.AbsencePeriod()
            absence_period.id = "PL-14449-0000002237"
            absence_period.absenceType = "Continuous"
            absence_period.reason = "Child Bonding"
            absence_period.reasonQualifier1 = "Foster Care"
            absence_period.reasonQualifier2 = ""
            absence_period.startDate = datetime.date(2021, 1, 29)
            absence_period.endDate = datetime.date(2021, 1, 30)
            absence_period.requestStatus = "Pending"

            absence_details.absencePeriods = [absence_period]
            return absence_details
        else:
            return models.customer_api.AbsenceDetails()

    def get_absence_period_decisions(
        self, user_id: str, absence_id: str
    ) -> models.group_client_api.PeriodDecisions:
        _capture_call("get_absence_period_decisions", user_id, absence_id=absence_id)
        absence_periods = mock_absence_periods(absence_id)
        return models.group_client_api.PeriodDecisions.parse_obj(absence_periods)

    def get_customer_info(
        self, user_id: str, customer_id: str
    ) -> models.group_client_api.CustomerInfo:
        return models.group_client_api.CustomerInfo.parse_obj(mock_customer_info())

    def get_customer_occupations_customer_api(
        self, user_id: str, customer_id: str
    ) -> List[models.customer_api.ReadCustomerOccupation]:
        _capture_call("get_customer_occupations_customer_api", user_id, customer_id=customer_id)

        hrsWorkedPerWeek = 37 if customer_id == "1000" else 37.5
        return [
            models.customer_api.ReadCustomerOccupation(
                occupationId=12345,
                hoursWorkedPerWeek=hrsWorkedPerWeek,
                workPatternBasis="Unknown",
                employmentStatus="Active",
            )
        ]

    def get_customer_occupations(
        self, user_id: str, customer_id: str
    ) -> models.group_client_api.CustomerOccupations:
        _capture_call("get_customer_occupations", user_id, customer_id=customer_id)

        hrsWorkedPerWeek = 37 if customer_id == "1000" else 37.5
        return models.group_client_api.CustomerOccupations(
            elements=[
                models.group_client_api.CustomerOccupation(
                    id="12345", hrsWorkedPerWeek=str(hrsWorkedPerWeek)
                )
            ]
        )

    def get_outstanding_information(
        self, user_id: str, case_id: str
    ) -> List[models.group_client_api.OutstandingInformationItem]:
        """Get outstanding information"""
        _capture_call("get_outstanding_information", user_id, case_id=case_id)

        if case_id == "NTN-CASE-WITHOUT-OUTSTANDING-INFO":
            return []

        return [
            models.group_client_api.OutstandingInformationItem(
                informationType="Employer Confirmation of Leave Data", infoReceived=False
            )
        ]

    def update_outstanding_information_as_received(
        self,
        user_id: str,
        case_id: str,
        outstanding_information: models.group_client_api.OutstandingInformationData,
    ) -> None:
        """Update outstanding information received"""
        _capture_call(
            "update_outstanding_information_as_received",
            user_id,
            outstanding_information=outstanding_information,
            case_id=case_id,
        )

    def get_eform_summary(
        self, user_id: str, absence_id: str
    ) -> List[models.group_client_api.EFormSummary]:
        _capture_call("get_eform_summary", user_id, absence_id=absence_id)
        results = []

        for eform in self.mock_eforms:
            if eform.eformType:
                results.append(
                    models.group_client_api.EFormSummary(
                        eformId=eform.eformId,
                        eformTypeId="PE-11212-%010i" % eform.eformId,
                        effectiveDateFrom=None,
                        effectiveDateTo=None,
                        eformType=eform.eformType,
                    )
                )

        return results

    def customer_get_eform_summary(
        self, user_id: str, absence_id: str
    ) -> List[models.customer_api.EFormSummary]:
        _capture_call("customer_get_eform_summary", user_id, absence_id=absence_id)
        results = []

        for eform in self.mock_customer_eforms:
            if eform.eformType:
                results.append(
                    models.customer_api.EFormSummary(
                        eformId=eform.eformId,
                        eformTypeId="PE-11212-%010i" % eform.eformId,
                        effectiveDateFrom=None,
                        effectiveDateTo=None,
                        eformType=eform.eformType,
                    )
                )

        return results

    def get_eform(
        self, user_id: str, absence_id: str, eform_id: int
    ) -> models.group_client_api.EForm:
        _capture_call("get_eform", user_id, absence_id=absence_id, eform_id=eform_id)
        if eform_id in self.mock_eform_map:
            return self.mock_eform_map[eform_id]
        raise exception.FINEOSForbidden("get_eform", 200, 403, "Permission denied")

    def customer_get_eform(
        self, user_id: str, absence_id: str, eform_id: int
    ) -> models.customer_api.EForm:
        _capture_call("customer_get_eform", user_id, absence_id=absence_id, eform_id=eform_id)
        if eform_id in self.mock_customer_eform_map:
            return self.mock_customer_eform_map[eform_id]
        raise exception.FINEOSForbidden("get_eform", 200, 403, "Permission denied")

    def create_eform(self, user_id: str, absence_id: str, eform: EFormBody) -> None:
        _capture_call("create_eform", user_id, eform=eform, absence_id=absence_id)

    def customer_create_eform(self, user_id: str, absence_id: str, eform: EFormBody) -> None:
        _capture_call("customer_create_eform", user_id, eform=eform, absence_id=absence_id)

    def get_case_occupations(
        self, user_id: str, case_id: str
    ) -> List[models.customer_api.ReadCustomerOccupation]:
        _capture_call("get_case_occupations", user_id, case_id=case_id)
        return [models.customer_api.ReadCustomerOccupation(occupationId=12345)]

    def get_payment_preferences(
        self, user_id: str
    ) -> List[models.customer_api.PaymentPreferenceResponse]:
        _capture_call("get_payment_preferences", user_id)
        return [
            models.customer_api.PaymentPreferenceResponse(
                paymentMethod="Elec Funds Transfer",
                paymentPreferenceId="85622",
                isDefault=True,
                accountDetails=models.customer_api.AccountDetails(
                    accountNo="1234565555",
                    accountName="Constance Griffin",
                    routingNumber="011222333",
                    accountType="Checking",
                ),
                chequeDetails=models.customer_api.ChequeDetails(
                    nameToPrintOnCheck="Connie Griffin"
                ),
                customerAddress=models.customer_api.CustomerAddress(
                    address=models.customer_api.Address(
                        addressLine1="44324 Nayeli Stream",
                        addressLine2="",
                        addressLine3="",
                        addressLine4="New Monserrateberg",
                        addressLine5="",
                        addressLine6="IN",
                        addressLine7="",
                        postCode="22516-6101",
                        country="USA",
                    )
                ),
            )
        ]

    def add_payment_preference(
        self, user_id: str, payment_preference: models.customer_api.NewPaymentPreference
    ) -> models.customer_api.PaymentPreferenceResponse:
        _capture_call(
            "add_payment_preference", user_id=user_id, payment_preference=payment_preference
        )
        return models.customer_api.PaymentPreferenceResponse(
            paymentMethod=payment_preference.paymentMethod,
            paymentPreferenceId="1201",
            accountDetails=payment_preference.accountDetails,
            chequeDetails=payment_preference.chequeDetails,
        )

    def update_occupation(
        self,
        occupation_id: int,
        employment_status: Optional[str],
        hours_worked_per_week: Optional[Decimal],
        fineos_org_unit_id: Optional[str],
        worksite_id: Optional[str],
    ) -> None:
        _capture_call(
            "update_occupation",
            None,
            employment_status=employment_status,
            hours_worked_per_week=hours_worked_per_week,
            occupation_id=occupation_id,
            fineos_org_unit_id=fineos_org_unit_id,
            worksite_id=worksite_id,
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
        _capture_call(
            "upload_document",
            user_id,
            absence_id=absence_id,
            document_type=document_type,
            file_content=file_content,
            file_name=file_name,
            content_type=content_type,
            description=description,
        )

        document = mock_document(absence_id, document_type, file_name, description)
        return models.customer_api.Document.parse_obj(document)

    def upload_document_multipart(
        self,
        user_id: str,
        absence_id: str,
        document_type: str,
        file_content: bytes,
        file_name: str,
        content_type: str,
        description: str,
    ) -> models.customer_api.Document:
        _capture_call(
            "upload_document_multipart",
            user_id,
            absence_id=absence_id,
            document_type=document_type,
            file_content=file_content,
            file_name=file_name,
            content_type=content_type,
            description=description,
        )

        document = mock_document(absence_id, document_type, file_name, description)
        return models.customer_api.Document.parse_obj(document)

    def get_documents(self, user_id: str, absence_id: str) -> List[models.customer_api.Document]:
        document = mock_document(absence_id)
        return [
            models.customer_api.Document.parse_obj(
                fineos_client.fineos_document_empty_dates_to_none(document)
            )
        ]

    def get_managed_requirements(
        self, user_id: str, absence_id: str
    ) -> List[models.group_client_api.ManagedRequirementDetails]:
        return mock_managed_requirements_parsed()

    def group_client_get_documents(
        self, user_id: str, absence_id: str
    ) -> List[models.group_client_api.GroupClientDocument]:
        # TODO: (API-1812) - deprecate magic string ( no longer used )
        # special case for testing all downloadable document types:
        if absence_id == "leave_admin_mixed_allowable_doc_types":
            # This should mirror the DOWNLOADABLE_DOC_TYPES in fineos/common.py
            DOWNLOADABLE_DOC_TYPES = [
                "state managed paid leave confirmation",
                "approval notice",
                "request for more information",
                "denial notice",
                "employer response additional documentation",
                "care for a family member form",
                "own serious health condition form",
                "pregnancy/maternity form",
                "child bonding evidence form",
                "military exigency form",
                "pending application withdrawn",
                "appeal acknowledgment",
                "maximum weekly benefit change notice",
                "benefit amount change notice",
                "leave allotment change notice",
                "approved time cancelled",
                "change request approved",
                "change request denied",
            ]

            allowed_documents = [
                mock_document(absence_id, document_type=document_type)
                for document_type in DOWNLOADABLE_DOC_TYPES
            ]
            disallowed_documents = [
                mock_document(absence_id, document_type="Identification Proof"),
                mock_document(absence_id, document_type="Disallowed Doc Type"),
            ]

            return [
                models.group_client_api.GroupClientDocument.parse_obj(
                    fineos_client.fineos_document_empty_dates_to_none(document)
                )
                for document in allowed_documents + disallowed_documents
            ]

        if absence_id == "leave_admin_allowable_doc_type":
            document = mock_document(absence_id)
        else:
            document = mock_document(absence_id, document_type="Disallowed Doc Type")
        return [
            models.group_client_api.GroupClientDocument.parse_obj(
                fineos_client.fineos_document_empty_dates_to_none(document)
            )
        ]

    def download_document_as_leave_admin(
        self, user_id: str, absence_id: str, fineos_document_id: str
    ) -> models.group_client_api.Base64EncodedFileData:
        file_bytes = open(str(TEST_IMAGE_FILE_PATH), "rb").read()
        encoded_file_contents_str = base64.b64encode(file_bytes).decode("ascii")

        return models.group_client_api.Base64EncodedFileData.parse_obj(
            {
                "fileName": "test.pdf",
                "fileExtension": "pdf",
                "contentType": "application/pdf",
                "base64EncodedFileContents": encoded_file_contents_str,
                "fileSizeInBytes": len(file_bytes),
            }
        )

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
        self, user_id: str, occupation_id: Union[str, int]
    ) -> models.customer_api.WeekBasedWorkPattern:
        _capture_call("get_week_based_work_pattern", user_id, occupation_id=occupation_id)
        return models.customer_api.WeekBasedWorkPattern(
            workPatternType="Fixed",
            workPatternDays=[
                models.customer_api.WorkPatternDay(
                    dayOfWeek="Monday", weekNumber=12, hours=4, minutes=5
                )
            ],
        )

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
            raise exception.FINEOSForbidden("add_week_based_work_pattern", 200, 403)
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
        self,
        employer_create_or_update: models.CreateOrUpdateEmployer,
        existing_organization: Optional[models.OCOrganisationItem] = None,
    ) -> Tuple[str, int]:
        _capture_call(
            "create_or_update_employer",
            None,
            employer_create_or_update=employer_create_or_update,
            existing_organization=existing_organization,
        )

        if employer_create_or_update.employer_fein == "999999999":
            raise exception.FINEOSFatalResponseError(
                "create_or_update_employer",
                Exception(
                    "Employer not created. Response Code: 422, "
                    "Party alias pfml_api_21ecb120-9a9a-4f8d-968d-e710b120e148 for alias "
                    "type Unknown already exists for customer 2569"
                ),
            )

        return (
            employer_create_or_update.fineos_customer_nbr,
            fake_customer_no(employer_create_or_update.employer_fein),
        )

    def create_or_update_leave_period_change_request(
        self,
        fineos_web_id: str,
        absence_id: str,
        change_request: models.customer_api.CreateLeavePeriodsChangeRequestCommand,
    ) -> models.customer_api.LeavePeriodsChangeRequestResource:
        _capture_call(
            "create_or_update_leave_period_change_request",
            fineos_web_id,
            absence_id=absence_id,
            additional_information=change_request,
        )
        return models.customer_api.LeavePeriodsChangeRequestResource(
            reason=models.customer_api.ReasonResponse(
                fullId=0, name="Employee Requested Removal", domainId=0, domainName="Foo", _links={}  # type: ignore
            ),
            changeRequestPeriods=[
                ChangeRequestPeriod(
                    startDate=datetime.date(2022, 2, 14), endDate=datetime.date(2022, 2, 15)
                )
            ],
            additionalNotes="Withdrawal",
        )

    def create_or_update_leave_admin(
        self, leave_admin_create_or_update: models.CreateOrUpdateLeaveAdmin
    ) -> Tuple[Optional[str], Optional[str]]:
        _capture_call("create_or_update_leave_admin", None)
        return "", ""

    def update_reflexive_questions(
        self,
        user_id: str,
        absence_id: Optional[str],
        additional_information: models.customer_api.AdditionalInformation,
    ) -> None:
        _capture_call(
            "update_reflexive_questions",
            user_id,
            absence_id=absence_id,
            additional_information=additional_information,
        )

    def create_service_agreement_for_employer(
        self,
        fineos_employee_id: int,
        service_agreement_inputs: models.CreateOrUpdateServiceAgreement,
    ) -> str:
        _capture_call(
            "create_service_agreement_for_employer", None, fineos_employee_id=fineos_employee_id
        )

        return "SA-123"

    def send_tax_withholding_preference(self, absence_id: str, is_withholding_tax: bool) -> None:
        _capture_call(
            "send_tax_withholding_preference",
            None,
            absence_id=absence_id,
            is_withholding_tax=is_withholding_tax,
        )

    def upload_document_to_dms(self, file_name: str, file: bytes, data: Any) -> Response:
        _capture_call("upload_document_to_dms", None)

        response = Response()
        return response


massgov.pfml.util.logging.wrapper.log_all_method_calls(MockFINEOSClient, logger)


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
