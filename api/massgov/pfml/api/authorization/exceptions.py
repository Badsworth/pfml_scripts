from werkzeug.exceptions import Forbidden

import massgov.pfml.api.util.response as response_util
from massgov.pfml.api.validation.exceptions import ValidationErrorDetail


class NotAuthorizedForAccess(Forbidden):
    def __init__(
        self,
        status_code=Forbidden,
        description="User is not authorized for access",
        error_type="not_authorized_for_access",
        data=None,
    ):
        self.status_code = status_code
        self.description = description
        self.error_type = error_type
        self.data = data

    def to_api_response(self):
        return response_util.error_response(
            status_code=self.status_code,
            message=self.description,
            errors=[ValidationErrorDetail(message=self.description, type=self.error_type)],
            data=self.data,
        ).to_api_response()
