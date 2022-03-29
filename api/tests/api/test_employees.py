from datetime import date

import pytest

import tests.api
from massgov.pfml.api.models.applications.common import MaskedAddress
from massgov.pfml.db.models.employees import EmployeeAddress
from massgov.pfml.db.models.factories import (
    AddressFactory,
    ApplicationFactory,
    ClaimFactory,
    EmployeeFactory,
    EmployerFactory,
    TaxIdentifierFactory,
)


@pytest.fixture
def employee():
    employee = EmployeeFactory.create()
    return employee


@pytest.fixture
def employee_different_fineos_name():
    employee = EmployeeFactory.create(
        first_name="Foo",
        last_name="Bar",
        middle_name="Baz",
        fineos_employee_first_name="Foo2",
        fineos_employee_last_name="Bar2",
        fineos_employee_middle_name="Baz2",
    )
    return employee


def test_employees_get_snow_user_allowed(client, employee, snow_user_headers):
    response = client.get(
        "/v1/employees/{}".format(employee.employee_id), headers=snow_user_headers
    )

    assert response.status_code == 200


def test_employees_get_e164_phone_number(client, employee, snow_user_headers):
    response = client.get(
        "/v1/employees/{}".format(employee.employee_id), headers=snow_user_headers
    )
    response_data = response.get_json().get("data")

    assert response_data["phone_numbers"][0]["e164"] == employee.phone_number
    assert response.status_code == 200


def test_employees_get_snow_user_requires_agent_id(client, employee, snow_user_token):
    # requires header {"Mass-PFML-Agent-ID": "123"}
    response = client.get(
        "/v1/employees/{}".format(employee.employee_id),
        headers={"Authorization": "Bearer {}".format(snow_user_token)},
    )

    assert response.status_code == 401


def test_employess_get_invalid_employee(client, employee, snow_user_headers):
    response = client.get(
        "/v1/employees/{}".format("9e243bae-3b1e-43a4-aafe-aca3c6517cf0"), headers=snow_user_headers
    )
    tests.api.validate_error_response(response, 404)


def test_employees_get_nonsnow_forbidden(client, employee, consented_user_token):
    response = client.get(
        "/v1/employees/{}".format(employee.employee_id),
        headers={"Authorization": "Bearer {}".format(consented_user_token)},
    )

    assert response.status_code == 403


def test_employees_get_nonsnow_with_agent_header_also_forbidden(
    client, employee, consented_user_token
):
    response = client.get(
        "/v1/employees/{}".format(employee.employee_id),
        headers={
            "Authorization": "Bearer {}".format(consented_user_token),
            "Mass-PFML-Agent-ID": "123",
        },
    )

    assert response.status_code == 403


def test_employees_get_fineos_user_forbidden(client, employee, fineos_user_token):
    # Fineos role cannot access this endpoint
    response = client.get(
        "/v1/employees/{}".format(employee.employee_id),
        headers={
            "Authorization": "Bearer {}".format(fineos_user_token),
            # Agent ID header only required for SNOW users but including here to verify it doesn't cause unexpected
            # behavior
            "Mass-PFML-Agent-ID": "123",
        },
    )

    assert response.status_code == 403


def test_employees_search_nonsnow_forbidden(client, consented_user_token):
    employee = EmployeeFactory.create(
        first_name="John", last_name="Smith", email_address="test@example.com"
    )
    terms = {"first_name": employee.first_name, "last_name": employee.last_name}
    body = {"terms": terms}
    response = client.post(
        "/v1/employees/search",
        json=body,
        headers={
            "Authorization": "Bearer {}".format(consented_user_token),
            "Mass-PFML-Agent-ID": "123",
        },
    )
    assert response.status_code == 403


def test_employees_search_snow_allowed_with_default_values(client, snow_user_headers):
    employee = EmployeeFactory.create(
        first_name="John", last_name="Smith", email_address="test@example.com"
    )

    EmployeeFactory.create(
        first_name=employee.first_name, last_name="Black", email_address="test@example.com"
    )
    EmployeeFactory.create(
        first_name="Black", last_name=employee.last_name, email_address="test@example.com"
    )
    terms = {"first_name": employee.first_name, "last_name": employee.last_name}
    body = {"terms": terms}
    response = client.post("/v1/employees/search", json=body, headers=snow_user_headers)

    assert_employee_search_response_data(response, [employee])

    data = response.get_json()
    assert_employee_search_response_paging_data(data)


