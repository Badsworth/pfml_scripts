import copy
import io

import pytest

import massgov.pfml.fineos.mock_client
from massgov.pfml.api.models.applications.common import ContentType as AllowedContentTypes
from massgov.pfml.db.models.applications import DocumentType
from massgov.pfml.db.models.factories import ApplicationFactory, ClaimFactory, DocumentFactory
from massgov.pfml.fineos import fineos_client, models

# every test in here requires real resources
pytestmark = pytest.mark.integration

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

STATE_MANAGED_PAID_LEAVE_CONFIRMATION_DATA = {
    "document_type": "State managed Paid Leave Confirmation",
    "name": "state_managed_pl_conf_test.png",
    "description": "State managed Paid Leave Confirmation",
}

CARE_FOR_A_FAMILY_MEMBER_FORM_DATA = {
    "document_type": "Care for a family member form",
    "name": "care_test.png",
    "description": "Care for a family member form",
}

OWN_SERIOUS_HEALTH_CONDITION_FORM_DATA = {
    "document_type": "Own serious health condition form",
    "name": "own_test.png",
    "description": "Own serious health condition form",
}

PREGNANCY_MATERNITY_FORM_DATA = {
    "document_type": "Pregnancy/Maternity form",
    "name": "pregnancy_test.png",
    "description": "Pregnancy/Maternity form",
}

CHILD_BONDING_EVIDENCE_FORM_DATA = {
    "document_type": "Child bonding evidence form",
    "name": "bonding_test.png",
    "description": "Child bonding evidence form",
}

MILITARY_EXIGENCY_FORM_DATA = {
    "document_type": "Military exigency form",
    "name": "military_test.png",
    "description": "Military exigency form",
}


def valid_file():
    return (io.BytesIO(b"abcdef"), "test.png")


def invalid_file():
    return (io.BytesIO(b"abcdef"), "test.txt")


def document_upload_helper(client, user, auth_token, form_data):
    claim = ClaimFactory.create(
        fineos_notification_id="NTN-111", fineos_absence_id="NTN-111-ABS-01"
    )
    application = ApplicationFactory.create(user=user, claim=claim)

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


def test_caring_leave_doc_upload(client, consented_user, consented_user_token, test_db_session):
    response = document_upload_helper(
        client=client,
        user=consented_user,
        auth_token=consented_user_token,
        form_data=document_upload_payload_helper(CARE_FOR_A_FAMILY_MEMBER_FORM_DATA, valid_file()),
    )

    assert response["status_code"] == 200

    response_data = response["data"]
    assert response_data["content_type"] == "image/png"
    assert response_data["description"] == "Care for a family member form"
    assert response_data["document_type"] == "Care for a family member form"
    assert response_data["fineos_document_id"] == "3011"  # See massgov/pfml/fineos/mock_client.py
    assert response_data["name"] == "care_test.png"
    assert response_data["user_id"] == str(consented_user.user_id)
    assert response_data["created_at"] is not None


def test_own_serious_health_doc_upload(
    client, consented_user, consented_user_token, test_db_session
):
    response = document_upload_helper(
        client=client,
        user=consented_user,
        auth_token=consented_user_token,
        form_data=document_upload_payload_helper(
            OWN_SERIOUS_HEALTH_CONDITION_FORM_DATA, valid_file()
        ),
    )

    assert response["status_code"] == 200

    response_data = response["data"]
    assert response_data["content_type"] == "image/png"
    assert response_data["description"] == "Own serious health condition form"
    assert response_data["document_type"] == "Own serious health condition form"
    assert response_data["fineos_document_id"] == "3011"  # See massgov/pfml/fineos/mock_client.py
    assert response_data["name"] == "own_test.png"
    assert response_data["user_id"] == str(consented_user.user_id)
    assert response_data["created_at"] is not None


def test_pregnancy_maternity_doc_upload(
    client, consented_user, consented_user_token, test_db_session
):
    response = document_upload_helper(
        client=client,
        user=consented_user,
        auth_token=consented_user_token,
        form_data=document_upload_payload_helper(PREGNANCY_MATERNITY_FORM_DATA, valid_file()),
    )

    assert response["status_code"] == 200

    response_data = response["data"]
    assert response_data["content_type"] == "image/png"
    assert response_data["description"] == "Pregnancy/Maternity form"
    assert response_data["document_type"] == "Pregnancy/Maternity form"
    assert response_data["fineos_document_id"] == "3011"  # See massgov/pfml/fineos/mock_client.py
    assert response_data["name"] == "pregnancy_test.png"
    assert response_data["user_id"] == str(consented_user.user_id)
    assert response_data["created_at"] is not None


def test_child_bonding_doc_upload(client, consented_user, consented_user_token, test_db_session):
    response = document_upload_helper(
        client=client,
        user=consented_user,
        auth_token=consented_user_token,
        form_data=document_upload_payload_helper(CHILD_BONDING_EVIDENCE_FORM_DATA, valid_file()),
    )

    assert response["status_code"] == 200

    response_data = response["data"]
    assert response_data["content_type"] == "image/png"
    assert response_data["description"] == "Child bonding evidence form"
    assert response_data["document_type"] == "Child bonding evidence form"
    assert response_data["fineos_document_id"] == "3011"  # See massgov/pfml/fineos/mock_client.py
    assert response_data["name"] == "bonding_test.png"
    assert response_data["user_id"] == str(consented_user.user_id)
    assert response_data["created_at"] is not None


