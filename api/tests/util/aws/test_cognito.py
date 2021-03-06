import logging  # noqa: B1
from unittest import mock
from unittest.mock import MagicMock

import boto3
import botocore
import faker
import pytest

import massgov.pfml.util.aws.cognito as cognito_util
from massgov.pfml.cognito.exceptions import (
    CognitoAccountCreationFailure,
    CognitoLookupFailure,
    CognitoSubNotFound,
    CognitoUserExistsValidationError,
    CognitoValidationError,
)

fake = faker.Faker()


user_not_found_exception = boto3.client(
    "cognito-idp", "us-east-1"
).exceptions.UserNotFoundException(
    error_response={
        "Error": {
            "Code": "UserNotFoundException",
            "Message": ":(",
        }
    },
    operation_name="Foo",
)


@pytest.fixture
def auth_token():
    return "user cognito auth token"


@pytest.fixture
def magic_mock_cognito():
    # Used when we just want to be able to mock the implementation of and spy on cognito methods,
    # not use the full moto mock behavior
    return MagicMock()


def test_create_cognito_account(mock_cognito, mock_cognito_user_pool):
    email_address = fake.email(domain="example.com")

    sub = cognito_util.create_cognito_account(
        email_address,
        fake.password(length=12),
        mock_cognito_user_pool["id"],
        mock_cognito_user_pool["client_id"],
        cognito_client=mock_cognito,
    )

    users = mock_cognito.list_users(UserPoolId=mock_cognito_user_pool["id"])

    assert sub is not None
    assert users["Users"][0]["Username"] == email_address


def test_create_cognito_account_param_validation_error(mock_cognito, mock_cognito_user_pool):
    password = "short"  # invalid because it's less than 6 characters

    with pytest.raises(CognitoValidationError) as exc:
        cognito_util.create_cognito_account(
            fake.email(domain="example.com"),
            password,
            mock_cognito_user_pool["id"],
            mock_cognito_user_pool["client_id"],
            cognito_client=mock_cognito,
        )

    assert exc.value.issue.field == "password"
    assert exc.value.issue.type == "invalid"


def test_create_cognito_account_invalid_password_error(
    mock_cognito, mock_cognito_user_pool, monkeypatch
):
    def sign_up(**kwargs):
        raise mock_cognito.exceptions.InvalidPasswordException(
            error_response={
                "Error": {
                    "Code": "InvalidPasswordException",
                    "Message": "Password did not conform with policy: Password not long enough",
                }
            },
            operation_name="SignUp",
        )

    monkeypatch.setattr(mock_cognito, "sign_up", sign_up)

    with pytest.raises(CognitoValidationError) as exc:
        cognito_util.create_cognito_account(
            fake.email(domain="example.com"),
            fake.password(length=8),
            mock_cognito_user_pool["id"],
            mock_cognito_user_pool["client_id"],
            cognito_client=mock_cognito,
        )

    assert exc.value.issue.field == "password"
    assert exc.value.issue.type == "invalid"


def test_create_cognito_account_invalid_parameter_exception(
    mock_cognito, mock_cognito_user_pool, monkeypatch
):
    def sign_up(**kwargs):
        raise mock_cognito.exceptions.InvalidParameterException(
            error_response={
                "Error": {
                    "Code": "InvalidParameterException",
                    "Message": "1 validation error detected: Value at 'password' failed to satisfy constraint: Member must satisfy regular expression pattern: ^[\\S]+.*[\\S]+$",
                }
            },
            operation_name="SignUp",
        )

    monkeypatch.setattr(mock_cognito, "sign_up", sign_up)

    with pytest.raises(CognitoValidationError) as exc:
        cognito_util.create_cognito_account(
            fake.email(domain="example.com"),
            " abc123",  # One known way to trigger this exception is to begin a password with a space character
            mock_cognito_user_pool["id"],
            mock_cognito_user_pool["client_id"],
            cognito_client=mock_cognito,
        )

    assert exc.value.issue.field == "password"
    assert exc.value.issue.type == "invalid"


