#
# Tests for pfml.split.
#

import json
import flask
import pfml
import pfml.split

app = pfml.create_app()

def test_split_ok():
    client = app.app.test_client()
    response = client.get("/v1/split?message=abcd+efghij")
    assert response.status_code == 200
    data = json.loads(response.data.decode("utf-8", "replace"))
    assert data == {"words": ["abcd", "efghij"]}

def test_split_too_long():
    client = app.app.test_client()
    response = client.get("/v1/split?message=" + 100 * "a+")
    assert response.status_code == 400

def test_split_missing_parameter():
    client = app.app.test_client()
    response = client.get("/v1/split")
    assert response.status_code == 400

def test_split_extra_parameter():
    client = app.app.test_client()
    response = client.get("/v1/split?message=xyz&q=123")
    assert response.status_code == 400

def test_split_into_words():
    assert pfml.split.split_into_words("abc def ghi") == ["abc", "def", "ghi"]
