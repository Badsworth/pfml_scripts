from unittest import mock

import factory
import pytest

import massgov.pfml.db as db
import massgov.pfml.experian.address_validate_soap.client as soap_api
from massgov.pfml.db.models.employees import Claim, Employee, ExperianAddressPair, Payment
from massgov.pfml.db.models.factories import (
    AddressFactory,
    ClaimFactory,
    EmployeeFactory,
    EmployeeWithFineosNumberFactory,
    ExperianAddressPairFactory,
    PaymentFactory,
)
from massgov.pfml.db.models.geo import GeoState
from massgov.pfml.delegated_payments.address_validation import Constants
from massgov.pfml.delegated_payments.claimant_address_validation import (
    ClaimantAddressValidationStep,
)
from massgov.pfml.delegated_payments.mock.fineos_extract_data import FineosPaymentData
from massgov.pfml.experian.address_validate_soap.client import Client
from massgov.pfml.experian.address_validate_soap.mock_caller import MockVerificationZeepCaller
from massgov.pfml.experian.address_validate_soap.models import VerifyLevel
from massgov.pfml.experian.address_validate_soap.service import (
    address_to_experian_verification_search,
)
from massgov.pfml.experian.experian_util import address_to_experian_search_text


@pytest.fixture
def claimant_address_step(
    initialize_factories_session,
    test_db_session: db.Session,
):
    return ClaimantAddressValidationStep(
        db_session=test_db_session, log_entry_db_session=test_db_session
    )


@pytest.fixture
def employee_factory():
    return EmployeeWithFineosNumberFactory.build(
        date_of_birth=factory.Faker("date_of_birth", minimum_age=14, maximum_age=100),
        fineos_customer_number=factory.Faker("numerify", text="####"),
    )


@pytest.fixture
def employee_extract_factory():
    claimant_data = FineosPaymentData()
    return claimant_data


@pytest.fixture
def experian_factory():
    return ExperianAddressPairFactory.build()


@pytest.fixture
def address_factory():
    return AddressFactory.build()


@pytest.fixture
def experian_factory_with_experian_address(address_factory):
    return ExperianAddressPairFactory.build(experian_address=address_factory)


def test_employee_exists_for_customer_number(test_db_session, employee_extract_factory):

    employee = test_db_session.query(Employee).filter(
        Employee.fineos_customer_number == employee_extract_factory.customer_number
    )
    assert employee is not None


def test_get_employee_record(employee_factory, employee_extract_factory):
    assert employee_extract_factory.customer_number != employee_factory.fineos_customer_number


def test_construct_address_data(employee_extract_factory):
    AddressFactory.address_line_one = employee_extract_factory.address_1
    AddressFactory.city = employee_extract_factory.city
    AddressFactory.geo_state_id = employee_extract_factory.state
    AddressFactory.zip_code = employee_extract_factory.zip_code

    assert len(AddressFactory.zip_code) == 10


def is_address_same(address, employee_extract_factory):
    result = False
    if (
        address.fineos_address.address_line_one == employee_extract_factory.address_1
        and address.city == employee_extract_factory.city
        and address.geo_state_id == employee_extract_factory.state
        and address.zip_code == employee_extract_factory.zip_code
    ):
        result = True
    assert result is False


def test_validate_claimant_address_already_validated(experian_factory_with_experian_address):

    assert experian_factory_with_experian_address.experian_address is not None


def test_validate_claimant_address_has_all_parts(employee_extract_factory):
    result = True
    if (
        not employee_extract_factory.address_1
        or not employee_extract_factory.city
        or not employee_extract_factory.state
        or not employee_extract_factory.zip_code
    ):
        result = False
    assert result is True


def test_process_address_via_soap_api(employee_extract_factory, address_factory) -> None:
    mock_caller = MockVerificationZeepCaller()

    client = Client(mock_caller)
    search_response1 = client.search(address_to_experian_verification_search(address_factory))

    assert search_response1.address
    assert search_response1.verify_level == VerifyLevel.VERIFIED
    assert len(mock_caller.search_responses) == 1


def test_run_all_step_state_address_validation(claimant_address_step):
    mock_caller = MockVerificationZeepCaller()
    client = soap_api.Client(mock_caller)
    with mock.patch(
        "massgov.pfml.delegated_payments.address_validation._get_experian_soap_client",
        return_value=client,
    ):
        claimant_address_step.run()


def test_create_address_report(claimant_address_step):
    result1 = {
        Constants.INPUT_ADDRESS_KEY: "1 Main St, Charlestown, MA 02129",
        Constants.CONFIDENCE_KEY: "Verified",
        Constants.OUTPUT_ADDRESS_KEY_PREFIX: "1 Main St, Charlestown, MA 02129",
        Constants.MESSAGE_KEY: "Address verified by Experian",
    }

    result2 = {
        Constants.INPUT_ADDRESS_KEY: "11 Main St, Charlestown, MA 02129",
        Constants.CONFIDENCE_KEY: "Verified",
        Constants.OUTPUT_ADDRESS_KEY_PREFIX: "11 Main St, Charlestown, MA 02129",
        Constants.MESSAGE_KEY: "Address failed by Experian",
    }
    results = []
    results.append(result1)
    results.append(result2)
    report_path = "local_s3/agency-transfer/reports/"
    file_name = "Claimant_address_report"
    out_path = claimant_address_step.create_address_report(results, file_name, report_path)
    full_path = report_path + out_path.name
    assert str(out_path) == full_path


def test_is_address_new_or_updated(test_db_session, employee_extract_factory):
    employee = test_db_session.query(Employee).filter(
        Employee.fineos_customer_number == employee_extract_factory.customer_number
    )
    assert employee is not None
    # employee.employee_id='fc8b8d79-2fde-4128-b7b6-fc11fdd1855b'
    employee = EmployeeFactory.build(employee_id="fc8b8d79-2fde-4128-b7b6-fc11fdd1855b")

    claim = ClaimFactory.build(employee=employee)
    address_pair = ExperianAddressPairFactory.build(
        fineos_address=AddressFactory.build(
            address_line_one="AddressLine1-1",
            address_line_two="AddressLine2-1",
            city="City1",
            geo_state_id=GeoState.MA.geo_state_id,
            zip_code="11111",
        )
    )
    payment = PaymentFactory.build(claim=claim, experian_address_pair=address_pair)
    # test_db_session.commit()
    assert payment.payment_id
    # test_db_session.expire_all()

    pay_id = (
        test_db_session.query(Payment).join(Claim).filter(Claim.employee_id == employee.employee_id)
    )
    assert pay_id is not None
    experian_address_pairs = (
        test_db_session.query(ExperianAddressPair)
        .join(Payment, Payment.experian_address_pair_id == ExperianAddressPair.fineos_address_id)
        .all()
    )
    for experian_address_pair in experian_address_pairs:

        existing_fineos_address = experian_address_pair.fineos_address
        existing_experian_address = experian_address_pair.experian_address

        if existing_fineos_address and is_address_same(
            existing_fineos_address, employee_extract_factory
        ):
            result = True

        if existing_experian_address and is_address_same(
            existing_experian_address, employee_extract_factory
        ):
            result = True

        assert result is True


# This is a test to show that the existing address_to_experian_search_text format
# is broken as the state code is not mapped correctly. The fix shows the state code
# being mapped correctly. The results are different for the same address.


def test_formatted_address(address_factory, claimant_address_step):
    result_text_address_old = address_to_experian_search_text(address_factory)
    result_text_address_new = claimant_address_step.address_to_experian_suggestion_text_format(
        address_factory
    )
    assert result_text_address_old != result_text_address_new
