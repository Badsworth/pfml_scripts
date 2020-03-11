#
# Tests for pfml.users.users_post()
#

import json
import flask
import pfml
import pfml.users

app = pfml.create_app()

def test_valid_post():
    client = app.app.test_client()
    body = {"email": "joe@example.com", "auth_id": "00000"}
    response = client.post("/v1/users", json=body)
    assert response.status_code == 200

def test_missing_post_parameters():
    client = app.app.test_client()
    body = {"email": "joe@example.com"}
    response = client.post("/v1/users", json=body)
    assert response.status_code == 400

