import connexion
from werkzeug.exceptions import NotFound, Unauthorized

import massgov.pfml.api.app as app
import massgov.pfml.api.util.response as response_util
import massgov.pfml.util.logging
from massgov.pfml.api.authorization.flask import EDIT, READ, ensure
from massgov.pfml.api.models.flags.requests import FlagRequest
from massgov.pfml.api.models.flags.responses import FlagLogResponse, FlagResponse
from massgov.pfml.db.models.employees import AzurePermission
from massgov.pfml.db.models.flags import (
    FeatureFlag,
    FeatureFlagValue,
    LkFeatureFlag,
    UserAzureFeatureFlagLog,
)

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
        response = response_util.success_response(
            data=[
                FlagLogResponse(
                    given_name=log.given_name,
                    family_name=log.family_name,
                    created_at=log.created_at,
                    enabled=log.feature_flag_value.enabled,
                    name=log.feature_flag_value.name,
                    start=log.feature_flag_value.start,
                    end=log.feature_flag_value.end,
                    options=log.feature_flag_value.options,
                ).__dict__
                for log in logs
            ],
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


def flags_post(name):
    azure_user = app.azure_user()
    # This should not ever be the case.
    if azure_user is None:
        raise Unauthorized
    ensure(READ, azure_user)
    # There's a single API endpoint to set feature flags and maintenance is
    # the only feature flag right now. This will need to change if more feature
    # flags are set from the Admin Portal. This will disallow other feature
    # flags from being unset until the decision is made.
    if name == FeatureFlag.MAINTENANCE.name:
        ensure(EDIT, AzurePermission.MAINTENANCE_EDIT)
    else:
        raise Unauthorized
    body = FlagRequest.parse_obj(connexion.request.json)

    with app.db_session() as db_session:
        flag = db_session.query(LkFeatureFlag).filter_by(name=name).one_or_none()
        if flag is None:
            raise NotFound(
                description="Could not find {} with name {}".format(LkFeatureFlag.__name__, name)
            )
        feature_flag_value = FeatureFlagValue()
        feature_flag_value.feature_flag = flag

        for key in body.__fields_set__:
            value = getattr(body, key)
            setattr(feature_flag_value, key, value)
        db_session.add(feature_flag_value)
        db_session.flush()
        log = UserAzureFeatureFlagLog(
            azure_feature_flag_value_id=feature_flag_value.feature_flag_value_id,
            email_address=azure_user.email_address,
            sub_id=azure_user.sub_id,
            family_name=azure_user.first_name,
            given_name=azure_user.last_name,
            action="INSERT",
        )
        db_session.add(log)
        db_session.commit()

    return response_util.success_response(
        message="Successfully updated feature flag",
        data=FlagRequest.from_orm(flag).dict(),
        status_code=201,
    ).to_api_response()