def test_employees_search_snow_allowed(client, snow_user_headers):
    employee = EmployeeFactory.create(
        first_name="John", last_name="Smith", email_address="test@example.com"
    )

    EmployeeFactory.create(
        first_name=employee.first_name, last_name="Black", email_address="example@example.com"
    )
    EmployeeFactory.create(
        first_name="Mark", last_name=employee.last_name, email_address="example@example.com"
    )
    employee_2 = EmployeeFactory.create(
        first_name=employee.first_name,
        last_name=employee.last_name,
        email_address="example@example.com",
    )
    terms = {"first_name": employee.first_name, "last_name": employee.last_name}
    order = {"by": "created_at", "direction": "ascending"}
    paging = {"offset": 1, "size": 5}

    body = {"terms": terms, "order": order, "paging": paging}
    response = client.post("/v1/employees/search", json=body, headers=snow_user_headers)

    assert_employee_search_response_data(response, [employee, employee_2])

    data = response.get_json()
    paging = dict(order=order, paging=paging)
    assert_employee_search_response_paging_data(data, paging)


def test_employees_search_name_requirement(client, snow_user_headers):
    employee = EmployeeFactory.create(
        first_name="John", last_name="Smith", email_address="test@example.com"
    )

    terms_1 = {"first_name": employee.first_name}
    body_1 = {"terms": terms_1}
    terms_2 = {"last_name": employee.last_name}
    body_2 = {"terms": terms_2}
    terms_3 = {"email_address": "ac"}
    body_3 = {"terms": terms_3}
    terms_4 = {"first_name": "a", "last_name": "_"}
    body_4 = {"terms": terms_4}

    response_1 = client.post("/v1/employees/search", json=body_1, headers=snow_user_headers)
    response_2 = client.post("/v1/employees/search", json=body_2, headers=snow_user_headers)
    response_3 = client.post("/v1/employees/search", json=body_3, headers=snow_user_headers)
    response_4 = client.post("/v1/employees/search", json=body_4, headers=snow_user_headers)

    assert response_1.status_code == 400
    assert response_2.status_code == 400
    assert response_3.status_code == 400
    assert response_4.status_code == 400


def test_employees_search_nonexisting_employee(client, snow_user_headers):
    EmployeeFactory.create(first_name="Jar", last_name="binks", email_address="test@example.com")
    terms = {"first_name": "JarJar", "last_name": "Binks"}
    body = {"terms": terms}
    response = client.post("/v1/employees/search", json=body, headers=snow_user_headers)

    assert_employee_search_response_data(response, [])

    data = response.get_json()
    assert_employee_search_response_paging_data(data)


def test_employees_search_wildcard_rejects_invalid(client, snow_user_headers):
    employee_1 = EmployeeFactory(
        first_name="Bob", last_name="Black", email_address="test@example.com"
    )
    EmployeeFactory(
        first_name="Bobby", last_name=employee_1.last_name, email_address="example@example.com"
    )

    terms = {"first_name": "!@%*", "last_name": employee_1.last_name}

    response = client.post("/v1/employees/search", json={"terms": terms}, headers=snow_user_headers)

    assert response.status_code == 400
    response_body = response.get_json()
    assert "Must contain at least 1 alphanumeric character." in str(response_body)

    terms = {"email_address": "_@-.ab"}
    response = client.post("/v1/employees/search", json={"terms": terms}, headers=snow_user_headers)

    assert response.status_code == 400
    response_body = response.get_json()

    assert "Must contain at least 3 alphanumeric characters." in str(response_body)


def test_employees_search_wildcard_name(client, snow_user_headers):
    employee_1 = EmployeeFactory(
        first_name="Bob", last_name="Smith", email_address="test@example.com"
    )
    employee_2 = EmployeeFactory(
        first_name="Bobby", last_name=employee_1.last_name, email_address="example@example.com"
    )
    # different first name, same last name
    EmployeeFactory(first_name="Jane", last_name=employee_1.last_name)
    # different first and last name
    EmployeeFactory(first_name="Joe")

    terms = {"first_name": "Bob", "last_name": employee_1.last_name}

    response = client.post("/v1/employees/search", json={"terms": terms}, headers=snow_user_headers)

    assert_employee_search_response_data(response, [employee_1, employee_2])

    data = response.get_json()
    assert_employee_search_response_paging_data(data)