def test_military_exigency_doc_upload(
    client, consented_user, consented_user_token, test_db_session
):
    response = document_upload_helper(
        client=client,
        user=consented_user,
        auth_token=consented_user_token,
        form_data=document_upload_payload_helper(MILITARY_EXIGENCY_FORM_DATA, valid_file()),
    )

    assert response["status_code"] == 200

    response_data = response["data"]
    assert response_data["content_type"] == "image/png"
    assert response_data["description"] == "Military exigency form"
    assert response_data["document_type"] == "Military exigency form"
    assert response_data["fineos_document_id"] == "3011"  # See massgov/pfml/fineos/mock_client.py
    assert response_data["name"] == "military_test.png"
    assert response_data["user_id"] == str(consented_user.user_id)
    assert response_data["created_at"] is not None


def test_old_document_type_saved(client, consented_user, consented_user_token, test_db_session):
    claim = ClaimFactory.create(
        fineos_notification_id="NTN-111", fineos_absence_id="NTN-111-ABS-01"
    )

    application = ApplicationFactory.create(user=consented_user, claim=claim)

    # Create a document with the STATE_MANAGED_PAID_LEAVE_CONFIRMATION document type
    DocumentFactory.create(
        user_id=consented_user.user_id,
        application_id=application.application_id,
        document_type_id=DocumentType.STATE_MANAGED_PAID_LEAVE_CONFIRMATION.document_type_id,
    )

    # POST a document with one of the new document types
    response = client.post(
        "/v1/applications/{}/documents".format(application.application_id),
        headers={"Authorization": f"Bearer {consented_user_token}"},
        content_type="multipart/form-data",
        data=document_upload_payload_helper(CARE_FOR_A_FAMILY_MEMBER_FORM_DATA, valid_file()),
    ).get_json()

    assert response["status_code"] == 200

    response_data = response["data"]
    # Assert that the document has the old, rather than the new, document type
    assert response_data["document_type"] == "State managed Paid Leave Confirmation"
    assert response_data["content_type"] == "image/png"
    assert response_data["description"] == "Care for a family member form"
    assert response_data["fineos_document_id"] == "3011"  # See massgov/pfml/fineos/mock_client.py
    assert response_data["name"] == "care_test.png"
    assert response_data["user_id"] == str(consented_user.user_id)
    assert response_data["created_at"] is not None


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
        assert capture[i][0] == expected_client_function_calls[i]


@pytest.mark.parametrize(
    "mark_evidence_received_flag,document_type,expected_client_function_calls",
    (
        (
            True,
            DocumentType.CARE_FOR_A_FAMILY_MEMBER_FORM.document_type_description,
            ("find_employer", "register_api_user", "upload_document", "mark_document_as_received"),
        ),
        (
            True,
            DocumentType.OWN_SERIOUS_HEALTH_CONDITION_FORM.document_type_description,
            ("find_employer", "register_api_user", "upload_document", "mark_document_as_received"),
        ),
        (
            True,
            DocumentType.PREGNANCY_MATERNITY_FORM.document_type_description,
            ("find_employer", "register_api_user", "upload_document", "mark_document_as_received"),
        ),
        (
            True,
            DocumentType.CHILD_BONDING_EVIDENCE_FORM.document_type_description,
            ("find_employer", "register_api_user", "upload_document", "mark_document_as_received"),
        ),
        (
            True,
            DocumentType.MILITARY_EXIGENCY_FORM.document_type_description,
            ("find_employer", "register_api_user", "upload_document", "mark_document_as_received"),
        ),
    ),
)
def test_new_document_types_upload_and_mark_evidence_received(
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
        assert capture[i][0] == expected_client_function_calls[i]


def test_documents_get(client, consented_user, consented_user_token, test_db_session):
    claim = ClaimFactory.create(
        fineos_notification_id="NTN-111", fineos_absence_id="NTN-111-ABS-01"
    )
    application = ApplicationFactory.create(user=consented_user, claim=claim)

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

    claim = ClaimFactory.create(
        fineos_notification_id="NTN-111", fineos_absence_id="NTN-111-ABS-01"
    )
    application = ApplicationFactory.create(user=consented_user, claim=claim)

    response = client.get(
        "/v1/applications/{}/documents".format(application.application_id),
        headers={"Authorization": f"Bearer {consented_user_token}"},
    ).get_json()

    assert response["status_code"] == 200
    response_data = response["data"][0]

    assert response_data["created_at"] == "2020-09-01"


def test_documents_download(client, consented_user, consented_user_token, test_db_session):
    document_id = "3011"

    claim = ClaimFactory.create(
        fineos_notification_id="NTN-111", fineos_absence_id="NTN-111-ABS-01"
    )
    application = ApplicationFactory.create(user=consented_user, claim=claim)

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

    claim = ClaimFactory.create(
        fineos_notification_id="NTN-111", fineos_absence_id="NTN-111-ABS-01"
    )
    application = ApplicationFactory.create(user=consented_user, claim=claim)

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

    claim = ClaimFactory.create(
        fineos_notification_id="NTN-111", fineos_absence_id="NTN-111-ABS-01"
    )
    application = ApplicationFactory.create(user=consented_user, claim=claim)

    response = client.get(
        "/v1/applications/{}/documents/{}".format(application.application_id, document_id),
        headers={"Authorization": f"Bearer {consented_user_token}"},
    )

    assert response.status_code == 200
    assert response.content_type == "application/pdf"
    assert response.headers.get("Content-Disposition") == "attachment; filename=test.pdf"
    assert response.data.startswith(b"\x89PNG\r\n")


def test_documents_download_forbidden(client, fineos_user, fineos_user_token, test_db_session):
    document_id = "3011"

    claim = ClaimFactory.create(
        fineos_notification_id="NTN-111", fineos_absence_id="NTN-111-ABS-01"
    )
    application = ApplicationFactory.create(user=fineos_user, claim=claim)

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
