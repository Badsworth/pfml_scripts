from datetime import datetime, timedelta

import pytest
from jose import jwt
from jose.exceptions import JWTError

import massgov.pfml.api.authentication as authentication


@pytest.fixture
def claims():
    claims = {"a": "b", "exp": datetime.now() + timedelta(days=1)}
    return claims


@pytest.fixture
def test_key():
    hmac_key = {
        "kty": "oct",
        "kid": "018c0ae5-4d9b-471b-bfd6-eef314bc7037",
        "use": "sig",
        "alg": "HS256",
        "k": "hJtXIZ2uSN5kbQfbtTNWbpdmhkV8FJG-Onbc6mxCcYg",
    }

    return hmac_key


@pytest.fixture
def test_token(claims, test_key):

    encoded = jwt.encode(claims, test_key)
    return encoded


@pytest.fixture
def test_token_with_no_exp(test_key):

    encoded = jwt.encode({"a": "b"}, test_key)
    return encoded


@pytest.fixture
def test_token_expired(test_key):
    exp = datetime.now() - timedelta(days=1)
    expired_claims = {"a": "b", "exp": exp}

    encoded = jwt.encode(expired_claims, test_key)
    return encoded


def test_decode_cognito_token_success(monkeypatch, app, claims, test_token, test_key):
    monkeypatch.setattr(authentication, "public_keys", test_key)
    decoded = authentication._decode_cognito_token(test_token)

    assert decoded == claims


def test_decode_cognito_token_invalid_key(monkeypatch, claims, test_token):
    monkeypatch.setattr(authentication, "public_keys", "nope")
    with pytest.raises(JWTError, match="Signature verification failed."):
        authentication._decode_cognito_token(test_token)


def test_decode_cognito_token_no_exp(monkeypatch, test_token_with_no_exp, test_key):
    monkeypatch.setattr(authentication, "public_keys", test_key)
    with pytest.raises(JWTError, match='missing required key "exp" among claims'):
        authentication._decode_cognito_token(test_token_with_no_exp)


def test_decode_cognito_token_expired(monkeypatch, test_token_expired, test_key):
    monkeypatch.setattr(authentication, "public_keys", test_key)
    with pytest.raises(JWTError, match="Signature has expired."):
        authentication._decode_cognito_token(test_token_expired)


def test_without_token(monkeypatch, client, test_key, test_token):
    monkeypatch.setattr(authentication, "public_keys", test_key)

    response = client.get("/v1/status")
    response_body = response.get_json()

    assert response.status_code == 200
    assert response_body["status"] == "ok"
