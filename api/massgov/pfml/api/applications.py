import uuid

import connexion
from werkzeug.exceptions import NotFound

import massgov.pfml.api.generate_fake_data as fake

#
#   Shell class to be implemented at a later date.
#


def applications_get_all_fake():
    return fake.applications


def application_get(application_id):
    for application in fake.applications.values():
        if application.get("application_id") == application_id:
            return application

    raise NotFound()


def applications_get():
    applications = []
    for application in fake.applications.values():
        short_application = {}
        short_application["application_id"] = application["application_id"]
        short_application["application_nickname"] = application["application_nickname"]
        applications.append(short_application)

    return applications


def applications_start():
    return {"application_id": str(uuid.uuid4())}, 201


def applications_update(application_id):
    body = connexion.request.json

    # This is just a contrived error to test the different responses.
    if body.get("application_id") == application_id:
        return {"code": "200", "message": "Application updated without errors."}, 200
    else:
        return (
            {
                "code": "400",
                "message": "Application has errors",
                "errors": [
                    {
                        "message": "Application ID in body does not match header value.",
                        "attribute": "application_id",
                    }
                ],
            },
            400,
        )


def applications_submit(application_id):
    application_get(application_id)
    success_response = {
        "code": "201",
        "message": "Application completed without errors",
        "warnings": [],
        "errors": [],
    }

    return success_response, 201
