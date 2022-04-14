from massgov.pfml.api.models.employees.responses import EmployeeForPfmlCrmResponse, EmployeeResponse
from massgov.pfml.db.models.factories import (
    ApplicationFactory,
    ClaimFactory,
    EmployeeFactory,
    TaxIdentifierFactory,
)
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


def test_employee_mass_id(initialize_factories_session):

    claim_one = ClaimFactory.create(
        is_id_proofed=True, employee_id="4376896b-596c-4c86-a653-1915cf997a84"
    )
    application_one = ApplicationFactory.create(claim=claim_one, mass_id="123456789")

    employee_one = EmployeeFactory.create(
        claims=[claim_one], employee_id="4376896b-596c-4c86-a653-1915cf997a84"
    )
    employee_two = EmployeeFactory.create(
        mass_id_number="111222333", out_of_state_id_number="444555666"
    )

    claim_two = ClaimFactory.create(employee=employee_two)

    ApplicationFactory.create(claim=claim_two, mass_id="555555555")

    service_now_response_one = EmployeeForPfmlCrmResponse.from_orm(employee_one).dict()
    full_response_one = EmployeeResponse.from_orm(employee_one).dict()

    service_now_response_two = EmployeeForPfmlCrmResponse.from_orm(employee_two).dict()
    full_response_two = EmployeeResponse.from_orm(employee_two).dict()

    assert service_now_response_one["mass_id_number"] == application_one.mass_id
    assert full_response_one["mass_id_number"] == application_one.mass_id

    assert service_now_response_two["mass_id_number"] == "111222333"
    assert full_response_two["mass_id_number"] == "111222333"
