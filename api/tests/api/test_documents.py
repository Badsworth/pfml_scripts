import copy
import io

import pytest

import massgov.pfml.fineos.mock_client
from massgov.pfml.api.models.applications.common import ContentType as AllowedContentTypes
from massgov.pfml.db.models.applications import DocumentType
from massgov.pfml.db.models.factories import ApplicationFactory
from massgov.pfml.fineos import fineos_client, models

VALID_FORM_DATA = {
    "document_type": "Passport",
    "name": "passport.png",
    "description": "Passport",
}

VALID_MISSING_NAME_DESCRIPTION_FORM_DATA = {
    "document_type": "Passport",
    "description": "Passport",
}

MISSING_DOCUMENT_TYPE_FORM_DATA = {
    "description": "Passport",
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
        form_data=document_upload_payload_helper(MISSING_DOCUMENT_TYPE_FORM_DATA, valid_file()),
    )

    assert response["status_code"] == 400
    assert response["errors"] is not None
    assert len(response["errors"]) == 1
    assert response["errors"][0]["type"] == "required"
    assert response["errors"][0]["message"] == "'document_type' is a required property"


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


@pytest.mark.parametrize(
    "mark_evidence_received_flag,document_type,expected_client_function_calls",
    (
        # Expect to make call because flag is set and document type is associated with evidence.
        (
            True,
            DocumentType.IDENTIFICATION_PROOF.document_type_description,
            ("find_employer", "register_api_user", "upload_document", "mark_document_as_received"),
        ),
        # DO NOT expect to make call because flag is set but document type is not associated with evidence.
        (
            True,
            DocumentType.PASSPORT.document_type_description,
            ("find_employer", "register_api_user", "upload_document"),
        ),
        # DO NOT expect to make call because flag is not set.
        (
            False,
            DocumentType.IDENTIFICATION_PROOF.document_type_description,
            ("find_employer", "register_api_user", "upload_document"),
        ),
    ),
)
def test_document_upload_and_mark_evidence_received(
    client,
    consented_user,
    consented_user_token,
    test_db_session,
    mark_evidence_received_flag,
    document_type,
    expected_client_function_calls,
):
    form_data = VALID_FORM_DATA
    form_data["mark_evidence_received"] = mark_evidence_received_flag
    form_data["document_type"] = document_type

    massgov.pfml.fineos.mock_client.start_capture()
    response = document_upload_helper(
        client=client,
        user=consented_user,
        auth_token=consented_user_token,
        form_data=document_upload_payload_helper(form_data, valid_file()),
    )
    assert response["status_code"] == 200

    capture = massgov.pfml.fineos.mock_client.get_capture()

    assert len(capture) == len(expected_client_function_calls)

    for i in range(len(capture)):
        print(capture[i][0])
        assert capture[i][0] == expected_client_function_calls[i]


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
    assert response_data["content_type"] == "application/pdf"
    assert response_data["document_type"] == "Approval Notice"
    assert response_data["fineos_document_id"] == "3011"
    assert response_data["name"] == "test.pdf"
    assert response_data["description"] == "Mock File"
    assert response_data["user_id"] == str(consented_user.user_id)
    assert response_data["created_at"] is not None


def test_documents_get_date_created(
    client, consented_user, consented_user_token, test_db_session, monkeypatch
):
    absence_case_id = "NTN-111-ABS-01"

    def mocked_mock_document(absence_id):

        # mock the response object using "dateCreated"
        mocked_document = copy.copy(massgov.pfml.fineos.mock_client.MOCK_DOCUMENT_DATA)
        mocked_document.update(
            {
                "caseId": absence_id,
                "dateCreated": "2020-09-01",
                "name": "ID Document",
                "originalFilename": "test.png",
                "receivedDate": "",
            }
        )
        return mocked_document

    monkeypatch.setattr(massgov.pfml.fineos.mock_client, "mock_document", mocked_mock_document)

    application = ApplicationFactory.create(user=consented_user, fineos_absence_id=absence_case_id)

    response = client.get(
        "/v1/applications/{}/documents".format(application.application_id),
        headers={"Authorization": f"Bearer {consented_user_token}"},
    ).get_json()

    assert response["status_code"] == 200
    response_data = response["data"][0]

    assert response_data["created_at"] == "2020-09-01T00:00:00Z"


