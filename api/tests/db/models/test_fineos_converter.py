import pytest

from massgov.pfml.db.models.employees import ChangeRequest, ChangeRequestType


class TestToFineosModel:
    # Run `initialize_factories_session` for all tests,
    # so that it doesn't need to be manually included
    @pytest.fixture(autouse=True)
    def setup_factories(self, initialize_factories_session):
        return

    @pytest.fixture
    def change_request(self, claim):
        return ChangeRequest(
            claim_id=claim.claim_id,
            claim=claim,
            change_request_type_instance=ChangeRequestType.WITHDRAWAL,
        )

    def test_success(self, change_request):
        fineos_model = change_request.to_fineos_model()
        assert True
