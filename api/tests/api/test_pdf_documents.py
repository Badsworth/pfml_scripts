from datetime import datetime
from pathlib import Path
from unittest import mock

import pytest

import massgov.pfml.util.pdf as pdf_util
from massgov.pfml.db.models.applications import LeaveReason
from massgov.pfml.db.models.factories import ApplicationFactory, ClaimFactory


@pytest.fixture
def valid_form_data():
    return {"document_type": "Passport", "name": "passport.pdf", "description": "Passport"}


@pytest.fixture
def valid_form_data_with_file(valid_form_data):
    def _form_data(file_data):
        payload = valid_form_data
        payload["file"] = file_data
        return payload

    return _form_data


@pytest.fixture
def document_upload(client, consented_user, consented_user_token, valid_form_data_with_file):
    def _upload_document(file_data):
        claim = ClaimFactory.create(
            fineos_notification_id="NTN-111", fineos_absence_id="NTN-111-ABS-01"
        )

        leave_reason_id = LeaveReason.SERIOUS_HEALTH_CONDITION_EMPLOYEE.leave_reason_id
        pregnant_or_recent_birth = (
            leave_reason_id == LeaveReason.PREGNANCY_MATERNITY.leave_reason_id
        )

        application = ApplicationFactory.create(
            user=consented_user,
            claim=claim,
            leave_reason_id=leave_reason_id,
            pregnant_or_recent_birth=pregnant_or_recent_birth,
            submitted_time=datetime.now(),
        )

        response = client.post(
            "/v1/applications/{}/documents".format(application.application_id),
            headers={"Authorization": f"Bearer {consented_user_token}"},
            content_type="multipart/form-data",
            data=valid_form_data_with_file(file_data),
        )

        return response.get_json()

    return _upload_document


@pytest.fixture
def pdf_bytes_small():
    return b"""%!
    /Helvetica findfont 20 scalefont setfont
    50 50 moveto
    (Hello World) show
    showpage
    quit
    """


@pytest.fixture
def pdf_bytes_large():
    pdf_str = f"""%!
    /Helvetica findfont 20 scalefont setfont
    50 50 moveto
    ({"A" * 6000000}) show
    showpage
    quit
    """
    return pdf_str.encode("utf-8")


@pytest.fixture
def pdf_util_test_files():
    return Path(__file__).parent.parent / "util/pdf/test_files"


@pytest.fixture
def small_pdf_file(pdf_util_test_files):
    return pdf_util_test_files / "certHealthCondition.pdf"


@pytest.fixture
def too_large_pdf_file(pdf_util_test_files):
    return pdf_util_test_files / "marsEv2.pdf"


# Check for regression against existing upload pattern
@mock.patch("massgov.pfml.util.pdf.compress_pdf")
def test_upload_does_not_attempt_compress_small_pdf(
    mock_compress_pdf, consented_user, document_upload, small_pdf_file
):
    with small_pdf_file.open("rb") as pdf:
        response = document_upload(pdf)

        mock_compress_pdf.assert_not_called()

        assert response["status_code"] == 200

        response_data = response["data"]
        assert response_data["content_type"] == "application/pdf"
        assert response_data["description"] == "Passport"
        assert response_data["document_type"] == "Passport"
        assert response_data["name"] == "passport.pdf"
        assert response_data["user_id"] == str(consented_user.user_id)
        assert response_data["created_at"] is not None


@mock.patch("massgov.pfml.util.pdf.subprocess.run")
def test_upload_forwards_compressed_file_to_fineos(
    mock_subprocess_run, document_upload, too_large_pdf_file, pdf_bytes_small
):
    mock_proc = mock.Mock()
    mock_proc.configure_mock(**{"returncode": 0, "stdout": pdf_bytes_small, "stderr": ""})
    mock_subprocess_run.return_value = mock_proc

    with too_large_pdf_file.open("rb") as pdf:
        response = document_upload(pdf)

        mock_subprocess_run.assert_called()
        assert response["status_code"] == 200

        response_data = response["data"]
        assert response_data["content_type"] == "application/pdf"
        assert response_data["description"] == "Passport"
        assert response_data["document_type"] == "Passport"
        assert response_data["name"] == "Compressed_passport.pdf"
        assert response_data["created_at"] is not None


def _assert_file_too_large_response(response):
    assert response["status_code"] == 400

    response_errors = response["errors"]
    assert response_errors is not None
    assert len(response_errors) == 1
    assert response_errors[0]["type"] == "file_size"


@mock.patch("massgov.pfml.util.pdf.compress_pdf")
def test_upload_validates_file_size(
    mock_compress_pdf, document_upload, too_large_pdf_file, pdf_bytes_large
):
    mock_compress_pdf.return_value = len(pdf_bytes_large)

    with too_large_pdf_file.open("rb") as pdf:
        response = document_upload(pdf)

        mock_compress_pdf.assert_called()
        _assert_file_too_large_response(response)


@mock.patch("massgov.pfml.util.pdf.compress_pdf")
def test_upload_handles_pdf_size_error(mock_compress_pdf, document_upload, too_large_pdf_file):
    mock_compress_pdf.side_effect = pdf_util.PDFSizeError

    with too_large_pdf_file.open("rb") as pdf:
        response = document_upload(pdf)

        mock_compress_pdf.assert_called()
        _assert_file_too_large_response(response)


@mock.patch("massgov.pfml.util.pdf.compress_pdf")
def test_upload_handles_pdf_compression_error(
    mock_compress_pdf, document_upload, too_large_pdf_file
):
    mock_compress_pdf.side_effect = pdf_util.PDFCompressionError

    with too_large_pdf_file.open("rb") as pdf:
        response = document_upload(pdf)

        mock_compress_pdf.assert_called()
        assert response["status_code"] == 400
        assert response["errors"] == [
            {"field": "file", "message": "File is too large.", "type": "file_size"}
        ]
        assert response["message"] == "Invalid request"
