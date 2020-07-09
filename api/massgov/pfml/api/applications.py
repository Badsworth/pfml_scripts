from datetime import datetime

import connexion
from werkzeug.exceptions import Unauthorized

import massgov.pfml.api.app as app
import massgov.pfml.api.models.applications.requests as application_request_model
import massgov.pfml.api.services.applications as applications_service
from massgov.pfml.api.models.applications.responses import (
    ApplicationResponse,
    ApplicationUpdateResponse,
)
from massgov.pfml.db.models.applications import Application
from massgov.pfml.util.sqlalchemy import get_or_404


def application_get(application_id):
    with app.db_session() as db_session:
        existing_application = get_or_404(db_session, Application, application_id)

        application_response = ApplicationResponse.from_orm(existing_application)

    return application_response.dict()


def applications_get():
    with app.db_session() as db_session:
        applications = db_session.query(Application).all()

    return list(
        map(lambda application: ApplicationResponse.from_orm(application).dict(), applications)
    )


def applications_start():
    application = Application()

    now = datetime.now()
    application.start_time = now
    application.updated_time = now

    # this should always be the case at this point, but the type for
    # current_user is still optional until we require authentication
    if user := app.current_user():
        application.user = user
    else:
        raise Unauthorized

    with app.db_session() as db_session:
        db_session.add(application)

    return {"application_id": application.application_id}, 201


def applications_update(application_id):
    body = connexion.request.json

    with app.db_session() as db_session:
        existing_application = get_or_404(db_session, Application, application_id)

    (application_request, errors_and_warnings) = application_request_model.validate(body)

    if application_request is not None and len(errors_and_warnings) == 0:
        with app.db_session() as db_session:
            applications_service.update_from_request(
                db_session, application_request, existing_application
            )

        return (
            ApplicationUpdateResponse(
                code="200", message="Application updated without errors."
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

        existing_application.completed_time = datetime.now()
        db_session.add(existing_application)

    success_response = {
        "code": "201",
        "message": "Application {} completed without errors".format(
            existing_application.application_id
        ),
        "warnings": [],
        "errors": [],
    }

    return success_response, 201
