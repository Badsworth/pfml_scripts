import faker
import pytest

from massgov.pfml.db.models.employees import User
from massgov.pfml.util.users import register_user

fake = faker.Faker()


@pytest.mark.integration
def test_register_user_success(test_db_session, mock_cognito, mock_cognito_user_pool):
    email_address = fake.email(domain="example.com")

    user = register_user(
        test_db_session,
        email_address,
        fake.password(length=12),
        mock_cognito_user_pool["client_id"],
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
