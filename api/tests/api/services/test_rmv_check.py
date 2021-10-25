import json
from datetime import date, timedelta

import pytest
from werkzeug.exceptions import InternalServerError, ServiceUnavailable

import massgov.pfml.rmv.errors as rmv_errors
from massgov.pfml.api.services.rmv_check import (
    RMVCheckApiErrorCode,
    RMVCheckRequest,
    do_checks,
    handle_rmv_check_request,
    make_response_from_rmv_check,
)
from massgov.pfml.db.models.applications import RMVCheck
from massgov.pfml.rmv.caller import MockZeepCaller
from massgov.pfml.rmv.client import RmvClient
from massgov.pfml.rmv.models import RmvAcknowledgement, VendorLicenseInquiryResponse


@pytest.fixture
def matching_check_data():
    rmv_check_request = RMVCheckRequest(
        first_name="Jane",
        last_name="Doe",
        date_of_birth=date(1970, 1, 1),
        ssn_last_4="1234",
        mass_id_number="S12345678",
        residential_address_line_1="123 Main St.",
        residential_address_line_2="Apt. 123",
        residential_address_city="Boston",
        residential_address_zip_code="12345",
        absence_case_id="foo",
    )

    license_inquiry_response = VendorLicenseInquiryResponse(
        customer_key="5678",
        license_id=rmv_check_request.mass_id_number,
        license1_expiration_date=date.today() + timedelta(days=365),
        license2_expiration_date=None,
        cfl_sanctions=False,
        cfl_sanctions_active=False,
        is_customer_inactive=False,
        street1=rmv_check_request.residential_address_line_1,
        street2=rmv_check_request.residential_address_line_2,
        city=rmv_check_request.residential_address_city,
        zip=rmv_check_request.residential_address_zip_code,
        sex="F",
    )

    return (rmv_check_request, license_inquiry_response)


def make_raw_rmv_response_from_pydantic_model(license_inquiry_response):
    starting = json.loads(license_inquiry_response.json(by_alias=True))

    if val := starting.get("License1ExpirationDate", None):
        starting["License1ExpirationDate"] = val.replace("-", "")

    if val := starting.get("License2ExpirationDate", None):
        starting["License2ExpirationDate"] = val.replace("-", "")

    return starting


def test_do_checks_pass(matching_check_data):
    (rmv_check_request, license_inquiry_response) = matching_check_data
    rmv_check_record = RMVCheck()

    result = do_checks(rmv_check_request, license_inquiry_response, rmv_check_record)

    assert result.check_expiration is True
    assert result.check_customer_inactive is True
    assert result.check_active_fraudulent_activity is True
    assert result.check_mass_id_number is True
    assert result.check_residential_address_line_1 is True
    assert result.check_residential_address_line_2 is True
    assert result.check_residential_city is True
    assert result.check_residential_zip_code is True
    assert result.has_passed_required_checks is True


def test_do_checks_fail_expiration_license1(matching_check_data):
    (rmv_check_request, license_inquiry_response) = matching_check_data
    rmv_check_record = RMVCheck()

    license_inquiry_response.license1_expiration_date = date.today() - timedelta(days=1)

    result = do_checks(rmv_check_request, license_inquiry_response, rmv_check_record)

    assert result.check_expiration is False
    assert result.check_customer_inactive is True
    assert result.check_active_fraudulent_activity is True
    assert result.check_mass_id_number is True
    assert result.check_residential_address_line_1 is True
    assert result.check_residential_address_line_2 is True
    assert result.check_residential_city is True
    assert result.check_residential_zip_code is True
    assert result.has_passed_required_checks is False


