from datetime import datetime, timedelta

import pytest
from flask import g
from jose import jws, jwt
from jose.constants import ALGORITHMS
from jose.exceptions import JWTError

import massgov.pfml.api.authentication as authentication


@pytest.fixture(scope="session")
def auth_token_unit(auth_claims_unit, auth_private_key):
    encoded = jwt.encode(auth_claims_unit, auth_private_key, algorithm=ALGORITHMS.RS256)
    return encoded


@pytest.fixture(scope="session")
def auth_token_with_no_exp(auth_private_key, auth_claims_unit):
    auth_claims = auth_claims_unit.copy()
    auth_claims.pop("exp")

    encoded = jwt.encode(auth_claims, auth_private_key, algorithm=ALGORITHMS.RS256)
    return encoded


@pytest.fixture(scope="session")
def auth_token_with_no_sub(auth_private_key, auth_claims_unit):
    auth_claims = auth_claims_unit.copy()
    auth_claims.pop("sub")

    encoded = jwt.encode(auth_claims, auth_private_key, algorithm=ALGORITHMS.RS256)
    return encoded


@pytest.fixture(scope="session")
def auth_token_expired(auth_private_key, auth_claims_unit):
    auth_claims = auth_claims_unit.copy()

    exp = datetime.now() - timedelta(days=1)
    auth_claims["exp"] = exp

    encoded = jwt.encode(auth_claims, auth_private_key, algorithm=ALGORITHMS.RS256)
    return encoded


@pytest.fixture(scope="session")
def auth_token_invalid_user_id(auth_private_key, auth_claims_unit):
    auth_claims = auth_claims_unit.copy()

    auth_claims["sub"] = "foo"
    encoded = jwt.encode(auth_claims, auth_private_key, algorithm=ALGORITHMS.RS256)
    return encoded


@pytest.fixture
def auth_token_alg_none(auth_claims):
    auth_claims["exp"] = (datetime.now() + timedelta(days=1)).timestamp()

    key = {"kid": "1234example=", "alg": "none"}

    encoded_header = jws._encode_header(key)
    encoded_payload = jws._encode_payload(auth_claims)

    signature = "".encode("utf-8")

    return b".".join([encoded_header, encoded_payload, signature]).decode("utf-8")


@pytest.fixture
def auth_token_alg_hs256(auth_claims):
    auth_claims["exp"] = (datetime.now() + timedelta(days=1)).timestamp()

    key = {"kid": "1234example=", "alg": "RS256"}

    encoded_header = jws._encode_header(key)
    encoded_payload = jws._encode_payload(auth_claims)

    signature = "".encode("utf-8")

    return b".".join([encoded_header, encoded_payload, signature]).decode("utf-8")


def test_decode_cognito_token_success(set_auth_public_keys, auth_claims_unit, auth_token_unit):
    decoded = authentication._decode_cognito_token(auth_token_unit)

    assert decoded == auth_claims_unit


def test_decode_cognito_token_invalid_key(monkeypatch, auth_token_unit):
    pub_key = {
        "keys": [
            {
                "alg": "RS256",
                "e": "AQAB",
                "kid": "9fb36b80-d4d4-484d-afff-fd8efdd3a83c",
                "kty": "RSA",
                "n": "tyg_ywBEcanke5ZuBdz94fUcdPi7MgQLwLNtASF6kqdLBuiNqYMfBYYyaZJP7s1aSOEFS74Tc1-8UtdpmBEfTbqi_sKIGGWdLe_B9EKSzU7wx8KSXgfWGnl12y3ph4JI0M7_tPUzBnyu2ir0BxXMdcL5xDk5FlUKqhAlZAGcPYU",
                "use": "sig",
            }
        ]
    }
    monkeypatch.setattr(authentication, "public_keys", pub_key)
    with pytest.raises(JWTError, match="Signature verification failed."):
        authentication._decode_cognito_token(auth_token_unit)


def test_decode_cognito_token_without_public_key(monkeypatch, auth_token_unit):
    pub_key = {"keys": []}
    monkeypatch.setattr(authentication, "public_keys", pub_key)
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

        if g.current_user.user_id:
            assert g.current_user.sub_id == user.sub_id
        else:
            assert g.current_user.active_directory_id == user.sub_id
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


def test_decode_cognito_token_rejects_alg_none(set_auth_public_keys, auth_token_alg_none):
    with pytest.raises(JWTError, match=r"The specified alg value is not allowed.*"):
        authentication._decode_cognito_token(auth_token_alg_none)


def test_decode_cognito_token_rejects_alg_hs256(set_auth_public_keys, auth_token_alg_hs256):
    with pytest.raises(JWTError, match=r"The specified alg value is not allowed.*"):
        authentication._decode_cognito_token(auth_token_alg_hs256)


def test_endpoint_rejects_token_with_alg_none(client, app, user, auth_token_alg_none):
    with app.app.test_request_context("/v1/users/current"):
        response = client.get(
            "/v1/users/current", headers={"Authorization": f"Bearer {auth_token_alg_none}"}
        )

        assert not hasattr(g, "current_user")
        assert response.status_code == 401


def test_endpoint_rejects_token_with_alg_hs256(client, app, user, auth_token_alg_hs256):
    with app.app.test_request_context("/v1/users/current"):
        response = client.get(
            "/v1/users/current", headers={"Authorization": f"Bearer {auth_token_alg_hs256}"}
        )

        assert not hasattr(g, "current_user")
        assert response.status_code == 401
