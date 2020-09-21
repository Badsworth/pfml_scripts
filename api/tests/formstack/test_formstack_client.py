import pytest
import requests

from massgov.pfml.formstack.exception import FormstackBadResponse
from massgov.pfml.formstack.formstack_client import FormstackClient, Submission, SubmissionsData


class MockResponse:
    """ Mocks a requests.Response """

    def __init__(self, response_to_return, status_code_to_return):
        self.status_code = status_code_to_return
        self.response_to_return = response_to_return
        self.reason = "fake reason to support raise_for_status"
        self.url = "fake url to support raise_for_status"

    def json(self):
        return self.response_to_return

    def raise_for_status(self):
        requests.Response.raise_for_status(self)


class MockHeaders:
    """ Mocks a requests.Session.headers object """

    def __init__(self):
        pass

    def update(self, headers):
        pass


class MockSession:
    """ Mocks a request_oauthlib.OAuth2Session() """

    def __init__(self, mock_request):
        self.mock_request = mock_request
        self.headers = MockHeaders()

    def request(self, method, url, params, timeout):
        return self.mock_request(method=method, url=url, params=params, timeout=timeout)


def mock_get_secret_from_env(*args):
    return '{"client_id": "fake_id"}'


def test_get_forms_success(monkeypatch):
    """ Asserts a 200 is returned with forms data when get_forms is called """

    def mock_request(*args, **kwargs):
        return MockResponse(
            {"forms": [{"mock_key": "mock_response"}]}, requests.codes.ok
        )  # pylint: disable=no-member

    def mock_session(*args, **kwargs):
        return MockSession(mock_request)

    monkeypatch.setattr("massgov.pfml.formstack.formstack_client.OAuth2Session", mock_session)
    monkeypatch.setattr(
        "massgov.pfml.formstack.formstack_client.get_secret_from_env", mock_get_secret_from_env
    )
    client = FormstackClient()

    result = client.get_forms()

    assert result[0]["mock_key"] == "mock_response"


def test_get_forms_bad_resp(monkeypatch):
    """ Asserts that a 500 is raised as a FormstackBadResponse with the correct formatting when calling get_forms """

    def mock_request(*args, **kwargs):
        return MockResponse({}, requests.codes.server_error)  # pylint: disable=no-member

    def mock_session(*args, **kwargs):
        return MockSession(mock_request)

    monkeypatch.setattr("massgov.pfml.formstack.formstack_client.OAuth2Session", mock_session)
    monkeypatch.setattr(
        "massgov.pfml.formstack.formstack_client.get_secret_from_env", mock_get_secret_from_env
    )
    client = FormstackClient()

    with pytest.raises(FormstackBadResponse, match="expected 200, but got 500"):
        assert client.get_forms()


def test_get_submissions_success(monkeypatch):
    """ Asserts a 200 is returned with an iterable SubmissionsData object when get_submissions is called """

    def mock_request(*args, **kwargs):
        fake_submissions_resp = {
            "submissions": [
                {
                    "id": "fake_id",
                    "data": {"field_id": {"field": "fake_field", "flat_value": "fake_value"}},
                }
            ]
        }
        assert kwargs["params"]["data"] == "true"
        assert kwargs["params"]["expand_data"] == "false"
        return MockResponse(fake_submissions_resp, requests.codes.ok)  # pylint: disable=no-member

    def mock_session(*args, **kwargs):
        return MockSession(mock_request)

    monkeypatch.setattr("massgov.pfml.formstack.formstack_client.OAuth2Session", mock_session)
    monkeypatch.setattr(
        "massgov.pfml.formstack.formstack_client.get_secret_from_env", mock_get_secret_from_env
    )
    client = FormstackClient()
    result = client.get_submissions("fake_form_id")

    assert type(result) is SubmissionsData
    i = iter(result)
    submission = next(i)
    assert type(submission) is Submission
    submission_dict = submission.dict()
    assert submission_dict["submission_id"] == "fake_id"
    assert submission_dict["data"][0]["field"] == "fake_field"
    assert submission_dict["data"][0]["value"] == "fake_value"


def test_get_submissions_bad_resp(monkeypatch):
    """
    Asserts that an iterable SubmissionsData object is returned and a 500 is raised as a FormstackBadResponse
    with the correct formatting when calling get_submissions
    """

    def mock_request(*args, **kwargs):
        return MockResponse({}, requests.codes.server_error)  # pylint: disable=no-member

    def mock_session(*args, **kwargs):
        return MockSession(mock_request)

    monkeypatch.setattr("massgov.pfml.formstack.formstack_client.OAuth2Session", mock_session)
    monkeypatch.setattr(
        "massgov.pfml.formstack.formstack_client.get_secret_from_env", mock_get_secret_from_env
    )
    client = FormstackClient()

    result = client.get_submissions("fake_form_id")
    assert type(result) is SubmissionsData

    i = iter(result)
    with pytest.raises(FormstackBadResponse, match="expected 200, but got 500"):
        assert next(i)


def test_get_submission_success(monkeypatch):
    """ Asserts a 200 is returned with data of type Submission when get_submission is called """

    def mock_request(*args, **kwargs):
        fake_submission_resp = {
            "id": "fake_id",
            "data": [{"field": "fake_field", "value": "fake_value"}],
        }
        return MockResponse(fake_submission_resp, requests.codes.ok)  # pylint: disable=no-member

    def mock_session(*args, **kwargs):
        return MockSession(mock_request)

    monkeypatch.setattr("massgov.pfml.formstack.formstack_client.OAuth2Session", mock_session)
    monkeypatch.setattr(
        "massgov.pfml.formstack.formstack_client.get_secret_from_env", mock_get_secret_from_env
    )
    client = FormstackClient()
    result = client.get_submission("fake_submission_id")
    assert type(result) is Submission
    result_dict = result.dict()
    assert result_dict["submission_id"] == "fake_id"
    assert result_dict["data"][0]["field"] == "fake_field"
    assert result_dict["data"][0]["value"] == "fake_value"


def test_get_submission_bad_resp(monkeypatch):
    """
    Asserts that a 500 is raised as a FormstackBadResponse with the correct formatting when
    calling get_submission
    """

    def mock_request(*args, **kwargs):
        return MockResponse({}, requests.codes.server_error)  # pylint: disable=no-member

    def mock_session(*args, **kwargs):
        return MockSession(mock_request)

    monkeypatch.setattr("massgov.pfml.formstack.formstack_client.OAuth2Session", mock_session)
    monkeypatch.setattr(
        "massgov.pfml.formstack.formstack_client.get_secret_from_env", mock_get_secret_from_env
    )
    client = FormstackClient()

    with pytest.raises(FormstackBadResponse, match="expected 200, but got 500"):
        assert client.get_submission("fake_submission_id")
