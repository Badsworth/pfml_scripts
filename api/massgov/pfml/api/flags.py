import connexion
from werkzeug.exceptions import NotFound

import massgov.pfml.api.app as app
import massgov.pfml.api.util.response as response_util
from massgov.pfml.api.models.flags.requests import FlagRequest
from massgov.pfml.api.models.flags.responses import FlagResponse
from massgov.pfml.db.models.flags import Flag, FlagLog


##########################################
# Handlers
##########################################


def flag_get(name):
    with app.db_session() as db_session:
        flag = db_session.query(Flag).filter_by(name=name).one_or_none()
        if flag is None:
            raise NotFound(description="Could not find {} with name {}".format(Flag.__name__, name))
        response = response_util.success_response(
            data=FlagResponse.from_orm(flag).dict(), message="Successfully retrieved flag",
        ).to_api_response()
        response.headers["Cache-Control"] = "max-age=300"
        return response


def flag_get_logs(name):
    with app.db_session() as db_session:
        logs = (
            db_session.query(FlagLog)
            .filter_by(name=name)
            .order_by(FlagLog.flag_log_id.desc())
            .limit(10)
            .offset(1)
        )
        if logs is None:
            raise NotFound(description="Could not find {} with name {}".format(Flag.__name__, name))
        response = response_util.success_response(
            data=[FlagResponse.from_orm(flag_log).dict() for flag_log in logs],
            message="Successfully retrieved flag",
        ).to_api_response()
        return response


def flags_get():
    with app.db_session() as db_session:
        response = response_util.success_response(
            data=[FlagResponse.from_orm(flag).dict() for flag in db_session.query(Flag)],
            message="Successfully retrieved flags",
        ).to_api_response()
        response.headers["Cache-Control"] = "max-age=300"
        return response


# TODO azure authentication.
def flags_patch(name):
    body = FlagRequest.parse_obj(connexion.request.json)

    with app.db_session() as db_session:
        flag = db_session.query(Flag).filter_by(name=name).one_or_none()
        if flag is None:
            raise NotFound(description="Could not find {} with name {}".format(Flag.__name__, name))

        for key in body.__fields_set__:
            value = getattr(body, key)
            setattr(flag, key, value)

    return response_util.success_response(
        message="Successfully updated feature flag", data=FlagRequest.from_orm(flag).dict()
    ).to_api_response()