def test_do_checks_fail_expiration_if_license2_with_no_license1(matching_check_data):
    (rmv_check_request, license_inquiry_response) = matching_check_data
    rmv_check_record = RMVCheck()

    license_inquiry_response.license1_expiration_date = None
    license_inquiry_response.license2_expiration_date = date.today() - timedelta(days=1)

    result = do_checks(rmv_check_request, license_inquiry_response, rmv_check_record)

    assert result.check_expiration is False
    assert result.check_customer_inactive is True
    assert result.check_active_fraudulent_activity is True
    assert result.check_mass_id_number is True
    assert result.check_residential_address_line_1 is True
    assert result.check_residential_address_line_2 is True
    assert result.check_residential_city is True
    assert result.check_residential_zip_code is True
    assert result.has_passed_required_checks is False


def test_do_checks_pass_expiration_if_only_license2_expired(matching_check_data):
    (rmv_check_request, license_inquiry_response) = matching_check_data
    rmv_check_record = RMVCheck()

    license_inquiry_response.license1_expiration_date = date.today() + timedelta(days=1)
    license_inquiry_response.license2_expiration_date = date.today() - timedelta(days=1)

    result = do_checks(rmv_check_request, license_inquiry_response, rmv_check_record)

    assert result.check_expiration is True
    assert result.check_customer_inactive is True
    assert result.check_active_fraudulent_activity is True
    assert result.check_mass_id_number is True
    assert result.check_residential_address_line_1 is True
    assert result.check_residential_address_line_2 is True
    assert result.check_residential_city is True
    assert result.check_residential_zip_code is True
    assert result.has_passed_required_checks is True


def test_do_checks_fail_customer_inactive(matching_check_data):
    (rmv_check_request, license_inquiry_response) = matching_check_data
    rmv_check_record = RMVCheck()

    license_inquiry_response.is_customer_inactive = True

    result = do_checks(rmv_check_request, license_inquiry_response, rmv_check_record)

    assert result.check_expiration is True
    assert result.check_customer_inactive is False
    assert result.check_active_fraudulent_activity is True
    assert result.check_mass_id_number is True
    assert result.check_residential_address_line_1 is True
    assert result.check_residential_address_line_2 is True
    assert result.check_residential_city is True
    assert result.check_residential_zip_code is True
    assert result.has_passed_required_checks is False


def test_do_checks_fail_fraudulent_activity(matching_check_data):
    (rmv_check_request, license_inquiry_response) = matching_check_data
    rmv_check_record = RMVCheck()

    license_inquiry_response.cfl_sanctions = True
    license_inquiry_response.cfl_sanctions_active = True

    result = do_checks(rmv_check_request, license_inquiry_response, rmv_check_record)

    assert result.check_expiration is True
    assert result.check_customer_inactive is True
    assert result.check_active_fraudulent_activity is False
    assert result.check_mass_id_number is True
    assert result.check_residential_address_line_1 is True
    assert result.check_residential_address_line_2 is True
    assert result.check_residential_city is True
    assert result.check_residential_zip_code is True
    assert result.has_passed_required_checks is False

    # ensure it has to be marked as active
    license_inquiry_response.cfl_sanctions = True
    license_inquiry_response.cfl_sanctions_active = False

    result = do_checks(rmv_check_request, license_inquiry_response, rmv_check_record)

    assert result.check_active_fraudulent_activity is True

    # ensure being marked as active isn't the *only* requirement
    license_inquiry_response.cfl_sanctions = False
    license_inquiry_response.cfl_sanctions_active = True

    result = do_checks(rmv_check_request, license_inquiry_response, rmv_check_record)

    assert result.check_active_fraudulent_activity is True


def test_do_checks_fail_mass_id_number(matching_check_data):
    (rmv_check_request, license_inquiry_response) = matching_check_data
    rmv_check_record = RMVCheck()

    rmv_check_request.mass_id_number = "S12345678"
    license_inquiry_response.license_id = "S87654321"

    result = do_checks(rmv_check_request, license_inquiry_response, rmv_check_record)

    assert result.check_expiration is True
    assert result.check_customer_inactive is True
    assert result.check_active_fraudulent_activity is True
    assert result.check_mass_id_number is False
    assert result.check_residential_address_line_1 is True
    assert result.check_residential_address_line_2 is True
    assert result.check_residential_city is True
    assert result.check_residential_zip_code is True
    assert result.has_passed_required_checks is False