def test_employees_search_with_phone_number(client, snow_user_headers):
    employee_1 = EmployeeFactory(
        first_name="Bob",
        last_name="Smith",
        email_address="test@example.com",
        cell_phone_number="+12247052345",
    )
    EmployeeFactory(
        first_name=employee_1.first_name, last_name="Black", email_address="example@example.com"
    )
    terms = {"phone_number": employee_1.cell_phone_number}

    response = client.post("/v1/employees/search", json={"terms": terms}, headers=snow_user_headers)

    assert_employee_search_response_data(response, [employee_1])
    data = response.get_json()

    # assert cell phone comes back with the correct type
    cell_phone = data["data"][0]["phone_numbers"][1]
    assert cell_phone["phone_number"] == "224-705-2345"
    assert cell_phone["phone_type"] == "Cell"

    assert_employee_search_response_paging_data(data)


def test_employees_search_with_fineos_customer_number(client, snow_user_headers):
    employee_1 = EmployeeFactory(
        first_name="Bob",
        last_name="Smith",
        email_address="test@example.com",
        fineos_customer_number="111111",
    )
    EmployeeFactory(
        first_name=employee_1.first_name, last_name="Black", email_address="example@example.com"
    )
    terms = {"fineos_customer_number": employee_1.fineos_customer_number}

    response = client.post("/v1/employees/search", json={"terms": terms}, headers=snow_user_headers)

    assert_employee_search_response_data(response, [employee_1])

    data = response.get_json()
    assert_employee_search_response_paging_data(data)


def test_employees_search_with_email_address(client, snow_user_headers):
    employee_1 = EmployeeFactory(
        first_name="Will", last_name="Witten", email_address="test@example.com"
    )
    EmployeeFactory(
        first_name=employee_1.first_name, last_name="Smith", email_address="example@example.com"
    )
    terms = {"email_address": employee_1.email_address}

    response = client.post("/v1/employees/search", json={"terms": terms}, headers=snow_user_headers)

    assert_employee_search_response_data(response, [employee_1])

    data = response.get_json()
    assert_employee_search_response_paging_data(data)


def test_employees_search(client, snow_user_headers):
    employee_1 = EmployeeFactory(
        first_name="will",
        last_name="smith",
        email_address="test@example.com",
        cell_phone_number="+12247052345",
    )
    employee_2 = EmployeeFactory(
        fineos_employee_first_name="Will",
        fineos_employee_last_name="Smith",
        first_name="john",
        last_name="doe",
        email_address="example@example.com",
        cell_phone_number="+12247052345",
    )
    employee_3 = EmployeeFactory(
        fineos_employee_last_name="smith",
        first_name="Will",
        last_name="doe",
        email_address="test@example.com",
        phone_number="+12247052345",
    )
    EmployeeFactory(
        fineos_employee_last_name="O'Keefe",
        first_name="Kennedy",
        last_name="O'Keefe",
        email_address="kennedy@okeefe.com",
        phone_number="+12247052346",
    )
    EmployeeFactory(
        first_name="Will",
        last_name="Farrel",
        email_address="mars@example.com",
    )

    terms = {"first_name": "will", "last_name": "Smith", "phone_number": "+12247052345"}
    order = {"by": "created_at", "direction": "descending"}
    paging = {"size": 5}

    body = {"terms": terms, "order": order, "paging": paging}

    response = client.post("/v1/employees/search", json=body, headers=snow_user_headers)

    assert_employee_search_response_data(response, [employee_1, employee_2, employee_3])

    data = response.get_json()
    paging = dict(order=order, paging=paging)
    assert_employee_search_response_paging_data(data, paging)

    terms_special_chars = {"first_name": "Kennedy", "last_name": "O'Keefe"}
    body_special_chars = {"terms": terms_special_chars, "order": order, "paging": paging}

    response_special_chars = client.post(
        "/v1/employees/search", json=body_special_chars, headers=snow_user_headers
    )
    data = response_special_chars.get_json()

    assert response_special_chars.status_code == 200

    data = response_special_chars.get_json()["data"]
    assert len(data) == 1
    assert data[0]["last_name"] == "O'Keefe"


def test_get_employee_basic_response(client, employee_different_fineos_name, snow_user_headers):
    response = client.get(
        f"/v1/employees/{employee_different_fineos_name.employee_id}", headers=snow_user_headers
    )

    assert response.status_code == 200
    response_body = response.get_json()

    employee_data = response_body.get("data")

    assert employee_data["first_name"] == "Foo2"
    assert employee_data["middle_name"] == "Baz2"
    assert employee_data["last_name"] == "Bar2"
    assert employee_data["tax_identifier"] is not None
    assert employee_data["tax_identifier_last4"] is not None