def test_documents_download(client, consented_user, consented_user_token, test_db_session):
    absence_case_id = "NTN-111-ABS-01"
    document_id = "3011"

    application = ApplicationFactory.create(user=consented_user, fineos_absence_id=absence_case_id)

    response = client.get(
        "/v1/applications/{}/documents/{}".format(application.application_id, document_id),
        headers={"Authorization": f"Bearer {consented_user_token}"},
    )

    assert response.status_code == 200
    assert response.content_type == "application/pdf"
    assert response.headers.get("Content-Disposition") == "attachment; filename=test.pdf"
    assert response.data.startswith(b"\x89PNG\r\n")


def test_documents_download_matches_document_id(
    client, consented_user, consented_user_token, test_db_session, monkeypatch
):
    # Regression test to ensure that get_document_by_id searches through all documents from FINEOS
    absence_case_id = "NTN-111-ABS-01"
    document_id = "3012"

    def mock_get_documents(self, user_id, absence_id):
        # mock the response to return multiple documents
        document_type = "Approval Notice"
        file_name = "test.pdf"
        description = "Mock File"
        document1 = copy.copy(massgov.pfml.fineos.mock_client.MOCK_DOCUMENT_DATA)
        document1.update(
            {
                "caseId": absence_id,
                "name": document_type,
                "fileExtension": ".pdf",
                "originalFilename": file_name,
                "description": description,
                "documentId": 3011,
            }
        )
        document2 = copy.copy(massgov.pfml.fineos.mock_client.MOCK_DOCUMENT_DATA)
        document2.update(
            {
                "caseId": absence_id,
                "name": document_type,
                "fileExtension": ".pdf",
                "originalFilename": file_name,
                "description": description,
                "documentId": 3012,
            }
        )
        return [
            models.customer_api.Document.parse_obj(
                fineos_client.fineos_document_empty_dates_to_none(document1)
            ),
            models.customer_api.Document.parse_obj(
                fineos_client.fineos_document_empty_dates_to_none(document2)
            ),
        ]

    monkeypatch.setattr(
        massgov.pfml.fineos.mock_client.MockFINEOSClient, "get_documents", mock_get_documents
    )

    application = ApplicationFactory.create(user=consented_user, fineos_absence_id=absence_case_id)

    response = client.get(
        "/v1/applications/{}/documents/{}".format(application.application_id, document_id),
        headers={"Authorization": f"Bearer {consented_user_token}"},
    )

    assert response.status_code == 200
    assert response.content_type == "application/pdf"
    assert response.headers.get("Content-Disposition") == "attachment; filename=test.pdf"
    assert response.data.startswith(b"\x89PNG\r\n")


def test_documents_download_mismatch_case(
    client, consented_user, consented_user_token, test_db_session, monkeypatch
):
    # Regression test to ensure that get_document_by_id searches through all documents from FINEOS
    absence_case_id = "NTN-111-ABS-01"
    document_id = "3012"

    def mock_get_documents(self, user_id, absence_id):
        # mock the response to return multiple documents
        document_type = "approval notice"
        document1 = copy.copy(massgov.pfml.fineos.mock_client.MOCK_DOCUMENT_DATA)
        document1.update({"caseId": absence_id, "name": document_type, "documentId": document_id})

        return [
            models.customer_api.Document.parse_obj(
                fineos_client.fineos_document_empty_dates_to_none(document1)
            ),
        ]

    monkeypatch.setattr(
        massgov.pfml.fineos.mock_client.MockFINEOSClient, "get_documents", mock_get_documents
    )

    application = ApplicationFactory.create(user=consented_user, fineos_absence_id=absence_case_id)

    response = client.get(
        "/v1/applications/{}/documents/{}".format(application.application_id, document_id),
        headers={"Authorization": f"Bearer {consented_user_token}"},
    )

    assert response.status_code == 200
    assert response.content_type == "application/pdf"
    assert response.headers.get("Content-Disposition") == "attachment; filename=test.pdf"
    assert response.data.startswith(b"\x89PNG\r\n")


def test_documents_download_forbidden(client, fineos_user, fineos_user_token, test_db_session):
    absence_case_id = "NTN-111-ABS-01"
    document_id = "3011"

    application = ApplicationFactory.create(user=fineos_user, fineos_absence_id=absence_case_id)

    response = client.get(
        "/v1/applications/{}/documents/{}".format(application.application_id, document_id),
        headers={"Authorization": f"Bearer {fineos_user_token}"},
    )

    assert response.status_code == 403


def test_documents_get_not_submitted_application(
    client, consented_user, consented_user_token, test_db_session
):
    application = ApplicationFactory.create(user=consented_user)

    response = client.get(
        "/v1/applications/{}/documents".format(application.application_id),
        headers={"Authorization": f"Bearer {consented_user_token}"},
    ).get_json()

    assert response["status_code"] == 200
    assert response["data"] is not None
    assert len(response["data"]) == 0