def test_create_cognito_account_insecure_password_error(
    mock_cognito, mock_cognito_user_pool, monkeypatch
):
    def sign_up(**kwargs):
        raise mock_cognito.exceptions.InvalidPasswordException(
            error_response={
                "Error": {
                    "Code": "InvalidPasswordException",
                    "Message": "Provided password cannot be used for security reasons.",
                }
            },
            operation_name="SignUp",
        )

    monkeypatch.setattr(mock_cognito, "sign_up", sign_up)

    with pytest.raises(CognitoValidationError) as exc:
        cognito_util.create_cognito_account(
            fake.email(domain="example.com"),
            "test123456",
            mock_cognito_user_pool["id"],
            mock_cognito_user_pool["client_id"],
            cognito_client=mock_cognito,
        )

    assert exc.value.issue.field == "password"
    assert exc.value.issue.type == "insecure"


def test_create_cognito_account_username_exists_error(
    mock_cognito, mock_cognito_user_pool, monkeypatch
):
    # Add a user so the subsequent sign up fails due to the user existing already,
    # and so we can return the existing user's id
    email_address = fake.email(domain="example.com")
    password = fake.password(length=12)
    existing_cognito_user = mock_cognito.sign_up(
        ClientId=mock_cognito_user_pool["client_id"], Username=email_address, Password=password
    )

    # Mock the admin_get_user method to return the user with their Sub attribute,
    # which moto does not do, but the real boto does
    def admin_get_user(Username: str = None, UserPoolId: str = None):
        return {
            "Username": Username,
            "UserAttributes": [{"Name": "sub", "Value": existing_cognito_user["UserSub"]}],
        }

    monkeypatch.setattr(mock_cognito, "admin_get_user", admin_get_user)

    # Mock the sign up method to identify the user as already existing.
    # Moto could handle this in the future, making this monkeypatch unnecessary,
    # assuming this gets merged: https://github.com/spulec/moto/pull/3765
    def sign_up(**kwargs):
        raise mock_cognito.exceptions.UsernameExistsException(
            error_response={
                "Error": {
                    "Code": "UserNotFoundException",
                    "Message": "An account with the given email already exists.",
                }
            },
            operation_name="SignUp",
        )

    monkeypatch.setattr(mock_cognito, "sign_up", sign_up)

    with pytest.raises(CognitoUserExistsValidationError) as exc:
        cognito_util.create_cognito_account(
            email_address,
            password,
            mock_cognito_user_pool["id"],
            mock_cognito_user_pool["client_id"],
            cognito_client=mock_cognito,
        )

    assert exc.value.issue.field == "email_address"
    assert exc.value.issue.message == "An account with the given email already exists."
    assert exc.value.issue.type == "exists"
    assert exc.value.sub_id == existing_cognito_user["UserSub"]


def test_create_cognito_account_client_error(mock_cognito, mock_cognito_user_pool, monkeypatch):
    def sign_up(**kwargs):
        raise botocore.exceptions.ClientError(
            error_response={
                "Error": {
                    "Code": "CodeDeliveryFailureException",  # error code that we don't catch
                    "Message": "Verification code failed to deliver successfully.",
                }
            },
            operation_name="SignUp",
        )

    monkeypatch.setattr(mock_cognito, "sign_up", sign_up)

    with pytest.raises(
        CognitoAccountCreationFailure,
        match="create_cognito_account error: CodeDeliveryFailureException: Verification code failed to deliver successfully.",
    ):
        cognito_util.create_cognito_account(
            fake.email(domain="example.com"),
            fake.password(length=12),
            mock_cognito_user_pool["id"],
            mock_cognito_user_pool["client_id"],
            cognito_client=mock_cognito,
        )


