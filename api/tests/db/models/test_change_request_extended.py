import datetime

import pytest

from massgov.pfml.db.models.change_request_extended import ChangeRequest
from massgov.pfml.db.models.employees import ChangeRequestType, LkChangeRequestType


class TestToFineosModel:
    # Run `initialize_factories_session` for all tests,
    # so that it doesn't need to be manually included
    @pytest.fixture(autouse=True)
    def setup_factories(self, initialize_factories_session):
        return

    @pytest.fixture
    def claim(self, claim):
        claim.absence_period_start_date = datetime.date(2022, 1, 1)
        claim.absence_period_end_date = datetime.date(2022, 1, 10)

        return claim

    @pytest.fixture
    def change_request(self, claim):
        return ChangeRequest(
            claim_id=claim.claim_id,
            claim=claim,
            change_request_type_instance=ChangeRequestType.MODIFICATION,
        )

    def test_withdrawn(self, change_request):
        change_request.change_request_type_instance = ChangeRequestType.WITHDRAWAL

        fineos_change_request = change_request.to_fineos_model()

        assert fineos_change_request.reason.name == "Employee Requested Removal"
        assert fineos_change_request.additionalNotes == "Withdrawal"

        change_request_period = fineos_change_request.changeRequestPeriods[0]
        assert change_request_period.startDate == datetime.date(2022, 1, 1)
        assert change_request_period.endDate == datetime.date(2022, 1, 10)

    def test_medical_to_bonding(self, change_request):
        change_request.change_request_type_instance = ChangeRequestType.MEDICAL_TO_BONDING
        change_request.start_date = datetime.date(2022, 2, 2)
        change_request.end_date = datetime.date(2022, 2, 12)

        fineos_change_request = change_request.to_fineos_model()

        assert fineos_change_request.reason.name == "Add time for different Absence Reason"
        assert fineos_change_request.additionalNotes == "Medical to bonding transition"

        change_request_period = fineos_change_request.changeRequestPeriods[0]
        assert change_request_period.startDate == datetime.date(2022, 2, 2)
        assert change_request_period.endDate == datetime.date(2022, 2, 12)

    def test_extension(self, change_request):
        change_request.start_date = datetime.date(2022, 2, 2)
        change_request.end_date = datetime.date(2022, 2, 12)

        fineos_change_request = change_request.to_fineos_model()

        assert fineos_change_request.reason.name == "Add time for identical Absence Reason"
        assert fineos_change_request.additionalNotes == "Extension"

        change_request_period = fineos_change_request.changeRequestPeriods[0]
        assert change_request_period.startDate == datetime.date(2022, 2, 2)
        assert change_request_period.endDate == datetime.date(2022, 2, 12)

    def test_cancellation(self, change_request):
        change_request.start_date = datetime.date(2022, 1, 1)
        change_request.end_date = datetime.date(2022, 1, 5)

        fineos_change_request = change_request.to_fineos_model()

        assert fineos_change_request.reason.name == "Employee Requested Removal"
        assert fineos_change_request.additionalNotes == "Cancellation"

        change_request_period = fineos_change_request.changeRequestPeriods[0]
        assert change_request_period.startDate == datetime.date(2022, 1, 6)
        assert change_request_period.endDate == datetime.date(2022, 1, 10)

    def test_unknown_type(self, change_request):
        change_request.change_request_type_instance = LkChangeRequestType(123, "Foo")

        with pytest.raises(ValueError) as exc_info:
            change_request.to_fineos_model()

        error = exc_info.value
        assert "Unknown type: Foo" in str(error)
