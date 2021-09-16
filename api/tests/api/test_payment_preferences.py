import massgov.pfml.fineos.mock_client as fineos_mock
import tests.api
from massgov.pfml.api.validation.exceptions import IssueRule, IssueType
from massgov.pfml.db.models.applications import Address, ApplicationPaymentPreference
from massgov.pfml.db.models.employees import BankAccountType, PaymentMethod
from massgov.pfml.db.models.factories import ApplicationFactory


def submit_payment_pref_helper(client, user, auth_token, post_data, application):
    response = client.post(
        "/v1/applications/{}/submit_payment_preference".format(application.application_id),
        headers={"Authorization": f"Bearer {auth_token}"},
        json=post_data,
    )

    return response


def test_submit_payment_preference_ach_success(client, user, auth_token, test_db_session):
    application = ApplicationFactory.create(user=user)
    update_request_body = {
        "payment_preference": {
            "payment_method": "Elec Funds Transfer",
            "bank_account_type": "Checking",
            "routing_number": "011401533",
            "account_number": "123456789",
        },
    }
    fineos_mock.start_capture()
    response = submit_payment_pref_helper(
        client=client,
        user=user,
        auth_token=auth_token,
        post_data=update_request_body,
        application=application,
    )
    assert response.status_code == 201
    capture = fineos_mock.get_capture()

    expected_fineos_calls = ["find_employer", "register_api_user", "add_payment_preference"]
    assert len(capture) == len(expected_fineos_calls)
    assert [call[0] for call in capture] == expected_fineos_calls

    response_body = response.get_json()
    test_db_session.refresh(application)
    # Verify values in the DB are updated and not masked
    assert (
        application.payment_preference.payment_method.payment_method_id
        == PaymentMethod.ACH.payment_method_id
    )
    assert (
        application.payment_preference.bank_account_type.bank_account_type_id
        == BankAccountType.CHECKING.bank_account_type_id
    )
    assert application.payment_preference.account_number == "123456789"
    assert application.payment_preference.routing_number == "011401533"
    assert application.has_submitted_payment_preference is True

    # Verify values returned by the API are properly masked
    payment_preference = response_body.get("data").get("payment_preference")
    assert payment_preference["account_number"] == "*****6789"
    assert payment_preference["routing_number"] == "*********"
    assert payment_preference["payment_method"] == "Elec Funds Transfer"
    assert payment_preference["bank_account_type"] == "Checking"


def test_submit_payment_preference_check_success(client, user, auth_token, test_db_session):
    application = ApplicationFactory.create(user=user)
    update_request_body = {
        "payment_preference": {"payment_method": "Check",},
    }
    fineos_mock.start_capture()
    response = submit_payment_pref_helper(
        client=client,
        user=user,
        auth_token=auth_token,
        post_data=update_request_body,
        application=application,
    )
    assert response.status_code == 201
    capture = fineos_mock.get_capture()

    expected_fineos_calls = ["find_employer", "register_api_user", "add_payment_preference"]
    assert len(capture) == len(expected_fineos_calls)
    assert [call[0] for call in capture] == expected_fineos_calls

    response_body = response.get_json()
    test_db_session.refresh(application)
    # Verify values in the DB are updated and not masked
    assert (
        application.payment_preference.payment_method.payment_method_id
        == PaymentMethod.CHECK.payment_method_id
    )
    assert application.has_submitted_payment_preference is True

    # Verify values returned by the API are properly masked
    payment_preference = response_body.get("data").get("payment_preference")
    assert payment_preference["payment_method"] == "Check"


def test_submit_payment_preference_ach_mailing_addr_override(
    client, user, auth_token, test_db_session
):
    mailing_address = Address(
        address_line_one="123 Foo St.",
        address_line_two="Apt #123",
        city="Chicago",
        geo_state_id=17,  # Illinois
        zip_code="12345-6789",
    )
    application = ApplicationFactory.create(
        user=user, has_mailing_address=True, mailing_address=mailing_address
    )
    update_request_body = {
        "payment_preference": {
            "payment_method": "Elec Funds Transfer",
            "bank_account_type": "Checking",
            "routing_number": "011401533",
            "account_number": "123456789",
        },
    }
    fineos_mock.start_capture()
    response = submit_payment_pref_helper(
        client=client,
        user=user,
        auth_token=auth_token,
        post_data=update_request_body,
        application=application,
    )
    assert response.status_code == 201
    capture = fineos_mock.get_capture()

    expected_fineos_calls = ["find_employer", "register_api_user", "add_payment_preference"]
    assert len(capture) == len(expected_fineos_calls)
    assert [call[0] for call in capture] == expected_fineos_calls

    response_body = response.get_json()
    test_db_session.refresh(application)
    assert application.payment_preference.account_number == "123456789"
    assert application.payment_preference.routing_number == "011401533"
    assert application.has_mailing_address is True

    mailing_address = response_body.get("data").get("mailing_address")
    assert mailing_address["city"] == "Chicago"
    assert mailing_address["zip"] == "12345-****"
    assert mailing_address["line_1"] == "*******"


