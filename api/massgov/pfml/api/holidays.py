import flask

import massgov.pfml.api.util.response as response_util


# TODO API-2480 will complete this implementation
def holidays_search() -> flask.Response:
    data = [
        {"name": "New Year's Day", "date": "2022-01-01",},
        {"name": "Christmas Day", "date": "2021-12-25",},
    ]

    return response_util.success_response(message="success", data=data,).to_api_response()
