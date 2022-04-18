#
# PDF client - mock implementation.
#
# This implementation is intended for use in local development or in test cases. It may also be
# used in deployed environments when needed.
#

import base64
import copy
import datetime
import pathlib
from decimal import Decimal
from typing import Any, Iterable, List, Optional, Tuple, Union

import faker
import requests
from requests.models import Response

import massgov.pfml.util.logging
import massgov.pfml.util.logging.wrapper

from . import client, exception, models, pdf_client

# from .mock.field import fake_customer_no
# from .models.customer_api import ChangeRequestPeriod, ChangeRequestReason

logger = massgov.pfml.util.logging.get_logger(__name__)

# Capture calls for unit testing.
_capture: Optional[List] = None

MOCK_DOCUMENT_DATA = {
    "caseId": "",
}

TEST_IMAGE_FILE_PATH = pathlib.Path(__file__).parent / "mock_files" / "test.png"


def fake_date_of_birth(fake):
    """Generate a fake date of birth in a reproducible way."""
    return fake.date_between(datetime.date(1930, 1, 1), datetime.date(2010, 1, 1))


# def mock_document(
#     absence_id: str,
#     document_type: str = "Approval Notice",
#     file_name: str = "test.pdf",
#     description: str = "Mock File",
# ) -> dict:
#     mocked_document = copy.copy(MOCK_DOCUMENT_DATA)
#     mocked_document.update(
#         {
#             "caseId": absence_id,
#             "name": document_type,
#             "fileExtension": pathlib.Path(file_name).suffix.lower(),
#             "originalFilename": file_name,
#             "description": description,
#         }
#     )

#     return mocked_document


class MockPDFClient(client.AbstractPDFClient):
    """Mock PDF API client that returns fake responses."""

    def __init__(
        self,
        # mock_eforms: Iterable[EForm] = MOCK_EFORMS,
    ):
        pass
        # self.mock_eforms = mock_eforms

    # def read_employer(self, employer_fein: str) -> models.OCOrganisation:
    #     _capture_call("read_employer", None, employer_fein=employer_fein)


massgov.pfml.util.logging.wrapper.log_all_method_calls(MockPDFClient, logger)


def start_capture():
    """Start capturing API calls made via MockPDFClient."""
    global _capture
    _capture = []


def _capture_call(method_name, user_id, **args):
    """Record the name and arguments of an API call."""
    global _capture
    if _capture is not None:
        _capture.append((method_name, user_id, args))


def get_capture():
    """Return the list of API calls captured since start_capture() was called."""
    global _capture
    return _capture