def test_do_checks_pass_residential_address_line_1_mismatch(matching_check_data):
    (rmv_check_request, license_inquiry_response) = matching_check_data
    rmv_check_record = RMVCheck()

    rmv_check_request.residential_address_line_1 = "Foo"
    license_inquiry_response.street1 = "123 Main St."

    result = do_checks(rmv_check_request, license_inquiry_response, rmv_check_record)

    assert result.check_expiration is True
    assert result.check_customer_inactive is True
    assert result.check_active_fraudulent_activity is True
    assert result.check_mass_id_number is True
    assert result.check_residential_address_line_1 is False
    assert result.check_residential_address_line_2 is True
    assert result.check_residential_city is True
    assert result.check_residential_zip_code is True
    assert result.has_passed_required_checks is True

    # even if conceptually the same
    rmv_check_request.residential_address_line_1 = "123 Main St"
    license_inquiry_response.street1 = "123 Main Street"

    result = do_checks(rmv_check_request, license_inquiry_response, rmv_check_record)

    assert result.check_residential_address_line_1 is False
    assert result.has_passed_required_checks is True

    # even minor differences
    rmv_check_request.residential_address_line_1 = "123 Main St"
    license_inquiry_response.street1 = "123 Main St."

    result = do_checks(rmv_check_request, license_inquiry_response, rmv_check_record)

    assert result.check_residential_address_line_1 is False
    assert result.has_passed_required_checks is True


def test_do_checks_pass_residential_address_line_1_case_insensitive(matching_check_data):
    (rmv_check_request, license_inquiry_response) = matching_check_data
    rmv_check_record = RMVCheck()

    rmv_check_request.residential_address_line_1 = "123 Main St."
    license_inquiry_response.street1 = "123 MAIN ST."

    result = do_checks(rmv_check_request, license_inquiry_response, rmv_check_record)

    assert result.check_expiration is True
    assert result.check_customer_inactive is True
    assert result.check_active_fraudulent_activity is True
    assert result.check_mass_id_number is True
    assert result.check_residential_address_line_1 is True
    assert result.check_residential_address_line_2 is True
    assert result.check_residential_city is True
    assert result.check_residential_zip_code is True
    assert result.has_passed_required_checks is True


def test_do_checks_pass_residential_address_line_2_mismatch(matching_check_data):
    (rmv_check_request, license_inquiry_response) = matching_check_data
    rmv_check_record = RMVCheck()

    rmv_check_request.residential_address_line_2 = "Foo"
    license_inquiry_response.street2 = "Unit 123"

    result = do_checks(rmv_check_request, license_inquiry_response, rmv_check_record)

    assert result.check_expiration is True
    assert result.check_customer_inactive is True
    assert result.check_active_fraudulent_activity is True
    assert result.check_mass_id_number is True
    assert result.check_residential_address_line_1 is True
    assert result.check_residential_address_line_2 is False
    assert result.check_residential_city is True
    assert result.check_residential_zip_code is True
    assert result.has_passed_required_checks is True

    # if RMV has a line 2 on record, but not provided by user
    rmv_check_request.residential_address_line_2 = None
    license_inquiry_response.street2 = "Unit 123"

    result = do_checks(rmv_check_request, license_inquiry_response, rmv_check_record)

    assert result.check_residential_address_line_2 is False
    assert result.has_passed_required_checks is True

    # even if conceptually the same
    rmv_check_request.residential_address_line_2 = "Apt 123"
    license_inquiry_response.street2 = "Unit 123"

    result = do_checks(rmv_check_request, license_inquiry_response, rmv_check_record)

    assert result.check_residential_address_line_2 is False
    assert result.has_passed_required_checks is True

    # even on minor differences
    rmv_check_request.residential_address_line_2 = "Apt. 123"
    license_inquiry_response.street2 = "Apt 123"

    result = do_checks(rmv_check_request, license_inquiry_response, rmv_check_record)

    assert result.check_residential_address_line_2 is False
    assert result.has_passed_required_checks is True