def test_lookup_cognito_account_id(monkeypatch, mock_cognito, mock_cognito_user_pool):
    email_address = fake.email(domain="example.com")
    existing_cognito_user = mock_cognito.sign_up(
        ClientId=mock_cognito_user_pool["client_id"],
        Username=email_address,
        Password=fake.password(length=12),
    )

    # Mock the admin_get_user method to return the user with their Sub attribute,
    # which moto does not do, but the real boto does
    def admin_get_user(Username: str = None, UserPoolId: str = None):
        return {
            "Username": Username,
            "UserAttributes": [{"Name": "sub", "Value": existing_cognito_user["UserSub"]}],
        }

    monkeypatch.setattr(mock_cognito, "admin_get_user", admin_get_user)

    id = cognito_util.lookup_cognito_account_id(
        email=email_address,
        cognito_user_pool_id=mock_cognito_user_pool["id"],
        cognito_client=mock_cognito,
    )

    assert id is existing_cognito_user["UserSub"]


def test_lookup_cognito_account_id_user_not_found(mock_cognito, mock_cognito_user_pool):
    id = cognito_util.lookup_cognito_account_id(
        email=fake.email(domain="example.com"),
        cognito_user_pool_id=mock_cognito_user_pool["id"],
        cognito_client=mock_cognito,
    )

    assert id is None


def test_lookup_cognito_account_id_missing_sub_attribute(
    monkeypatch, mock_cognito, mock_cognito_user_pool
):
    # Mock the admin_get_user method to return the user WITHOUT a Sub attribute
    def admin_get_user(Username: str = None, UserPoolId: str = None):
        return {"Username": Username, "UserAttributes": [{"Name": "email", "Value": Username}]}

    monkeypatch.setattr(mock_cognito, "admin_get_user", admin_get_user)

    with pytest.raises(CognitoSubNotFound):
        cognito_util.lookup_cognito_account_id(
            email=fake.email(domain="example.com"),
            cognito_user_pool_id=mock_cognito_user_pool["id"],
            cognito_client=mock_cognito,
        )


def test_lookup_cognito_account_id_retries(
    caplog, monkeypatch, mock_cognito, mock_cognito_user_pool
):
    caplog.set_level(logging.INFO)  # noqa: B1

    def admin_get_user(*args, **kwargs):
        raise mock_cognito.exceptions.TooManyRequestsException(
            error_response={
                "Error": {"Code": "TooManyRequestsException", "Message": "Too many requests"}
            },
            operation_name="AdminGetUser",
        )

    monkeypatch.setattr(mock_cognito, "admin_get_user", admin_get_user)

    with pytest.raises(CognitoLookupFailure):
        cognito_util.lookup_cognito_account_id(
            email=fake.email(domain="example.com"),
            cognito_user_pool_id=mock_cognito_user_pool["id"],
            cognito_client=mock_cognito,
        )

    retry_log_count = 0
    for record in caplog.records:
        if "Too many requests error from Cognito" in record.getMessage():
            retry_log_count += 1

    assert retry_log_count == 3


def test_lookup_user_mfa_status(monkeypatch, mock_cognito, mock_cognito_user_pool):
    email_address = fake.email(domain="example.com")

    def admin_get_user(Username: str = None, UserPoolId: str = None):
        return {
            "Username": Username,
            "UserAttributes": [{"Name": "phone_number_verified", "Value": "true"}],
        }

    monkeypatch.setattr(mock_cognito, "admin_get_user", admin_get_user)

    mfa_status = cognito_util.is_mfa_phone_verified(
        email=email_address, cognito_user_pool_id=mock_cognito_user_pool["id"]
    )

    assert mfa_status is True


def test_lookup_user_mfa_status_false(monkeypatch, mock_cognito, mock_cognito_user_pool):
    email_address = fake.email(domain="example.com")

    def admin_get_user(Username: str = None, UserPoolId: str = None):
        return {
            "Username": Username,
            "UserAttributes": [{"Name": "phone_number_verified", "Value": "false"}],
        }

    monkeypatch.setattr(mock_cognito, "admin_get_user", admin_get_user)

    mfa_status = cognito_util.is_mfa_phone_verified(
        email=email_address, cognito_user_pool_id=mock_cognito_user_pool["id"]
    )

    assert mfa_status is False


