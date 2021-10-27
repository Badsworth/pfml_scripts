import connexion
from werkzeug.exceptions import NotFound

import massgov.pfml.api.app as app
import massgov.pfml.api.util.response as response_util
import massgov.pfml.util.logging
from massgov.pfml.api.models.flags.requests import FlagRequest
from massgov.pfml.api.models.flags.responses import FlagResponse
from massgov.pfml.db.models.flags import LkFeatureFlag

logger = massgov.pfml.util.logging.get_logger(__name__)

##########################################
# Handlers
##########################################


def flag_get(name):
    with app.db_session() as db_session:
        flag = db_session.query(LkFeatureFlag).filter_by(name=name).one_or_none()
        if flag is None:
            raise NotFound(
                description="Could not find {} with name {}".format(LkFeatureFlag.__name__, name)
            )
        response = response_util.success_response(
            data=FlagResponse.from_orm(flag).dict(), message="Successfully retrieved flag",
        ).to_api_response()
        response.headers["Cache-Control"] = "max-age=300"
        return response


def flag_get_logs(name):
    with app.db_session() as db_session:
        logs = db_session.query(LkFeatureFlag).filter_by(name=name).one().logs()
        if not logs:
            raise NotFound(description="Could not find logs for {} feature flag".format(name))
        response = response_util.success_response(
            data=[FlagResponse.from_orm(flag_log).dict() for flag_log in logs],
            message="Successfully retrieved flag",
        ).to_api_response()
        return response


def flags_get():
    with app.db_session() as db_session:
        response = response_util.success_response(
            data=[FlagResponse.from_orm(flag).dict() for flag in db_session.query(LkFeatureFlag)],
            message="Successfully retrieved flags",
        ).to_api_response()
        response.headers["Cache-Control"] = "max-age=300"
        return response


# TODO change to post ?
def flags_patch(name):
    body = FlagRequest.parse_obj(connexion.request.json)

    with app.db_session() as db_session:
        flag = db_session.query(LkFeatureFlag).filter_by(name=name).one_or_none()
        if flag is None:
            raise NotFound(
                description="Could not find {} with name {}".format(LkFeatureFlag.__name__, name)
            )

        for key in body.__fields_set__:
            value = getattr(body, key)
            setattr(flag, key, value)

    return response_util.success_response(
        message="Successfully updated feature flag", data=FlagRequest.from_orm(flag).dict()
    ).to_api_response()
