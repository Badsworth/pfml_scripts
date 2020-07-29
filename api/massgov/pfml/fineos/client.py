#
# FINEOS client - abstract base class.
#

import abc
import typing

from . import models


class AbstractFINEOSClient(abc.ABC, metaclass=abc.ABCMeta):
    """Abstract base class for a FINEOS API client."""

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
    def add_payment_preference(
        self, user_id: str, payment_preference: models.customer_api.NewPaymentPreference
    ) -> models.customer_api.PaymentPreferenceResponse:
        pass