def test_lookup_user_mfa_status_with_no_attrs(monkeypatch, mock_cognito, mock_cognito_user_pool):
    email_address = fake.email(domain="example.com")

    def admin_get_user(Username: str = None, UserPoolId: str = None):
        return {"Username": Username, "UserAttributes": []}

    monkeypatch.setattr(mock_cognito, "admin_get_user", admin_get_user)

    mfa_status = cognito_util.is_mfa_phone_verified(
        email=email_address, cognito_user_pool_id=mock_cognito_user_pool["id"]
    )

    assert mfa_status is False


class TestEnableUserMfa:
    @pytest.fixture
    def mock_cognito(self, magic_mock_cognito):
        return magic_mock_cognito

    @mock.patch("massgov.pfml.util.aws.cognito.create_cognito_client")
    def test_success(self, mock_create_cognito, mock_cognito, auth_token):
        mock_create_cognito.return_value = mock_cognito

        cognito_util.enable_user_mfa(auth_token)

        mock_cognito.set_user_mfa_preference.assert_called_with(
            SMSMfaSettings={"Enabled": True}, AccessToken=auth_token
        )

    @mock.patch("massgov.pfml.util.aws.cognito.create_cognito_client")
    def test_user_not_found_raises_exception(
        self, mock_create_cognito, mock_cognito, auth_token, caplog
    ):
        mock_create_cognito.return_value = mock_cognito

        mock_set_mfa_prefs = mock_cognito.set_user_mfa_preference
        mock_set_mfa_prefs.side_effect = user_not_found_exception

        with pytest.raises(Exception):
            cognito_util.enable_user_mfa(auth_token)

        assert "User not found" in caplog.text


class TestDisableUserMfa:
    @pytest.fixture
    def mock_cognito(self, magic_mock_cognito):
        return magic_mock_cognito

    @mock.patch("massgov.pfml.util.aws.cognito.create_cognito_client")
    def test_success(self, mock_create_cognito, mock_cognito, auth_token):
        mock_create_cognito.return_value = mock_cognito

        cognito_util.disable_user_mfa(auth_token)

        mock_cognito.set_user_mfa_preference.assert_called_with(
            SMSMfaSettings={"Enabled": False}, AccessToken=auth_token
        )

    @mock.patch("massgov.pfml.util.aws.cognito.create_cognito_client")
    def test_user_not_found_raises_exception(
        self, mock_create_cognito, mock_cognito, auth_token, caplog
    ):
        mock_create_cognito.return_value = mock_cognito

        mock_set_mfa_prefs = mock_cognito.set_user_mfa_preference
        mock_set_mfa_prefs.side_effect = user_not_found_exception

        with pytest.raises(Exception):
            cognito_util.disable_user_mfa(auth_token)

        assert "User not found" in caplog.text


class TestAdminDisableUserMFA:
    @pytest.fixture
    def mock_cognito(self, magic_mock_cognito):
        return magic_mock_cognito

    @mock.patch("massgov.pfml.util.aws.cognito.create_cognito_client")
    def test_success(self, mock_create_cognito, mock_cognito):
        mock_create_cognito.return_value = mock_cognito

        cognito_util.admin_disable_user_mfa("foo@bar.com")

        mock_cognito.admin_set_user_mfa_preference.assert_called_with(
            SMSMfaSettings={"Enabled": False}, Username="foo@bar.com", UserPoolId=mock.ANY
        )

    @mock.patch("massgov.pfml.util.aws.cognito.create_cognito_client")
    def test_user_not_found_raises_exception(self, mock_create_cognito, mock_cognito, caplog):
        mock_create_cognito.return_value = mock_cognito

        mock_set_mfa_prefs = mock_cognito.admin_set_user_mfa_preference
        mock_set_mfa_prefs.side_effect = user_not_found_exception

        with pytest.raises(Exception):
            cognito_util.admin_disable_user_mfa("foo@bar.com")

        assert "User not found with email" in caplog.text
