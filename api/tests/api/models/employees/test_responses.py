from massgov.pfml.api.models.employees.responses import EmployeeForPfmlCrmResponse, EmployeeResponse
from massgov.pfml.db.models.factories import EmployeeFactory
from tests.helpers.api_responses import assert_structural_subset


def test_response_structural_subset(initialize_factories_session):
    employee = EmployeeFactory.create()
    service_now_response = EmployeeForPfmlCrmResponse.from_orm(employee).dict()
    full_response = EmployeeResponse.from_orm(employee).dict()

    assert_structural_subset(service_now_response, full_response)
