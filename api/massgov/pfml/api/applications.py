from datetime import datetime
from typing import Optional

import connexion
from pydantic import UUID4
from werkzeug.exceptions import NotFound

import massgov.pfml.api.app as app
from massgov.pfml.api.models.application_request import ApplicationRequest
from massgov.pfml.api.models.application_response import ApplicationResponse
from massgov.pfml.db.models.applications import Application
from massgov.pfml.util.pydantic import PydanticBaseModel


def application_get(application_id):
    with app.db_session() as db_session:
        existing_application = (
            db_session.query(Application)
            .filter(Application.application_id == application_id)
            .one_or_none()
        )

    if existing_application is None:
        raise NotFound()
    else:
        application_response = ApplicationResponse(existing_application)
        return application_response.create_full_response()


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
        existing_application = (
            db_session.query(Application)
            .filter(Application.application_id == application_id)
            .one_or_none()
        )

    if existing_application is None:
        raise NotFound

    application_request = ApplicationRequest(body, existing_application)
    errors_and_warnings = application_request.validate()

    if len(errors_and_warnings) == 0:
        application_request.update()

    if len(errors_and_warnings) == 0:
        return {"code": "200", "message": "Application updated without errors."}, 200
    else:
        return (
            {"code": "400", "message": "Application has errors", "errors": errors_and_warnings},
            400,
        )


def applications_submit(application_id):
    with app.db_session() as db_session:
        existing_application = (
            db_session.query(Application)
            .filter(Application.application_id == application_id)
            .one_or_none()
        )

        if existing_application is None:
            raise NotFound

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