def test_do_checks_pass_residential_address_line_2_case_insensitive(matching_check_data):
    (rmv_check_request, license_inquiry_response) = matching_check_data
    rmv_check_record = RMVCheck()

    rmv_check_request.residential_address_line_2 = "UNIT 123"
    license_inquiry_response.street2 = "Unit 123"

    result = do_checks(rmv_check_request, license_inquiry_response, rmv_check_record)

    assert result.check_expiration is True
    assert result.check_customer_inactive is True
    assert result.check_active_fraudulent_activity is True
    assert result.check_mass_id_number is True
    assert result.check_residential_address_line_1 is True
    assert result.check_residential_address_line_2 is True
    assert result.check_residential_city is True
    assert result.check_residential_zip_code is True
    assert result.has_passed_required_checks is True


def test_do_checks_pass_residential_address_line_2_when_not_needed(matching_check_data):
    (rmv_check_request, license_inquiry_response) = matching_check_data
    rmv_check_record = RMVCheck()

    rmv_check_request.residential_address_line_2 = None
    license_inquiry_response.street2 = None

    result = do_checks(rmv_check_request, license_inquiry_response, rmv_check_record)

    assert result.check_expiration is True
    assert result.check_customer_inactive is True
    assert result.check_active_fraudulent_activity is True
    assert result.check_mass_id_number is True
    assert result.check_residential_address_line_1 is True
    assert result.check_residential_address_line_2 is True
    assert result.check_residential_city is True
    assert result.check_residential_zip_code is True
    assert result.has_passed_required_checks is True

    # if user provides a line two, but RMV doesn't have it on record, that's okay
    rmv_check_request.residential_address_line_2 = "Apt 123"
    license_inquiry_response.street2 = None

    result = do_checks(rmv_check_request, license_inquiry_response, rmv_check_record)

    assert result.check_residential_address_line_2 is True
    assert result.has_passed_required_checks is True


def test_do_checks_fail_residential_city(matching_check_data):
    (rmv_check_request, license_inquiry_response) = matching_check_data
    rmv_check_record = RMVCheck()

    rmv_check_request.residential_address_city = "Foo"
    license_inquiry_response.city = "Boston"

    result = do_checks(rmv_check_request, license_inquiry_response, rmv_check_record)

    assert result.check_expiration is True
    assert result.check_customer_inactive is True
    assert result.check_active_fraudulent_activity is True
    assert result.check_mass_id_number is True
    assert result.check_residential_address_line_1 is True
    assert result.check_residential_address_line_2 is True
    assert result.check_residential_city is False
    assert result.check_residential_zip_code is True
    assert result.has_passed_required_checks is False

    # even with minor differences
    rmv_check_request.residential_address_city = "Boston "
    license_inquiry_response.city = "Boston"

    result = do_checks(rmv_check_request, license_inquiry_response, rmv_check_record)

    assert result.check_residential_city is False
    assert result.has_passed_required_checks is False


def test_do_checks_pass_residential_address_city_case_insensitive(matching_check_data):
    (rmv_check_request, license_inquiry_response) = matching_check_data
    rmv_check_record = RMVCheck()

    rmv_check_request.residential_address_city = "Boston"
    license_inquiry_response.city = "BOSTON"

    result = do_checks(rmv_check_request, license_inquiry_response, rmv_check_record)

    assert result.check_expiration is True
    assert result.check_customer_inactive is True
    assert result.check_active_fraudulent_activity is True
    assert result.check_mass_id_number is True
    assert result.check_residential_address_line_1 is True
    assert result.check_residential_address_line_2 is True
    assert result.check_residential_city is True
    assert result.check_residential_zip_code is True
    assert result.has_passed_required_checks is True


