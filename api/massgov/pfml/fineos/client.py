#
# FINEOS client - abstract base class.
#

import abc
import typing
from decimal import Decimal

from massgov.pfml.fineos.transforms.to_fineos.base import EFormBody

from . import models


class AbstractFINEOSClient(abc.ABC, metaclass=abc.ABCMeta):
    """Abstract base class for a FINEOS API client."""

    @abc.abstractmethod
    def read_employer(self, employer_fein: str) -> models.OCOrganisation:
        pass

    @abc.abstractmethod
    def find_employer(self, employer_fein: str) -> str:
        """Create the employee account registration."""
        pass

    @abc.abstractmethod
    def register_api_user(self, employee_registration: models.EmployeeRegistration) -> None:
        """Create the employee account registration."""
        pass

    @abc.abstractmethod
    def health_check(self, user_id: str) -> bool:
        """Health check API."""
        pass

    @abc.abstractmethod
    def read_customer_details(self, user_id: str) -> models.customer_api.Customer:
        """Read customer details."""
        pass

    @abc.abstractmethod
    def update_customer_details(self, user_id: str, customer: models.customer_api.Customer) -> None:
        """Update customer details."""
        pass

    @abc.abstractmethod
    def read_customer_contact_details(self, user_id: str) -> models.customer_api.ContactDetails:
        """Read customer contact details."""
        pass

    @abc.abstractmethod
    def update_customer_contact_details(
        self, user_id: str, contact_details: models.customer_api.ContactDetails
    ) -> models.customer_api.ContactDetails:
        """Update customer contact details."""
        pass

    @abc.abstractmethod
    def start_absence(
        self, user_id: str, absence_case: models.customer_api.AbsenceCase
    ) -> models.customer_api.AbsenceCaseSummary:
        pass

    @abc.abstractmethod
    def complete_intake(
        self, user_id: str, notification_case_id: str
    ) -> models.customer_api.NotificationCaseSummary:
        pass

    @abc.abstractmethod
    def get_absences(self, user_id: str) -> typing.List[models.customer_api.AbsenceCaseSummary]:
        pass

    @abc.abstractmethod
    def get_absence(self, user_id: str, absence_id: str) -> models.customer_api.AbsenceDetails:
        pass

    @abc.abstractmethod
    def get_absence_period_decisions(
        self, user_id: str, absence_id: str
    ) -> models.group_client_api.PeriodDecisions:
        pass

    @abc.abstractmethod
    def get_customer_info(
        self, user_id: str, customer_id: str
    ) -> models.group_client_api.CustomerInfo:
        pass

    @abc.abstractmethod
    def get_customer_occupations(
        self, user_id: str, customer_id: str
    ) -> models.group_client_api.CustomerOccupations:
        pass

    @abc.abstractmethod
    def get_outstanding_information(
        self, user_id: str, case_id: str
    ) -> typing.List[models.group_client_api.OutstandingInformationItem]:
        """Get outstanding information"""
        pass

    @abc.abstractmethod
    def update_outstanding_information_as_received(
        self,
        user_id: str,
        case_id: str,
        outstanding_information: models.group_client_api.OutstandingInformationData,
    ) -> None:
        """Update outstanding information received"""
        pass

    @abc.abstractmethod
    def get_eform_summary(
        self, user_id: str, absence_id: str
    ) -> typing.List[models.group_client_api.EFormSummary]:
        pass

    @abc.abstractmethod
    def get_eform(
        self, user_id: str, absence_id: str, eform_id: str
    ) -> models.group_client_api.EForm:
        pass

    def create_eform(self, user_id: str, absence_id: str, eform: EFormBody) -> None:
        pass

    def customer_create_eform(self, user_id: str, absence_id: str, eform: EFormBody) -> None:
        pass

    @abc.abstractmethod
    def get_case_occupations(
        self, user_id: str, case_id: str
    ) -> typing.List[models.customer_api.ReadCustomerOccupation]:
        pass

    @abc.abstractmethod
    def add_payment_preference(
        self, user_id: str, payment_preference: models.customer_api.NewPaymentPreference
    ) -> models.customer_api.PaymentPreferenceResponse:
        pass

    @abc.abstractmethod
    def update_occupation(
        self,
        occupation_id: int,
        employment_status: typing.Optional[str],
        hours_worked_per_week: typing.Optional[Decimal],
        NAICS_occupation: typing.Optional[str],
        job_title: typing.Optional[str],
    ) -> None:
        pass

    @abc.abstractmethod
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
        pass

    @abc.abstractmethod
    def group_client_get_documents(
        self, user_id: str, absence_id: str
    ) -> typing.List[models.group_client_api.GroupClientDocument]:
        pass

    @abc.abstractmethod
    def get_managed_requirements(
        self, user_id: str, absence_id: str
    ) -> typing.List[models.group_client_api.ManagedRequirementDetails]:
        pass

    @abc.abstractmethod
    def get_documents(
        self, user_id: str, absence_id: str
    ) -> typing.List[models.customer_api.Document]:
        pass

    @abc.abstractmethod
    def download_document_as_leave_admin(
        self, user_id: str, absence_id: str, fineos_document_id: str
    ) -> models.group_client_api.Base64EncodedFileData:
        pass

    @abc.abstractmethod
    def download_document(
        self, user_id: str, absence_id: str, fineos_document_id: str
    ) -> models.customer_api.Base64EncodedFileData:
        pass

    @abc.abstractmethod
    def mark_document_as_received(
        self, user_id: str, absence_id: str, fineos_document_id: str
    ) -> None:
        pass

    @abc.abstractmethod
    def get_week_based_work_pattern(
        self, user_id: str, occupation_id: typing.Union[str, int],
    ) -> models.customer_api.WeekBasedWorkPattern:
        pass

    @abc.abstractmethod
    def add_week_based_work_pattern(
        self,
        user_id: str,
        occupation_id: typing.Union[str, int],
        week_based_work_pattern: models.customer_api.WeekBasedWorkPattern,
    ) -> models.customer_api.WeekBasedWorkPattern:
        pass

    @abc.abstractmethod
    def update_week_based_work_pattern(
        self,
        user_id: str,
        occupation_id: typing.Union[str, int],
        week_based_work_pattern: models.customer_api.WeekBasedWorkPattern,
    ) -> models.customer_api.WeekBasedWorkPattern:
        pass

    @abc.abstractmethod
    def update_reflexive_questions(
        self,
        user_id: str,
        absence_id: typing.Optional[str],
        additional_information: models.customer_api.AdditionalInformation,
    ) -> None:
        pass

    @abc.abstractmethod
    def create_or_update_employer(
        self,
        employer_creation: models.CreateOrUpdateEmployer,
        existing_organization: typing.Optional[models.OCOrganisationItem] = None,
    ) -> typing.Tuple[str, int]:
        """Create or update an employer in FINEOS."""
        pass

    @abc.abstractmethod
    def create_or_update_leave_admin(
        self, leave_admin_create_or_update: models.CreateOrUpdateLeaveAdmin
    ) -> None:
        """Create or update a leave admin in FINEOS."""
        pass

    def create_service_agreement_for_employer(
        self,
        fineos_employer_id: int,
        service_agreement_inputs: models.CreateOrUpdateServiceAgreement,
    ) -> str:
        """Create Service Agreement For An Employer in FINEOS"""
        pass
