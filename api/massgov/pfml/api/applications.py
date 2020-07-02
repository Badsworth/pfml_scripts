from datetime import datetime
from typing import Optional

import connexion
from pydantic import UUID4

import massgov.pfml.api.app as app
import massgov.pfml.api.models.applications.requests as application_request_model
import massgov.pfml.api.services.applications as applications_service
from massgov.pfml.api.models.applications.responses import (
    ApplicationResponse,
    ApplicationUpdateResponse,
)
from massgov.pfml.db.models.applications import Application
from massgov.pfml.util.pydantic import PydanticBaseModel
from massgov.pfml.util.sqlalchemy import get_or_404


def application_get(application_id):
    with app.db_session() as db_session:
        existing_application = get_or_404(db_session, Application, application_id)

        application_response = ApplicationResponse.from_orm(existing_application)

    return application_response.dict()


class ApplicationSearchResult(PydanticBaseModel):
    application_id: UUID4
    application_nickname: Optional[str]


def applications_get():
    applications = []

    with app.db_session() as db_session:
        applications = db_session.query(
            Application.application_id, Application.nickname.label("application_nickname")
        ).all()

    return list(
        map(
            lambda query_result: ApplicationSearchResult.construct(**query_result._asdict()).dict(),
            applications,
        )
    )


def applications_start():
    application = Application()
    application.start_time = datetime.now()
    application.updated_time = datetime.now()

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
