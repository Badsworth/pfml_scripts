from massgov.pfml.api.models.employees.responses import EmployeeForPfmlCrmResponse, EmployeeResponse
from massgov.pfml.db.models.factories import EmployeeFactory, TaxIdentifierFactory
from tests.helpers.api_responses import assert_structural_subset


def test_response_structural_subset(initialize_factories_session):
    employee = EmployeeFactory.create()

    service_now_response = EmployeeForPfmlCrmResponse.from_orm(employee).dict()
    full_response = EmployeeResponse.from_orm(employee).dict()

    assert_structural_subset(service_now_response, full_response)


def test_tax_identifier_last_4(initialize_factories_session):
    tax_identifier = TaxIdentifierFactory.create(tax_identifier="587777091")
    employee_1 = EmployeeFactory.create(tax_identifier=tax_identifier)
    employee_2 = EmployeeFactory.create(tax_identifier_id=None, tax_identifier=None)

    service_now_response_1 = EmployeeForPfmlCrmResponse.from_orm(employee_1).dict()
    full_response_1 = EmployeeResponse.from_orm(employee_1).dict()

    service_now_response_2 = EmployeeForPfmlCrmResponse.from_orm(employee_2).dict()
    full_response_2 = EmployeeResponse.from_orm(employee_2).dict()

    assert service_now_response_1["tax_identifier"] == "587-77-7091"
    assert full_response_1["tax_identifier"] == "587-77-7091"
    assert service_now_response_1["tax_identifier_last4"] == tax_identifier.tax_identifier_last4
    assert full_response_1["tax_identifier_last4"] == tax_identifier.tax_identifier_last4

    assert service_now_response_2["tax_identifier"] is None
    assert full_response_2["tax_identifier"] is None
    assert service_now_response_2["tax_identifier_last4"] is None
    assert full_response_2["tax_identifier_last4"] is None