def test_do_checks_fail_residential_zip_code(matching_check_data):
    (rmv_check_request, license_inquiry_response) = matching_check_data
    rmv_check_record = RMVCheck()

    rmv_check_request.residential_address_zip_code = "12345"
    license_inquiry_response.zip = "67890"

    result = do_checks(rmv_check_request, license_inquiry_response, rmv_check_record)

    assert result.check_expiration is True
    assert result.check_customer_inactive is True
    assert result.check_active_fraudulent_activity is True
    assert result.check_mass_id_number is True
    assert result.check_residential_address_line_1 is True
    assert result.check_residential_address_line_2 is True
    assert result.check_residential_city is True
    assert result.check_residential_zip_code is False
    assert result.has_passed_required_checks is False

    # even with minor differences
    rmv_check_request.residential_address_zip_code = "12345-6789"
    license_inquiry_response.city = "123"

    result = do_checks(rmv_check_request, license_inquiry_response, rmv_check_record)

    assert result.check_residential_city is False
    assert result.has_passed_required_checks is False


def test_do_checks_pass_residential_zip_code_first_five(matching_check_data):
    (rmv_check_request, license_inquiry_response) = matching_check_data
    rmv_check_record = RMVCheck()

    rmv_check_request.residential_address_zip_code = "12345-6789"
    license_inquiry_response.zip = "12345"

    result = do_checks(rmv_check_request, license_inquiry_response, rmv_check_record)

    assert result.check_expiration is True
    assert result.check_customer_inactive is True
    assert result.check_active_fraudulent_activity is True
    assert result.check_mass_id_number is True
    assert result.check_residential_address_line_1 is True
    assert result.check_residential_address_line_2 is True
    assert result.check_residential_city is True
    assert result.check_residential_zip_code is True
    assert result.has_passed_required_checks is True


def test_make_response_from_rmv_check_pass():
    response = make_response_from_rmv_check(
        RMVCheck(
            check_expiration=True,
            check_customer_inactive=True,
            check_active_fraudulent_activity=True,
            check_mass_id_number=True,
            check_residential_address_line_1=True,
            check_residential_address_line_2=True,
            check_residential_city=True,
            check_residential_zip_code=True,
            has_passed_required_checks=True,
        ),
    )

    assert response.verified is True
    assert response.description == "Verification check passed."


def test_make_response_from_rmv_check_fail_due_to_rmv_not_found():
    response = make_response_from_rmv_check(
        RMVCheck(
            rmv_error_code=RmvAcknowledgement.CUSTOMER_NOT_FOUND, has_passed_required_checks=False,
        ),
    )

    assert response.verified is False
    assert (
        response.description
        == "Verification failed because no record could be found for given ID information."
    )

    response = make_response_from_rmv_check(
        RMVCheck(
            rmv_error_code=RmvAcknowledgement.CREDENTIAL_NOT_FOUND,
            has_passed_required_checks=False,
        )
    )

    assert response.verified is False
    assert (
        response.description
        == "Verification failed because no record could be found for given ID information."
    )


def test_make_response_from_rmv_check_500_due_to_rmv_required_fields_missing():
    with pytest.raises(InternalServerError):
        make_response_from_rmv_check(
            RMVCheck(
                rmv_error_code=RmvAcknowledgement.REQUIRED_FIELDS_MISSING,
                has_passed_required_checks=False,
            )
        )


def test_make_response_from_rmv_check_503_due_to_networking_issues():
    with pytest.raises(ServiceUnavailable):
        make_response_from_rmv_check(
            RMVCheck(
                api_error_code=RMVCheckApiErrorCode.NETWORKING_ISSUES,
                has_passed_required_checks=False,
            )
        )


