import faker
import pytest
from sqlalchemy.exc import SQLAlchemyError

import massgov.pfml.util.users as users_util
from massgov.pfml.db.models.employees import User
from massgov.pfml.db.models.factories import UserFactory

fake = faker.Faker()


@pytest.mark.integration
def test_register_user_success(test_db_session, mock_cognito, mock_cognito_user_pool):
    email_address = fake.email(domain="example.com")

    user = users_util.register_user(
        test_db_session,
        mock_cognito_user_pool["id"],
        mock_cognito_user_pool["client_id"],
        email_address,
        fake.password(length=12),
        cognito_client=mock_cognito,
    )

    assert user.sub_id is not None
    assert user.email_address == email_address

    # User added to DB
    user = test_db_session.query(User).filter(User.email_address == email_address).one_or_none()
    assert user.sub_id is not None

    # User added to user pool
    cognito_users = mock_cognito.list_users(UserPoolId=mock_cognito_user_pool["id"],)
    assert cognito_users["Users"][0]["Username"] == email_address


@pytest.mark.integration
def test_register_user_raises_sql_exception(
    initialize_factories_session, test_db_session, mock_cognito, mock_cognito_user_pool, monkeypatch
):
    sub_id = "mock-auth-id"

    def mock_create_cognito_account(*args, **kwargs):
        return sub_id

    monkeypatch.setattr(users_util, "create_cognito_account", mock_create_cognito_account)

    # Test DB failure
    # insert a User already containing the auth_id, forcing a unique key error
    UserFactory.create(sub_id=sub_id)

    with pytest.raises(SQLAlchemyError):
        users_util.register_user(
            test_db_session,
            mock_cognito_user_pool["id"],
            mock_cognito_user_pool["client_id"],
            fake.email(domain="example.com"),
            fake.password(length=12),
            cognito_client=mock_cognito,
        )


@pytest.mark.integration
def test_register_user_creates_missing_db_records(
    initialize_factories_session, test_db_session, mock_cognito, mock_cognito_user_pool, monkeypatch
):
    sub_id = "mock-auth-id"
    email_address = fake.email(domain="example.com")

    # This test is based on the assumption that in a previous request, a user was
    # successfully added to the Cognito user pool, but something prevented the
    # database records from being created. This requires us to mock a few
    # Cognito methods in order to simulate this.

    # Mock the sign up method to identify the user as already existing.
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

    # Mock the admin_get_user method to return the user with their Sub attribute,
    # which moto does not do, but the real boto does
    def admin_get_user(Username: str = None, UserPoolId: str = None):
        return {
            "Username": Username,
            "UserAttributes": [{"Name": "sub", "Value": sub_id}],
        }

    monkeypatch.setattr(mock_cognito, "admin_get_user", admin_get_user)
    monkeypatch.setattr(mock_cognito, "sign_up", sign_up)

    user = users_util.register_user(
        test_db_session,
        mock_cognito_user_pool["id"],
        mock_cognito_user_pool["client_id"],
        email_address,
        fake.password(length=12),
        cognito_client=mock_cognito,
    )

    assert user.sub_id == sub_id
    assert user.email_address == email_address