def test_submit_payment_preference_already_submitted(client, user, auth_token, test_db_session):
    application = ApplicationFactory.create(user=user, has_submitted_payment_preference=True)
    update_request_body = {
        "payment_preference": {
            "payment_method": "Elec Funds Transfer",
            "bank_account_type": "Checking",
            "routing_number": "011401533",
            "account_number": "123456789",
        },
    }
    response = submit_payment_pref_helper(
        client=client,
        user=user,
        auth_token=auth_token,
        post_data=update_request_body,
        application=application,
    )
    assert response.status_code == 403
    tests.api.validate_error_response(
        response,
        403,
        "Application {} could not be updated. Payment preference already submitted".format(
            application.application_id
        ),
    )


def test_submit_null_payment_preference_error(client, user, auth_token, test_db_session):
    application = ApplicationFactory.create(user=user)
    update_request_body = {
        "payment_preference": None,
    }
    response = submit_payment_pref_helper(
        client=client,
        user=user,
        auth_token=auth_token,
        post_data=update_request_body,
        application=application,
    )
    assert response.status_code == 400
    tests.api.validate_error_response(response, 400, message="Request Validation Error")


def test_submit_payment_preference_no_payment_method_error(
    client, user, auth_token, test_db_session
):
    application = ApplicationFactory.create(user=user)
    update_request_body = {
        "payment_preference": {},
    }
    response = submit_payment_pref_helper(
        client=client,
        user=user,
        auth_token=auth_token,
        post_data=update_request_body,
        application=application,
    )
    assert response.status_code == 400
    assert len(response.get_json()["errors"]) == 1
    assert response.get_json()["errors"][0]["field"] == "payment_preference.payment_method"


def test_submit_payments_pref_masked_inputs_ignored(client, user, auth_token, test_db_session):
    application = ApplicationFactory.create(user=user)
    application.payment_preference = ApplicationPaymentPreference(
        routing_number="011401533", account_number="123456789",
    )
    test_db_session.commit()
    update_request_body = {
        "payment_preference": {
            "payment_method": "Elec Funds Transfer",
            "bank_account_type": "Checking",
            "routing_number": "*********",
            "account_number": "*****6789",
        },
    }
    response = submit_payment_pref_helper(
        client=client,
        user=user,
        auth_token=auth_token,
        post_data=update_request_body,
        application=application,
    )
    assert response.status_code == 201
    test_db_session.refresh(application)
    assert application.payment_preference.account_number == "123456789"
    assert application.payment_preference.routing_number == "011401533"


def test_submit_payments_pref_masked_mismatch_fields(client, user, auth_token, test_db_session):
    application = ApplicationFactory.create(user=user)
    application.payment_preference = ApplicationPaymentPreference(
        routing_number=None, account_number="123456789",
    )
    test_db_session.commit()
    update_request_body = {
        "payment_preference": {
            "payment_method": "Elec Funds Transfer",
            "bank_account_type": "Checking",
            "routing_number": "*********",
            "account_number": "*****0000",
        },
    }
    response = submit_payment_pref_helper(
        client=client,
        user=user,
        auth_token=auth_token,
        post_data=update_request_body,
        application=application,
    )
    assert response.status_code == 400
    tests.api.validate_error_response(response, 400, message="Error validating masked fields")

    fields = set(err["field"] for err in response.get_json()["errors"])
    expected_fields = set(
        ["payment_preference.account_number", "payment_preference.routing_number"]
    )
    assert expected_fields == fields
    errors = response.get_json()["errors"]
    for error in errors:
        assert error["type"] == IssueType.invalid_masked_field
        if error["field"] == "payment_preference.account_number":
            assert error["rule"] == IssueRule.disallow_mismatched_masked_field
        elif error["field"] == "payment_preference.routing_number":
            assert error["rule"] == IssueRule.disallow_fully_masked_no_existing


def test_submit_payments_pref_invalid_values(client, user, auth_token, test_db_session):
    application = ApplicationFactory.create(user=user)
    application.payment_preference = ApplicationPaymentPreference(
        routing_number=None, account_number="123456789",
    )
    test_db_session.commit()
    update_request_body = {
        "payment_preference": {
            "payment_method": "Elec Funds Transfer",
            "bank_account_type": "Checking",
            # routing_number should conform to the pattern (e.g 801234567),
            "routing_number": "80123456789",
        },
    }
    response = submit_payment_pref_helper(
        client=client,
        user=user,
        auth_token=auth_token,
        post_data=update_request_body,
        application=application,
    )
    tests.api.validate_error_response(
        response,
        400,
        message="Request Validation Error",
        errors=[
            {
                "field": "payment_preference.routing_number",
                "message": "'80123456789' does not match '^((0[0-9])|(1[0-2])|(2[1-9])|(3[0-2])|(6[1-9])|(7[0-2])|80)([0-9]{7})$|(\\\\*{9})$'",
                "rule": "^((0[0-9])|(1[0-2])|(2[1-9])|(3[0-2])|(6[1-9])|(7[0-2])|80)([0-9]{7})$|(\\*{9})$",
                "type": "pattern",
            },
        ],
    )