def test_make_response_from_rmv_check_500_due_to_failing_to_parse_rmv_response():
    with pytest.raises(InternalServerError):
        make_response_from_rmv_check(
            RMVCheck(
                api_error_code=RMVCheckApiErrorCode.FAILED_TO_PARSE_RESPONSE,
                has_passed_required_checks=False,
            )
        )


def test_make_response_from_rmv_check_fail_due_to_one_thing():
    response = make_response_from_rmv_check(
        RMVCheck(
            check_expiration=False,
            check_customer_inactive=True,
            check_active_fraudulent_activity=True,
            check_mass_id_number=True,
            check_residential_address_line_1=True,
            check_residential_address_line_2=True,
            check_residential_city=True,
            check_residential_zip_code=True,
            has_passed_required_checks=False,
        ),
    )

    assert response.verified is False
    assert response.description == "Verification failed because ID is expired."


def test_make_response_from_rmv_check_fail_due_to_multiple_thing():
    response = make_response_from_rmv_check(
        RMVCheck(
            check_expiration=True,
            check_customer_inactive=False,
            check_active_fraudulent_activity=True,
            check_mass_id_number=True,
            check_residential_address_line_1=False,
            check_residential_address_line_2=True,
            check_residential_city=True,
            check_residential_zip_code=False,
            has_passed_required_checks=False,
        ),
    )

    assert response.verified is False
    assert (
        response.description
        == "Verification failed because ID holder is deceased and residential zip code mismatch."
    )


def test_handle_rmv_check_request_pass(test_db_session, matching_check_data):
    (rmv_check_request, license_inquiry_response) = matching_check_data

    caller = MockZeepCaller(license_inquiry_response.dict(by_alias=True))
    rmv_client = RmvClient(caller)

    rmv_check_record = handle_rmv_check_request(test_db_session, rmv_client, rmv_check_request)

    assert rmv_check_record

    assert rmv_check_record.rmv_check_id

    assert rmv_check_record.absence_case_id == rmv_check_record.absence_case_id

    assert rmv_check_record.created_at
    assert rmv_check_record.request_to_rmv_started_at
    assert rmv_check_record.request_to_rmv_completed_at
    assert (
        rmv_check_record.request_to_rmv_started_at != rmv_check_record.request_to_rmv_completed_at
    )

    assert rmv_check_record.rmv_error_code is None
    assert rmv_check_record.api_error_code is None

    assert rmv_check_record.rmv_customer_key == license_inquiry_response.customer_key

    assert rmv_check_record.check_expiration is True
    assert rmv_check_record.check_customer_inactive is True
    assert rmv_check_record.check_active_fraudulent_activity is True
    assert rmv_check_record.check_mass_id_number is True
    assert rmv_check_record.check_residential_address_line_1 is True
    assert rmv_check_record.check_residential_address_line_2 is True
    assert rmv_check_record.check_residential_city is True
    assert rmv_check_record.check_residential_zip_code is True

    assert rmv_check_record.has_passed_required_checks is True


def test_handle_rmv_check_request_fail(test_db_session, matching_check_data):
    (rmv_check_request, license_inquiry_response) = matching_check_data

    license_inquiry_response.license1_expiration_date = date.today() - timedelta(days=1)

    caller = MockZeepCaller(license_inquiry_response.dict(by_alias=True))
    rmv_client = RmvClient(caller)

    rmv_check_record = handle_rmv_check_request(test_db_session, rmv_client, rmv_check_request)

    assert rmv_check_record

    assert rmv_check_record.rmv_check_id

    assert rmv_check_record.absence_case_id == rmv_check_record.absence_case_id

    assert rmv_check_record.created_at
    assert rmv_check_record.request_to_rmv_started_at
    assert rmv_check_record.request_to_rmv_completed_at
    assert (
        rmv_check_record.request_to_rmv_started_at != rmv_check_record.request_to_rmv_completed_at
    )

    assert rmv_check_record.rmv_error_code is None
    assert rmv_check_record.api_error_code is None

    assert rmv_check_record.rmv_customer_key == license_inquiry_response.customer_key

    assert rmv_check_record.check_expiration is False
    assert rmv_check_record.check_customer_inactive is True
    assert rmv_check_record.check_active_fraudulent_activity is True
    assert rmv_check_record.check_mass_id_number is True
    assert rmv_check_record.check_residential_address_line_1 is True
    assert rmv_check_record.check_residential_address_line_2 is True
    assert rmv_check_record.check_residential_city is True
    assert rmv_check_record.check_residential_zip_code is True

    assert rmv_check_record.has_passed_required_checks is False


