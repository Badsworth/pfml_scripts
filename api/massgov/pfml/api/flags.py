import massgov.pfml.api.util.response as response_util
from massgov.pfml.api.models.flags.responses import FlagResponse
from massgov.pfml.util import feature_gate

##########################################
# Handlers
##########################################


def flags_get():
    flags = feature_gate.load_all()
    response = response_util.success_response(
        data=[FlagResponse.parse_obj(vars(flag)).dict() for flag in flags],
        message="Successfully retrieved flags",
    ).to_api_response()
    response.headers["Cache-Control"] = "max-age=300"
    return response
