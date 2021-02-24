from datetime import datetime, timedelta

import pytest
from flask import g
from jose import jwt
from jose.exceptions import JWTError

import massgov.pfml.api.authentication as authentication


@pytest.fixture(scope="session")
def auth_token_unit(auth_claims_unit, auth_key):
    encoded = jwt.encode(auth_claims_unit, auth_key)
    return encoded


@pytest.fixture(scope="session")
def auth_token_with_no_exp(auth_key, auth_claims_unit):
    auth_claims = auth_claims_unit.copy()
    auth_claims.pop("exp")

    encoded = jwt.encode(auth_claims, auth_key)
    return encoded


@pytest.fixture(scope="session")
def auth_token_with_no_sub(auth_key, auth_claims_unit):
    auth_claims = auth_claims_unit.copy()
    auth_claims.pop("sub")

    encoded = jwt.encode(auth_claims, auth_key)
    return encoded


@pytest.fixture(scope="session")
def auth_token_expired(auth_key, auth_claims_unit):
    auth_claims = auth_claims_unit.copy()

    exp = datetime.now() - timedelta(days=1)
    auth_claims["exp"] = exp

    encoded = jwt.encode(auth_claims, auth_key)
    return encoded


@pytest.fixture(scope="session")
def auth_token_invalid_user_id(auth_key, auth_claims_unit):
    auth_claims = auth_claims_unit.copy()

    auth_claims["sub"] = "foo"
    encoded = jwt.encode(auth_claims, auth_key)
    return encoded


def test_decode_cognito_token_success(set_auth_public_keys, auth_claims_unit, auth_token_unit):
    decoded = authentication._decode_cognito_token(auth_token_unit)

    assert decoded == auth_claims_unit


def test_decode_cognito_token_invalid_key(monkeypatch, auth_token_unit):
    monkeypatch.setattr(authentication, "public_keys", "nope")
    with pytest.raises(JWTError, match="Signature verification failed."):
        authentication._decode_cognito_token(auth_token_unit)


def test_decode_cognito_token_no_exp(set_auth_public_keys, auth_token_with_no_exp):
    with pytest.raises(JWTError, match='missing required key "exp" among claims'):
        authentication._decode_cognito_token(auth_token_with_no_exp)


def test_decode_cognito_token_no_sub(set_auth_public_keys, auth_token_with_no_sub):
    with pytest.raises(JWTError, match='missing required key "sub" among claims'):
        authentication._decode_cognito_token(auth_token_with_no_sub)


def test_decode_cognito_token_expired(set_auth_public_keys, auth_token_expired):
    with pytest.raises(JWTError, match="Signature has expired."):
        authentication._decode_cognito_token(auth_token_expired)


@pytest.mark.integration
def test_without_token(client, auth_token):
    response = client.get("/v1/status")
    response_body = response.get_json()

    assert response.status_code == 200
    assert response_body["message"] == "Service healthy"


@pytest.mark.integration
def test_current_user_is_set_successfully(client, app, user, auth_token):
    with app.app.test_request_context("/v1/users/current"):
        response = client.get(
            "/v1/users/current", headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert g.current_user.active_directory_id == user.active_directory_id
        assert g.current_user.user_id == user.user_id
        assert response.status_code == 200


@pytest.mark.integration
def test_claims_with_invalid_user_id(client, app, user, auth_token_invalid_user_id):
    with app.app.test_request_context("/v1/users/current"):
        response = client.get(
            "/v1/users/current", headers={"Authorization": f"Bearer {auth_token_invalid_user_id}"}
        )

        assert not hasattr(g, "current_user")
        assert response.status_code == 401
