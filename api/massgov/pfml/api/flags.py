from werkzeug.exceptions import NotFound

import massgov.pfml.api.app as app
import massgov.pfml.api.util.response as response_util
from massgov.pfml.api.models.flags.responses import FlagResponse
from massgov.pfml.db.models.flags import FeatureFlag, LkFeatureFlag

##########################################
# Handlers
##########################################


def flag_get(name):
    with app.db_session() as db_session:
        try:
            flag = FeatureFlag.get_instance(db_session, description=name)
        except KeyError:
            raise NotFound(
                description="Could not find {} with name {}".format(LkFeatureFlag.__name__, name)
            )
        response = response_util.success_response(
            data=FlagResponse.from_orm(flag).dict(),
            message="Successfully retrieved flag",
        ).to_api_response()
        response.headers["Cache-Control"] = "max-age=300"
        return response


def flags_get():
    with app.db_session() as db_session:
        response = response_util.success_response(
            data=[FlagResponse.from_orm(flag).dict() for flag in db_session.query(LkFeatureFlag)],
            message="Successfully retrieved flags",
        ).to_api_response()
        response.headers["Cache-Control"] = "max-age=300"
        return response
