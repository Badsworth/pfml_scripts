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
        mock_cognito_user_pool["client_id"],
        email_address,
        fake.password(length=12),
        cognito_client=mock_cognito,
    )

    assert user.active_directory_id is not None
    assert user.email_address == email_address

    # User added to DB
    user = test_db_session.query(User).filter(User.email_address == email_address).one_or_none()
    assert user.active_directory_id is not None

    # User added to user pool
    cognito_users = mock_cognito.list_users(UserPoolId=mock_cognito_user_pool["id"],)
    assert cognito_users["Users"][0]["Username"] == email_address


@pytest.mark.integration
def test_register_user_raises_sql_exception(
    initialize_factories_session, test_db_session, mock_cognito, mock_cognito_user_pool, monkeypatch
):
    active_directory_id = "mock-auth-id"

    def mock_create_cognito_account(*args, **kwargs):
        return active_directory_id

    monkeypatch.setattr(users_util, "create_cognito_account", mock_create_cognito_account)

    # Test DB failure
    # insert a User already containing the auth_id, forcing a unique key error
    UserFactory.create(active_directory_id=active_directory_id)

    with pytest.raises(SQLAlchemyError):
        users_util.register_user(
            test_db_session,
            mock_cognito_user_pool["client_id"],
            fake.email(domain="example.com"),
            fake.password(length=12),
            cognito_client=mock_cognito,
        )
