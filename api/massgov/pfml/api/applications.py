from datetime import datetime

import connexion
from werkzeug.exceptions import NotFound

import massgov.pfml.api.app as app
from massgov.pfml.api.models.application_request import ApplicationRequest
from massgov.pfml.api.models.application_response import ApplicationResponse
from massgov.pfml.db.models.applications import Application
from massgov.pfml.db.models.employees import Status
from massgov.pfml.db.status import UserStatusDescription, get_or_make_status


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


def applications_get():
    applications = []

    with app.db_session() as db_session:
        existing_applications = db_session.query(Application).all()

    for application in existing_applications:
        short_application = {
            "application_id": application.application_id,
            "application_nickname": str(application.nickname or ""),
        }
        applications.append(short_application)

    return applications


def applications_start():
    application = Application()
    application.start_time = datetime.now()

    with app.db_session() as db_session:
        draft_status = (
            db_session.query(Status).filter(Status.status_description == "Draft").one_or_none()
        )

        application.status_id = draft_status.status_id
        db_session.add(application)
        db_session.flush()
        db_session.commit()

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

        completed_status = get_or_make_status(db_session, UserStatusDescription.completed)
        existing_application.status_id = completed_status.status_id
        existing_application.completed_time = datetime.now()
        db_session.add(existing_application)
        db_session.flush()
        db_session.refresh(existing_application)
        db_session.commit()

    success_response = {
        "code": "201",
        "message": "Application {} completed without errors".format(
            existing_application.application_id
        ),
        "warnings": [],
        "errors": [],
    }

    return success_response, 201
