from typing import Callable, Dict, Generator, List, Optional
from urllib.parse import urljoin

import requests

from massgov.pfml.util.pydantic import PydanticBaseModel

from .exception import FormstackBadResponse, FormstackClientError

FORMSTACK_API_URL = "https://www.formstack.com/api/v2"


class SubmissionKeyValuePair(PydanticBaseModel):
    field: str
    value: str


class Submission(PydanticBaseModel):
    submission_id: str
    data: List[SubmissionKeyValuePair] = []


class SubmissionsData:
    """
    Class to provide an iterable of Formstack submissions for a given form
    """

    url: str
    params: Dict

    def __init__(self, url: str, params: Dict, request_method: Callable):
        self.url = url
        self.params = params
        self.request_method = request_method

    def build_submission(self, submission_data: Dict) -> Submission:
        submission = {"submission_id": submission_data["id"], "data": []}

        for _key, value in submission_data["data"].items():
            key_value_pair = {
                "field": value["field"],
                "value": value["flat_value"],
            }
            submission["data"].append(SubmissionKeyValuePair(**key_value_pair))

        return Submission(**submission)

    def __iter__(self) -> Generator:
        self.params["per_page"] = 25
        current_page = 1
        while True:
            self.params["page"] = current_page
            current_results = self.request_method("GET", self.url, self.params).json()

            if not current_results["submissions"]:
                break
            for result in current_results["submissions"]:
                yield self.build_submission(result)
            current_page += 1


class FormstackClient:
    """
    Client for retrieving forms and form data via the Formstack API
    """

    formstack_api_key: str

    def __init__(self, formstack_api_key):
        self.session = requests.Session()
        self.session.headers.update({"Authorization": f"Bearer {formstack_api_key}"})

    def _request(self, method: str, url: str, params: Optional[Dict] = None) -> requests.Response:
        full_url = urljoin(FORMSTACK_API_URL, url)

        try:
            response = self.session.request(method, full_url, params=params, timeout=10)
            response.raise_for_status()
        except requests.exceptions.HTTPError:
            raise FormstackBadResponse(
                requests.codes.ok, response.status_code  # pylint: disable=no-member
            )
        except requests.exceptions.RequestException as request_error:
            raise FormstackClientError(cause=request_error)

        return response

    def get_forms(self) -> List[Dict]:
        forms_url = "/form.json"

        response = self._request("GET", forms_url)
        return response.json()["forms"]

    def get_submissions(
        self,
        form_id: str,
        min_time: Optional[str] = None,
        max_time: Optional[str] = None,
        data: bool = True,
        expand_data: bool = False,
    ) -> SubmissionsData:
        submissions_url = f"/form/{form_id}/submission.json"
        params = {
            "min_time": min_time,
            "max_time": max_time,
            "data": str(data).lower(),
            "expand_data": str(expand_data).lower(),
        }
        return SubmissionsData(submissions_url, params, self._request)

    def get_submission(self, submission_id: str) -> Submission:
        submission_url = f"/submission/{submission_id}"

        response = self._request("GET", submission_url).json()

        submission = {"submission_id": response["id"], "data": []}
        for key_value_pair in response["data"]:
            submission["data"].append(SubmissionKeyValuePair(**key_value_pair))

        return Submission(**submission)
