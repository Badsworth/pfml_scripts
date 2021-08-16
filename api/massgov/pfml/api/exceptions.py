from werkzeug.exceptions import NotFound

import massgov.pfml.api.util.response as response_util
from massgov.pfml.api.validation.exceptions import IssueType, ValidationErrorDetail


# TODO (API-1811): Consolidate exception handling files
class ObjectNotFound(NotFound):
    status_code = NotFound

    def __init__(
        self, description="Object not found", data=None,
    ):
        self.description = description
        self.data = data

    def to_api_response(self):
        return response_util.error_response(
            status_code=self.status_code,
            message=self.description,
            errors=[
                ValidationErrorDetail(message=self.description, type=IssueType.object_not_found)
            ],
            data=self.data,
        ).to_api_response()
