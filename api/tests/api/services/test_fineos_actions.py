import io

import massgov.pfml.fineos
from massgov.pfml.api.services import fineos_actions
from massgov.pfml.db.models.applications import Application
from massgov.pfml.db.models.factories import ApplicationFactory
from massgov.pfml.fineos.exception import FINEOSClientBadResponse, FINEOSNotFound


def test_register_employee_pass(test_db_session):
    fineos_client = massgov.pfml.fineos.MockFINEOSClient()

    employer_fein = "179892886"
    employee_ssn = "784569632"
    employee_external_id = fineos_actions.register_employee(
        fineos_client, employee_ssn, employer_fein, test_db_session
    )

    assert employee_external_id is not None


def test_using_existing_id(test_db_session):
    fineos_client = massgov.pfml.fineos.MockFINEOSClient()

    employer_fein = "179892886"
    employee_ssn = "784569632"
    employee_external_id_1 = fineos_actions.register_employee(
        fineos_client, employee_ssn, employer_fein, test_db_session
    )

    employee_external_id_2 = fineos_actions.register_employee(
        fineos_client, employee_ssn, employer_fein, test_db_session
    )

    assert employee_external_id_1 == employee_external_id_2


def test_create_different_id_for_other_employer(test_db_session):
    fineos_client = massgov.pfml.fineos.MockFINEOSClient()

    employer_fein = "179892886"
    employee_ssn = "784569632"
    employee_external_id_1 = fineos_actions.register_employee(
        fineos_client, employee_ssn, employer_fein, test_db_session
    )

    employer_fein = "179892897"
    employee_external_id_2 = fineos_actions.register_employee(
        fineos_client, employee_ssn, employer_fein, test_db_session
    )

    assert employee_external_id_1 != employee_external_id_2


def test_register_employee_bad_fein(test_db_session):
    fineos_client = massgov.pfml.fineos.MockFINEOSClient()

    employer_fein = "999999999"
    employee_ssn = "784569632"

    try:
        fineos_actions.register_employee(
            fineos_client, employee_ssn, employer_fein, test_db_session
        )
    except FINEOSNotFound:
        assert True


def test_register_employee_bad_ssn(test_db_session):
    fineos_client = massgov.pfml.fineos.MockFINEOSClient()

    employer_fein = "179892886"
    employee_ssn = "999999999"

    try:
        fineos_actions.register_employee(
            fineos_client, employee_ssn, employer_fein, test_db_session
        )
    except FINEOSClientBadResponse:
        assert True


def test_send_to_fineos(user, test_db_session):
    application = ApplicationFactory.create(user=user)
    application.employer_fein = "179892886"
    application.tax_identifier.tax_identifier = "784569632"

    assert application.fineos_absence_id is None
    assert application.fineos_notification_case_id is None

    fineos_actions.send_to_fineos(application, test_db_session)

    updated_application = test_db_session.query(Application).get(application.application_id)

    assert updated_application.fineos_absence_id is not None
    assert str(updated_application.fineos_absence_id).startswith("NTN")
    assert str(updated_application.fineos_absence_id).__contains__("ABS")

    assert updated_application.fineos_notification_case_id is not None
    assert str(updated_application.fineos_notification_case_id).startswith("NTN")


def test_document_upload(user, test_db_session):
    application = ApplicationFactory.create(user=user)
    application.employer_fein = "179892886"
    application.tax_identifier.tax_identifier = "784569632"

    fineos_actions.send_to_fineos(application, test_db_session)
    updated_application = test_db_session.query(Application).get(application.application_id)

    assert updated_application.fineos_absence_id is not None

    file = io.BytesIO(b"abcdef")
    file_content = file.read()
    file_name = "test.png"
    content_type = "image/png"

    document_type = "Passport"
    description = "Test document upload description"

    fineos_document = fineos_actions.upload_document(
        updated_application,
        document_type,
        file_content,
        file_name,
        content_type,
        description,
        test_db_session,
    ).dict()
    assert fineos_document["caseId"] == updated_application.fineos_absence_id
    assert fineos_document["documentId"] == 3011  # See massgov/pfml/fineos/mock_client.py
    assert fineos_document["name"] == document_type
    assert fineos_document["fileExtension"] == ".png"
    assert fineos_document["originalFilename"] == file_name
    assert fineos_document["description"] == description
