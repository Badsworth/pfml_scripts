from datetime import datetime

import connexion
from werkzeug.exceptions import Unauthorized

import massgov.pfml.api.app as app
import massgov.pfml.api.models.applications.requests as application_request_model
import massgov.pfml.api.services.applications as applications_service
import massgov.pfml.util.logging
from massgov.pfml.api.authorization.flask import CREATE, EDIT, READ, can, ensure
from massgov.pfml.api.models.applications.responses import (
    ApplicationResponse,
    ApplicationUpdateResponse,
)
from massgov.pfml.api.services.fineos_actions import send_to_fineos
from massgov.pfml.db.models.applications import Application
from massgov.pfml.util.sqlalchemy import get_or_404

logger = massgov.pfml.util.logging.get_logger(__name__)


def application_get(application_id):
    with app.db_session() as db_session:
        existing_application = get_or_404(db_session, Application, application_id)

        ensure(READ, existing_application)
        application_response = ApplicationResponse.from_orm(existing_application)

    return application_response.dict()


def applications_get():
    with app.db_session() as db_session:
        applications = db_session.query(Application).all()

    filtered_applications = filter(lambda a: can(READ, a), applications)

    return list(
        map(
            lambda application: ApplicationResponse.from_orm(application).dict(),
            filtered_applications,
        )
    )


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

    return ApplicationResponse.from_orm(application).dict()


def applications_update(application_id):
    body = connexion.request.json

    with app.db_session() as db_session:
        existing_application = get_or_404(db_session, Application, application_id)

    ensure(EDIT, existing_application)
    (application_request, errors_and_warnings) = application_request_model.validate(body)

    if application_request is not None and len(errors_and_warnings) == 0:
        with app.db_session() as db_session:
            applications_service.update_from_request(
                db_session, application_request, existing_application
            )

        return (
            ApplicationUpdateResponse(
                code="200",
                message="Application updated without errors.",
                data=ApplicationResponse.from_orm(existing_application),
            ).dict(exclude_none=True),
            200,
        )
    else:
        return (
            ApplicationUpdateResponse(
                code="400", message="Application has errors", errors=errors_and_warnings
            ).dict(exclude_none=True),
            400,
        )


def applications_submit(application_id):
    with app.db_session() as db_session:
        existing_application = get_or_404(db_session, Application, application_id)

        ensure(EDIT, existing_application)

        if send_to_fineos(existing_application, db_session):
            existing_application.completed_time = datetime.now()
            db_session.add(existing_application)

        else:
            return (
                ApplicationUpdateResponse(
                    code="503",
                    message="Application {} could not be completed, try again later".format(
                        existing_application.application_id
                    ),
                    data=ApplicationResponse.from_orm(existing_application),
                ).dict(exclude_none=True),
                503,
            )

    return (
        ApplicationUpdateResponse(
            code="201",
            message="Application {} completed without errors".format(
                existing_application.application_id
            ),
            data=ApplicationResponse.from_orm(existing_application),
        ).dict(exclude_none=True),
        201,
    )
