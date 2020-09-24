import io

from massgov.pfml.api.models.applications.common import ContentType as AllowedContentTypes
from massgov.pfml.db.models.factories import ApplicationFactory

VALID_FORM_DATA = {
    "document_category": "Certification",
    "document_type": "Passport",
    "name": "passport.png",
    "description": "Passport",
}

VALID_MISSING_NAME_DESCRIPTION_FORM_DATA = {
    "document_category": "Certification",
    "document_type": "Passport",
    "description": "Passport",
}

MISSING_DOCUMENT_CATEGORY_FORM_DATA = {
    "document_type": "Passport",
}

FILE_WITH_NO_EXTENSION = (io.BytesIO(b"abcdef"), "test")


def valid_file():
    return (io.BytesIO(b"abcdef"), "test.png")


def invalid_file():
    return (io.BytesIO(b"abcdef"), "test.txt")


def document_upload_helper(client, user, auth_token, form_data):
    absence_case_id = "NTN-111-ABS-01"
    application = ApplicationFactory.create(user=user, fineos_absence_id=absence_case_id)

    response = client.post(
        "/v1/applications/{}/documents".format(application.application_id),
        headers={"Authorization": f"Bearer {auth_token}"},
        content_type="multipart/form-data",
        data=form_data,
    )

    return response.get_json()


def document_upload_payload_helper(form_data, file):
    payload = form_data
    payload["file"] = file
    return payload


def test_document_upload_success(client, consented_user, consented_user_token, test_db_session):
    response = document_upload_helper(
        client=client,
        user=consented_user,
        auth_token=consented_user_token,
        form_data=document_upload_payload_helper(VALID_FORM_DATA, valid_file()),
    )

    assert response["status_code"] == 200

    response_data = response["data"]
    assert response_data["content_type"] == "image/png"
    assert response_data["description"] == "Passport"
    assert response_data["document_type"] == "Passport"
    assert response_data["fineos_document_id"] == "3011"  # See massgov/pfml/fineos/mock_client.py
    assert response_data["name"] == "passport.png"
    assert response_data["user_id"] == str(consented_user.user_id)
    assert response_data["created_at"] is not None


def test_document_upload_unauthorized_application_user(
    client, user, consented_user_token, test_db_session
):
    response = document_upload_helper(
        client=client,
        user=user,
        auth_token=consented_user_token,
        form_data=document_upload_payload_helper(VALID_FORM_DATA, valid_file()),
    )

    assert response["status_code"] == 403
    assert response["errors"] is not None


def test_document_upload_unauthorized_consented_user(client, user, auth_token, test_db_session):
    response = document_upload_helper(
        client=client,
        user=user,
        auth_token=auth_token,
        form_data=document_upload_payload_helper(VALID_FORM_DATA, valid_file()),
    )

    assert response["status_code"] == 403
    assert response["errors"] is not None


def test_document_upload_invalid_filename(
    client, consented_user, consented_user_token, test_db_session
):
    response = document_upload_helper(
        client=client,
        user=consented_user,
        auth_token=consented_user_token,
        form_data=document_upload_payload_helper(VALID_FORM_DATA, FILE_WITH_NO_EXTENSION),
    )

    assert response["status_code"] == 400
    assert response["errors"] is not None
    assert len(response["errors"]) == 1
    assert response["errors"][0]["type"] == "file_name_extension"
    assert response["errors"][0]["rule"] == "File name extension required."


def test_document_upload_invalid_content_type(
    client, consented_user, consented_user_token, test_db_session
):
    response = document_upload_helper(
        client=client,
        user=consented_user,
        auth_token=consented_user_token,
        form_data=document_upload_payload_helper(VALID_FORM_DATA, invalid_file()),
    )

    assert response["status_code"] == 400
    assert response["errors"] is not None
    assert len(response["errors"]) == 1
    assert response["errors"][0]["type"] == "file_type"

    allowed_content_types = [item.value for item in AllowedContentTypes]
    assert response["errors"][0]["rule"] == allowed_content_types


def test_document_upload_invalid_form_data(
    client, consented_user, consented_user_token, test_db_session
):
    response = document_upload_helper(
        client=client,
        user=consented_user,
        auth_token=consented_user_token,
        form_data=document_upload_payload_helper(MISSING_DOCUMENT_CATEGORY_FORM_DATA, valid_file()),
    )

    assert response["status_code"] == 400
    assert response["errors"] is not None
    assert len(response["errors"]) == 1
    assert response["errors"][0]["type"] == "required"
    assert response["errors"][0]["message"] == "'document_category' is a required property"


def test_document_upload_defaults_for_name(
    client, consented_user, consented_user_token, test_db_session
):
    response = document_upload_helper(
        client=client,
        user=consented_user,
        auth_token=consented_user_token,
        form_data=document_upload_payload_helper(
            VALID_MISSING_NAME_DESCRIPTION_FORM_DATA, valid_file()
        ),
    )

    assert response["status_code"] == 200
    assert response["data"]["name"] == "test.png"


def test_documents_get(client, consented_user, consented_user_token, test_db_session):
    absence_case_id = "NTN-111-ABS-01"
    application = ApplicationFactory.create(user=consented_user, fineos_absence_id=absence_case_id)

    response = client.get(
        "/v1/applications/{}/documents".format(application.application_id),
        headers={"Authorization": f"Bearer {consented_user_token}"},
    ).get_json()

    assert response["status_code"] == 200
    response_data = response["data"][0]

    # See massgov/pfml/fineos/mock_client for the following values
    assert response_data["content_type"] == "image/png"
    assert response_data["document_type"] == "ID Document"
    assert response_data["fineos_document_id"] == "3011"
    assert response_data["name"] == "test.png"
    assert response_data["description"] == "Mock File"
    assert response_data["user_id"] == str(consented_user.user_id)
    assert response_data["created_at"] is not None
