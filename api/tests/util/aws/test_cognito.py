import botocore
import faker
import pytest

import massgov.pfml.util.aws.cognito as cognito_util

fake = faker.Faker()


def test_create_cognito_account(mock_cognito, mock_cognito_user_pool):
    email_address = fake.email(domain="example.com")

    sub = cognito_util.create_cognito_account(
        email_address,
        fake.password(length=12),
        mock_cognito_user_pool["client_id"],
        cognito_client=mock_cognito,
    )

    users = mock_cognito.list_users(UserPoolId=mock_cognito_user_pool["id"],)

    assert sub is not None
    assert users["Users"][0]["Username"] == email_address


def test_create_cognito_account_param_validation_error(mock_cognito, mock_cognito_user_pool):
    password = "short"  # invalid because it's less than 6 characters

    with pytest.raises(cognito_util.CognitoAccountCreationUserError) as exc:
        cognito_util.create_cognito_account(
            fake.email(domain="example.com"),
            password,
            mock_cognito_user_pool["client_id"],
            cognito_client=mock_cognito,
        )

    assert exc.value.issue.field == "password"
    assert exc.value.issue.type == "invalid"


def test_create_cognito_account_invalid_password_error(
    mock_cognito, mock_cognito_user_pool, monkeypatch
):
    def sign_up(ClientId, Username, Password):
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

    with pytest.raises(cognito_util.CognitoAccountCreationUserError) as exc:
        cognito_util.create_cognito_account(
            fake.email(domain="example.com"),
            fake.password(length=8),
            mock_cognito_user_pool["client_id"],
            cognito_client=mock_cognito,
        )

    assert exc.value.issue.field == "password"
    assert exc.value.issue.type == "invalid"


def test_create_cognito_account_insecure_password_error(
    mock_cognito, mock_cognito_user_pool, monkeypatch
):
    def sign_up(ClientId, Username, Password):
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

    with pytest.raises(cognito_util.CognitoAccountCreationUserError) as exc:
        cognito_util.create_cognito_account(
            fake.email(domain="example.com"),
            "test123456",
            mock_cognito_user_pool["client_id"],
            cognito_client=mock_cognito,
        )

    assert exc.value.issue.field == "password"
    assert exc.value.issue.type == "insecure"


def test_create_cognito_account_username_exists_error(
    mock_cognito, mock_cognito_user_pool, monkeypatch
):
    def sign_up(ClientId, Username, Password):
        raise mock_cognito.exceptions.UsernameExistsException(
            error_response={
                "Error": {
                    "Code": "UserNotFoundException",
                    "Message": "An account with the given email already exists.",
                }
            },
            operation_name="SignUp",
        )

    # Moto could handle this in the future, making this monkeypatch unnecessary,
    # assuming this gets merged: https://github.com/spulec/moto/pull/3765
    monkeypatch.setattr(mock_cognito, "sign_up", sign_up)

    with pytest.raises(cognito_util.CognitoAccountCreationUserError) as exc:
        cognito_util.create_cognito_account(
            fake.email(domain="example.com"),
            fake.password(length=12),
            mock_cognito_user_pool["client_id"],
            cognito_client=mock_cognito,
        )

    assert exc.value.issue.field == "email_address"
    assert exc.value.issue.type == "exists"


def test_create_cognito_account_client_error(mock_cognito, mock_cognito_user_pool, monkeypatch):
    def sign_up(ClientId, Username, Password):
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
        cognito_util.CognitoAccountCreationFailure,
        match="create_cognito_account error: CodeDeliveryFailureException: Verification code failed to deliver successfully.",
    ):
        cognito_util.create_cognito_account(
            fake.email(domain="example.com"),
            fake.password(length=12),
            mock_cognito_user_pool["client_id"],
            cognito_client=mock_cognito,
        )


@pytest.mark.integration
def test_create_verified_cognito_leave_admin_account(
    test_db_session, mock_cognito, mock_cognito_user_pool
):
    # Moto will not return a 'sub' attribute so we expect this error
    with pytest.raises(
        cognito_util.CognitoSubNotFound, match="Cognito did not return an ID for the user!"
    ):
        cognito_util.create_verified_cognito_leave_admin_account(
            test_db_session,
            "test@test.com",
            "1234567",
            cognito_user_pool_id=mock_cognito_user_pool["id"],
        )
    users = mock_cognito.list_users(UserPoolId=mock_cognito_user_pool["id"],)

    assert users["Users"][0]["Username"] == "test@test.com"


@pytest.mark.integration
def test_lookup_cognito_account_id(test_db_session, mock_cognito_user_pool):
    # Moto will not return a 'sub' attribute so we expect this error
    with pytest.raises(
        cognito_util.CognitoSubNotFound, match="Cognito did not return an ID for the user!"
    ):
        cognito_util.create_verified_cognito_leave_admin_account(
            test_db_session,
            "test@test.com",
            "1234567",
            cognito_user_pool_id=mock_cognito_user_pool["id"],
        )

    # ... the user has to be found for lookup_cognito_account_id to throw this error; a weird intersection to be sure
    with pytest.raises(
        cognito_util.CognitoSubNotFound, match="Cognito did not return an ID for the user!"
    ):
        cognito_util.lookup_cognito_account_id(
            email="test@test.com", cognito_user_pool_id=mock_cognito_user_pool["id"]
        )