def test_employee_for_pfml_crm_response(client, employee, snow_user_headers, user, test_db_session):
    tax_identifier = TaxIdentifierFactory.create(tax_identifier="587777091")
    employee = EmployeeFactory.create(
        tax_identifier=tax_identifier,
        first_name="Foo",
        last_name="Bar",
        middle_name="Baz",
        date_of_birth=date(2020, 1, 1),
        fineos_employee_first_name="Foo2",
        fineos_employee_last_name="Bar2",
        fineos_employee_middle_name="Baz2",
    )

    address = AddressFactory.create()
    employee.employee_addresses = [
        EmployeeAddress(employee_id=employee.employee_id, address_id=address.address_id)
    ]

    test_db_session.commit()

    ApplicationFactory.create(user=user)
    test_db_session.commit()

    response = client.get(f"/v1/employees/{employee.employee_id}", headers=snow_user_headers)

    assert response.status_code == 200
    response_body = response.get_json()

    employee_data = response_body.get("data")
    assert employee_data["date_of_birth"] == "****-01-01"
    assert employee_data["addresses"][0] == MaskedAddress.from_orm(address)
    assert employee_data["tax_identifier"] == "587-77-7091"
    assert employee_data["tax_identifier_last4"] == tax_identifier.tax_identifier_last4
    assert employee_data["email_address"] is not None
    assert len(employee_data["phone_numbers"]) == 1


def test_employee_with_claims_no_id_proof(
    client, employee, snow_user_headers, user, test_db_session
):
    employer = EmployerFactory.create()
    employee = EmployeeFactory.create()

    claim = ClaimFactory.create(employer=employer, employee=employee)

    ApplicationFactory.create(user=user, claim=claim, mass_id="123456789")
    test_db_session.commit()

    response = client.get(f"/v1/employees/{employee.employee_id}", headers=snow_user_headers)

    assert response.status_code == 200
    response_body = response.get_json()

    employee_data = response_body.get("data")
    assert employee_data["mass_id_number"] is None


def test_employee_empty_mass_id(client, employee, snow_user_headers, user, test_db_session):
    employee = EmployeeFactory.create()
    ApplicationFactory.create(user=user)
    test_db_session.commit()

    response = client.get(f"/v1/employees/{employee.employee_id}", headers=snow_user_headers)

    assert response.status_code == 200
    response_body = response.get_json()

    employee_data = response_body.get("data")
    assert employee_data["mass_id_number"] is None


def test_employee_get_mass_id(client, employee, snow_user_headers, user, test_db_session):
    employer = EmployerFactory.create()
    employee = EmployeeFactory.create()

    claim = ClaimFactory.create(
        employer=employer, employee=employee, is_id_proofed=True, created_at=date(2020, 1, 1)
    )

    claim2 = ClaimFactory.create(
        employer=employer,
        employee=employee,
        fineos_absence_status_id=1,
        claim_type_id=1,
        is_id_proofed=True,
        created_at=date(2021, 2, 1),
        fineos_absence_id="NTN-304363-ABS-02",
    )
    ApplicationFactory.create(user=user, claim=claim, mass_id="123456789")
    ApplicationFactory.create(user=user, claim=claim2, mass_id="012345678")
    test_db_session.commit()

    response = client.get(f"/v1/employees/{employee.employee_id}", headers=snow_user_headers)

    assert response.status_code == 200
    response_body = response.get_json()

    employee_data = response_body.get("data")
    assert employee_data["mass_id_number"] == "012345678"


def test_employee_auth_get(disable_employee_endpoint, client, employee, consented_user_token):
    # This tests a user that doesn't meet authorization rules. Should return 403

    response = client.get(
        "/v1/employees/{}".format(employee.employee_id),
        headers={"Authorization": "Bearer {}".format(consented_user_token)},
    )

    tests.api.validate_error_response(response, 403)


def assert_employee_search_response_data(response, expected_employees):
    assert response.status_code == 200

    data = response.get_json()["data"]
    assert len(data) == len(expected_employees)

    expected_employee_ids = {str(e.employee_id) for e in expected_employees}
    for employee_response in data:
        assert employee_response["employee_id"] in expected_employee_ids


def assert_employee_search_response_paging_data(search_response, paging=None):
    def deep_get(item, dictionary=paging):
        if paging is None:
            return None
        for k, v in dictionary.items():
            if k == item:
                return v
            if isinstance(v, dict) and item in v.keys():
                return v[item]
        return None

    by = deep_get("by")
    direction = deep_get("direction")
    offset = deep_get("offset")
    size = deep_get("size")

    data = search_response["meta"]["paging"]

    assert data["order_by"] == "created_at" if by is None else by
    assert data["order_direction"] == "descending" if direction is None else direction
    assert data["page_offset"] == 1 if offset is None else offset
    assert data["page_size"] == 25 if size is None else size
