import faker
import pytest

from massgov.pfml.util.aws.cognito import create_cognito_account

fake = faker.Faker()


def test_create_cognito_account(mock_cognito, mock_cognito_user_pool):
    email_address = fake.email(domain="example.com")

    sub = create_cognito_account(
        email_address,
        fake.password(length=12),
        mock_cognito_user_pool["client_id"],
        cognito_client=mock_cognito,
    )

    users = mock_cognito.list_users(UserPoolId=mock_cognito_user_pool["id"],)

    assert sub is not None
    assert users["Users"][0]["Username"] == email_address


@pytest.mark.integration
def test_create_verified_cognito_leave_admin_account(
    test_db_session, mock_cognito, mock_cognito_user_pool
):
    import massgov.pfml.util.aws.cognito as main

    main.db_session_raw = test_db_session

    # Moto will not return a 'sub' attribute so we expect this error
    with pytest.raises(main.CognitoSubNotFound, match="Cognito did not return an ID for the user!"):
        main.create_verified_cognito_leave_admin_account(
            test_db_session,
            "test@test.com",
            "1234567",
            cognito_user_pool_id=mock_cognito_user_pool["id"],
        )
    users = mock_cognito.list_users(UserPoolId=mock_cognito_user_pool["id"],)

    assert users["Users"][0]["Username"] == "test@test.com"


@pytest.mark.integration
def test_lookup_cognito_account_id(test_db_session, mock_cognito_user_pool):
    import massgov.pfml.util.aws.cognito as main

    main.db_session_raw = test_db_session

    # Moto will not return a 'sub' attribute so we expect this error
    with pytest.raises(main.CognitoSubNotFound, match="Cognito did not return an ID for the user!"):
        main.create_verified_cognito_leave_admin_account(
            test_db_session,
            "test@test.com",
            "1234567",
            cognito_user_pool_id=mock_cognito_user_pool["id"],
        )

    # ... the user has to be found for lookup_cognito_account_id to throw this error; a weird intersection to be sure
    with pytest.raises(main.CognitoSubNotFound, match="Cognito did not return an ID for the user!"):
        main.lookup_cognito_account_id(
            email="test@test.com", cognito_user_pool_id=mock_cognito_user_pool["id"]
        )
