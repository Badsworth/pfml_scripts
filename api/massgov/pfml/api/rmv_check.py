import connexion

import massgov.pfml.api.app as app
import massgov.pfml.api.util.response as response_util
from massgov.pfml.api.authorization.flask import CREATE, ensure
from massgov.pfml.api.config import RMVCheckBehavior
from massgov.pfml.api.services.rmv_check import (
    RMVCheckRequest,
    RMVCheckResponse,
    handle_rmv_check_request,
    make_response_from_rmv_check,
)
from massgov.pfml.db.models.applications import RMVCheck
from massgov.pfml.rmv.client import RmvClient


def is_test_record(request: RMVCheckRequest) -> bool:
    test_records = {
        ("Steve", "Tester"),
        ("Charles", "Presley"),
        ("Willis", "Sierra"),
        ("Lilibeth", "Perozo"),
        ("Roseangela", "Leite Da Silva"),
        ("Vida", "King"),
        ("John", "Pinkham"),
        ("Jonathan", "Day"),
        ("Linda", "Bellabe"),
    }

    return (request.first_name, request.last_name) in test_records


def is_mocked(rmv_mocking_behavior: RMVCheckBehavior, request: RMVCheckRequest) -> bool:
    return rmv_mocking_behavior is RMVCheckBehavior.MOCK or (
        rmv_mocking_behavior is RMVCheckBehavior.PARTIAL_MOCK and not is_test_record(request)
    )


def rmv_check_post():
    # Check if requester has access, else bounce back
    ensure(CREATE, RMVCheck)

    request = RMVCheckRequest.parse_obj(connexion.request.json)

    with app.db_session() as db_session:
        rmv_mocking_behavior = app.get_app_config().rmv_check_behavior
        if is_mocked(rmv_mocking_behavior, request):
            if app.get_app_config().rmv_check_mock_success:
                final_response = RMVCheckResponse(
                    verified=True, description="Verification check passed."
                )
            else:
                final_response = RMVCheckResponse(
                    verified=False,
                    description="Verification failed because no record could be found for given ID information.",
                )
        else:
            client = RmvClient()
            complete_rmv_check = handle_rmv_check_request(db_session, client, request)
            final_response = make_response_from_rmv_check(complete_rmv_check)

    return response_util.success_response(
        message="Completed RMV check", data=final_response.dict(),
    ).to_api_response()
