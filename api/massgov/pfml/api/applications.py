from datetime import datetime

import connexion
from werkzeug.exceptions import ServiceUnavailable, Unauthorized

import massgov.pfml.api.app as app
import massgov.pfml.api.services.applications as applications_service
import massgov.pfml.api.util.response as response_util
import massgov.pfml.util.logging
from massgov.pfml.api.authorization.flask import CREATE, EDIT, READ, can, ensure
from massgov.pfml.api.models.applications.requests import ApplicationRequestBody
from massgov.pfml.api.models.applications.responses import ApplicationResponse
from massgov.pfml.api.services.fineos_actions import send_to_fineos
from massgov.pfml.db.models.applications import Application
from massgov.pfml.util.sqlalchemy import get_or_404

logger = massgov.pfml.util.logging.get_logger(__name__)


def application_get(application_id):
    with app.db_session() as db_session:
        existing_application = get_or_404(db_session, Application, application_id)

        ensure(READ, existing_application)
        application_response = ApplicationResponse.from_orm(existing_application)

    return response_util.success_response(
        message="Successfully retrieved application", data=application_response.dict(),
    ).to_api_response()


def applications_get():
    with app.db_session() as db_session:
        applications = db_session.query(Application).all()

    filtered_applications = filter(lambda a: can(READ, a), applications)

    applications_response = list(
        map(
            lambda application: ApplicationResponse.from_orm(application).dict(),
            filtered_applications,
        )
    )
    return response_util.success_response(
        message="Successfully retrieved applications", data=applications_response
    ).to_api_response()


def applications_start():
    application = Application()

    now = datetime.now()
    application.start_time = now
    application.updated_time = now

    ensure(CREATE, application)

    # this should always be the case at this point, but the type for
    # current_user is still optional until we require authentication
    if user := app.current_user():
        application.user = user
    else:
        raise Unauthorized

    with app.db_session() as db_session:
        db_session.add(application)

    return response_util.success_response(
        message="Successfully created application",
        data=ApplicationResponse.from_orm(application).dict(),
        status_code=201,
    ).to_api_response()


def applications_update(application_id):
    body = connexion.request.json

    with app.db_session() as db_session:
        existing_application = get_or_404(db_session, Application, application_id)

    ensure(EDIT, existing_application)
    application_request = ApplicationRequestBody.parse_obj(body)

    with app.db_session() as db_session:
        applications_service.update_from_request(
            db_session, application_request, existing_application
        )

    return response_util.success_response(
        message="Application updated without errors.",
        data=ApplicationResponse.from_orm(existing_application).dict(exclude_none=True),
    ).to_api_response()


def applications_submit(application_id):
    with app.db_session() as db_session:
        existing_application = get_or_404(db_session, Application, application_id)

        ensure(EDIT, existing_application)

        if send_to_fineos(existing_application, db_session):
            existing_application.submitted_time = datetime.now()
            db_session.add(existing_application)

        else:
            return response_util.error_response(
                status_code=ServiceUnavailable,
                message="Application {} could not be submitted, try again later".format(
                    existing_application.application_id
                ),
                errors=[],
                data=ApplicationResponse.from_orm(existing_application).dict(exclude_none=True),
            ).to_api_response()

    return response_util.success_response(
        message="Application {} submitted without errors".format(
            existing_application.application_id
        ),
        data=ApplicationResponse.from_orm(existing_application).dict(exclude_none=True),
        status_code=201,
    ).to_api_response()
