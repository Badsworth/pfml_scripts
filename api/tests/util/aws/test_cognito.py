import uuid

import boto3
import moto
import pytest


@moto.mock_cognitoidp()
def test_create_cognito_leave_admin_account(test_db_session):
    import massgov.pfml.util.aws.cognito as main

    main.db_session_raw = test_db_session

    conn = boto3.client("cognito-idp", "us-east-1")
    user_pool_id = conn.create_user_pool(PoolName=str(uuid.uuid4()))["UserPool"]["Id"]

    # Moto will not return a 'sub' attribute so we expect this error
    with pytest.raises(Exception, match="Cognito did not return an ID for the user!"):
        main.create_cognito_leave_admin_account("test@test.com", "1234567", user_pool_id)
    users = conn.list_users(UserPoolId=user_pool_id,)

    assert users["Users"][0]["Username"] == "test@test.com"