def test_handle_rmv_check_request_fail_rmv_request(test_db_session, matching_check_data):
    (rmv_check_request, _) = matching_check_data

    caller = MockZeepCaller({"Acknowledgement": RmvAcknowledgement.CUSTOMER_NOT_FOUND.value})
    rmv_client = RmvClient(caller)

    rmv_check_record = handle_rmv_check_request(test_db_session, rmv_client, rmv_check_request)

    assert rmv_check_record

    assert rmv_check_record.rmv_check_id

    assert rmv_check_record.absence_case_id == rmv_check_record.absence_case_id

    assert rmv_check_record.created_at
    assert rmv_check_record.request_to_rmv_started_at
    assert rmv_check_record.request_to_rmv_completed_at
    assert (
        rmv_check_record.request_to_rmv_started_at != rmv_check_record.request_to_rmv_completed_at
    )

    assert rmv_check_record.rmv_error_code is RmvAcknowledgement.CUSTOMER_NOT_FOUND
    assert rmv_check_record.api_error_code is None

    assert rmv_check_record.rmv_customer_key is None

    assert rmv_check_record.check_expiration is False
    assert rmv_check_record.check_customer_inactive is False
    assert rmv_check_record.check_active_fraudulent_activity is False
    assert rmv_check_record.check_mass_id_number is False
    assert rmv_check_record.check_residential_address_line_1 is False
    assert rmv_check_record.check_residential_address_line_2 is False
    assert rmv_check_record.check_residential_city is False
    assert rmv_check_record.check_residential_zip_code is False

    assert rmv_check_record.has_passed_required_checks is False


def test_handle_rmv_check_request_fail_rmv_server_error(
    test_db_session, matching_check_data, mocker
):
    (rmv_check_request, _) = matching_check_data

    rmv_client = mocker.patch("massgov.pfml.rmv.client.RmvClient", autospec=True)
    rmv_client.vendor_license_inquiry.side_effect = rmv_errors.RmvError

    rmv_check_record = handle_rmv_check_request(test_db_session, rmv_client, rmv_check_request)

    assert rmv_check_record

    assert rmv_check_record.rmv_check_id

    assert rmv_check_record.absence_case_id == rmv_check_record.absence_case_id

    assert rmv_check_record.created_at
    assert rmv_check_record.request_to_rmv_started_at
    assert rmv_check_record.request_to_rmv_completed_at
    assert (
        rmv_check_record.request_to_rmv_started_at != rmv_check_record.request_to_rmv_completed_at
    )

    assert rmv_check_record.rmv_error_code is None
    assert rmv_check_record.api_error_code is RMVCheckApiErrorCode.UNKNOWN_RMV_ISSUE

    assert rmv_check_record.rmv_customer_key is None

    assert rmv_check_record.check_expiration is False
    assert rmv_check_record.check_customer_inactive is False
    assert rmv_check_record.check_active_fraudulent_activity is False
    assert rmv_check_record.check_mass_id_number is False
    assert rmv_check_record.check_residential_address_line_1 is False
    assert rmv_check_record.check_residential_address_line_2 is False
    assert rmv_check_record.check_residential_city is False
    assert rmv_check_record.check_residential_zip_code is False

    assert rmv_check_record.has_passed_required_checks is False
