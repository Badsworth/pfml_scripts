import io
import re
from datetime import date, timedelta

import pytest

import massgov.pfml.fineos
import massgov.pfml.fineos.mock_client as fineos_mock
from massgov.pfml.api.services import fineos_actions
from massgov.pfml.db.models.applications import (
    Application,
    LeaveReason,
    LeaveReasonQualifier,
    LkDayOfWeek,
)
from massgov.pfml.db.models.employees import (
    AddressType,
    BankAccountType,
    Country,
    Employer,
    PaymentMethod,
)
from massgov.pfml.db.models.factories import (
    AddressFactory,
    ApplicationFactory,
    ContinuousLeavePeriodFactory,
    PaymentPreferenceFactory,
    ReducedScheduleLeavePeriodFactory,
    WorkPatternFixedFactory,
)
from massgov.pfml.fineos import FINEOSClient
from massgov.pfml.fineos.exception import FINEOSClientBadResponse, FINEOSClientError, FINEOSNotFound
from massgov.pfml.fineos.models import CreateOrUpdateEmployer, CreateOrUpdateServiceAgreement
from massgov.pfml.fineos.models.customer_api import Address as FineosAddress
from massgov.pfml.fineos.models.customer_api import CustomerAddress

# almost every test in here requires real resources
pytestmark = pytest.mark.integration


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


def test_determine_absence_period_status_cont(user, test_db_session):
    application = ApplicationFactory.create(user=user)
    continuous_leave_period = ContinuousLeavePeriodFactory.create()
    application.continuous_leave_periods.append(continuous_leave_period)

    status = fineos_actions.determine_absence_period_status(application)
    assert status == "known"


def test_determine_absence_period_status_reduced(user, test_db_session):
    today = date.today()
    tomorrow = today + timedelta(days=1)

    application = ApplicationFactory.create(
        user=user,
        child_birth_date=tomorrow,
        has_future_child_date=True,
        leave_reason_id=LeaveReason.CHILD_BONDING.leave_reason_id,
    )
    reduced_schedule_leave_period = ReducedScheduleLeavePeriodFactory.create()
    application.reduced_schedule_leave_periods.append(reduced_schedule_leave_period)

    status = fineos_actions.determine_absence_period_status(application)
    assert status == "estimated"


def test_send_to_fineos(user, test_db_session):
    application = ApplicationFactory.create(
        user=user, work_pattern=WorkPatternFixedFactory.create()
    )
    application.employer_fein = "179892886"
    application.tax_identifier.tax_identifier = "784569632"

    # create leave period to ensure the code that sets the "status" for the absence period is triggered
    continuous_leave_period = ContinuousLeavePeriodFactory.create()
    application.continuous_leave_periods.append(continuous_leave_period)

    assert application.fineos_absence_id is None
    assert application.fineos_notification_case_id is None

    fineos_actions.send_to_fineos(application, test_db_session, user)

    updated_application = test_db_session.query(Application).get(application.application_id)

    assert updated_application.fineos_absence_id is not None
    assert str(updated_application.fineos_absence_id).startswith("NTN")
    assert str(updated_application.fineos_absence_id).__contains__("ABS")

    assert updated_application.fineos_notification_case_id is not None
    assert str(updated_application.fineos_notification_case_id).startswith("NTN")


def test_document_upload(user, test_db_session):
    application = ApplicationFactory.create(
        user=user, work_pattern=WorkPatternFixedFactory.create()
    )
    application.employer_fein = "179892886"
    application.tax_identifier.tax_identifier = "784569632"

    fineos_actions.send_to_fineos(application, test_db_session, user)
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


def test_submit_direct_deposit_payment_preference(user, test_db_session):
    payment_pref = PaymentPreferenceFactory.create(
        payment_method_id=PaymentMethod.ACH.payment_method_id,
        account_number="123456789",
        routing_number="234567890",
        bank_account_type_id=BankAccountType.CHECKING.bank_account_type_id,
    )
    application = ApplicationFactory.create(user=user, payment_preference=payment_pref)
    fineos_response = fineos_actions.submit_payment_preference(application, test_db_session)
    test_db_session.refresh(application)
    assert fineos_response is not None
    assert fineos_response.paymentMethod == PaymentMethod.ACH.payment_method_description
    assert fineos_response.accountDetails.accountNo == payment_pref.account_number
    assert fineos_response.accountDetails.routingNumber == payment_pref.routing_number
    assert (
        fineos_response.accountDetails.accountType
        == BankAccountType.CHECKING.bank_account_type_description
    )
    assert fineos_response.chequeDetails is None


def test_submit_direct_deposit_payment_pref_with_mailing_addr(user, test_db_session):
    payment_pref = PaymentPreferenceFactory.create(
        payment_method_id=PaymentMethod.ACH.payment_method_id,
        account_number="123456789",
        routing_number="234567890",
        bank_account_type_id=BankAccountType.CHECKING.bank_account_type_id,
    )
    mailing_address = AddressFactory.create(
        address_type_id=AddressType.MAILING.address_type_id,
        address_line_one="123 Main St",
        city="Cambridge",
        geo_state_id=1,  # Massachusetts
        zip_code="02139",
    )
    residential_address = AddressFactory.create(
        address_type_id=AddressType.RESIDENTIAL.address_type_id,
        address_line_one="321 South St",
        city="Somerville",
        geo_state_id=1,
        zip_code="02138",
    )
    application = ApplicationFactory.create(
        user=user,
        payment_preference=payment_pref,
        has_mailing_address=True,
        mailing_address=mailing_address,
        residential_address=residential_address,
    )
    fineos_mock.start_capture()
    fineos_response = fineos_actions.submit_payment_preference(application, test_db_session)
    assert fineos_response is not None
    assert fineos_response.paymentMethod == PaymentMethod.ACH.payment_method_description

    capture = fineos_mock.get_capture()
    fineos_payment_calls = [
        method_call for method_call in capture if method_call[0] == "add_payment_preference"
    ]
    assert len(fineos_payment_calls) == 1
    sent_new_payment_pref = fineos_payment_calls[0][2]["payment_preference"]
    assert sent_new_payment_pref.customerAddress == CustomerAddress(
        address=FineosAddress(
            addressLine1=mailing_address.address_line_one,
            addressLine4=mailing_address.city,
            addressLine6="MA",
            country="USA",
            postCode="02139",
        )
    )
    assert sent_new_payment_pref.overridePostalAddress is True


def test_submit_direct_deposit_payment_pref_without_mailing_addr(user, test_db_session):
    payment_pref = PaymentPreferenceFactory.create(
        payment_method_id=PaymentMethod.ACH.payment_method_id,
        account_number="123456789",
        routing_number="234567890",
        bank_account_type_id=BankAccountType.CHECKING.bank_account_type_id,
    )
    residential_address = AddressFactory.create(
        address_type_id=AddressType.RESIDENTIAL.address_type_id,
        address_line_one="321 South St",
        city="Somerville",
        geo_state_id=1,  # Massachusetts
        zip_code="02139",
    )
    application = ApplicationFactory.create(
        user=user, payment_preference=payment_pref, residential_address=residential_address
    )
    fineos_mock.start_capture()
    fineos_response = fineos_actions.submit_payment_preference(application, test_db_session)
    test_db_session.refresh(application)
    assert fineos_response is not None
    assert fineos_response.paymentMethod == PaymentMethod.ACH.payment_method_description

    capture = fineos_mock.get_capture()
    fineos_payment_calls = [
        method_call for method_call in capture if method_call[0] == "add_payment_preference"
    ]
    assert len(fineos_payment_calls) == 1
    sent_new_payment_pref = fineos_payment_calls[0][2]["payment_preference"]
    assert sent_new_payment_pref.customerAddress is None
    assert sent_new_payment_pref.overridePostalAddress is None


def test_submit_check_payment_pref_with_mailing_addr(user, test_db_session):
    payment_pref = PaymentPreferenceFactory.create(
        payment_method_id=PaymentMethod.CHECK.payment_method_id,
    )
    mailing_address = AddressFactory.create(
        address_type_id=AddressType.MAILING.address_type_id,
        address_line_one="123 Main St",
        city="Cambridge",
        geo_state_id=1,  # Massachusetts
        zip_code="02138",
    )
    residential_address = AddressFactory.create(
        address_type_id=AddressType.RESIDENTIAL.address_type_id,
        address_line_one="321 South St",
        city="Somerville",
        geo_state_id=1,
        zip_code="02138",
    )
    application = ApplicationFactory.create(
        user=user,
        payment_preference=payment_pref,
        has_mailing_address=True,
        mailing_address=mailing_address,
        residential_address=residential_address,
    )
    fineos_mock.start_capture()
    fineos_response = fineos_actions.submit_payment_preference(application, test_db_session)
    test_db_session.refresh(application)
    assert fineos_response is not None
    assert fineos_response.paymentMethod == PaymentMethod.CHECK.payment_method_description

    capture = fineos_mock.get_capture()
    fineos_payment_calls = [
        method_call for method_call in capture if method_call[0] == "add_payment_preference"
    ]
    assert len(fineos_payment_calls) == 1
    sent_new_payment_pref = fineos_payment_calls[0][2]["payment_preference"]
    assert sent_new_payment_pref.customerAddress == CustomerAddress(
        address=FineosAddress(
            addressLine1=mailing_address.address_line_one,
            addressLine4=mailing_address.city,
            addressLine6="MA",
            country="USA",
            postCode="02138",
        )
    )
    assert sent_new_payment_pref.overridePostalAddress is True


def test_submit_check_payment_pref_without_mailing_addr(user, test_db_session):
    payment_pref = PaymentPreferenceFactory.create(
        payment_method_id=PaymentMethod.CHECK.payment_method_id,
    )
    residential_address = AddressFactory.create(
        address_type_id=AddressType.RESIDENTIAL.address_type_id,
        address_line_one="321 South St",
        city="Somerville",
        geo_state_id=1,
        zip_code="02138",
    )
    application = ApplicationFactory.create(
        user=user, payment_preference=payment_pref, residential_address=residential_address
    )
    fineos_mock.start_capture()
    fineos_response = fineos_actions.submit_payment_preference(application, test_db_session)
    test_db_session.refresh(application)
    assert fineos_response is not None
    assert fineos_response.paymentMethod == PaymentMethod.CHECK.payment_method_description

    capture = fineos_mock.get_capture()
    fineos_payment_calls = [
        method_call for method_call in capture if method_call[0] == "add_payment_preference"
    ]
    assert len(fineos_payment_calls) == 1
    sent_new_payment_pref = fineos_payment_calls[0][2]["payment_preference"]
    assert sent_new_payment_pref.customerAddress is None
    assert sent_new_payment_pref.overridePostalAddress is None


def test_build_week_based_work_pattern(user, test_db_session):
    application = ApplicationFactory.create(user=user, work_pattern=WorkPatternFixedFactory(),)

    work_pattern = fineos_actions.build_week_based_work_pattern(application)

    assert work_pattern.workPatternType == "Fixed"
    assert work_pattern.workPatternDays == [
        massgov.pfml.fineos.models.customer_api.WorkPatternDay(
            dayOfWeek=test_db_session.query(LkDayOfWeek).all()[i].day_of_week_description,
            weekNumber=1,
            hours=8,
            minutes=15,
        )
        for i in range(7)
    ]


def test_create_employer_simple(test_db_session):
    fineos_client = massgov.pfml.fineos.MockFINEOSClient()

    employer = Employer()
    employer.employer_fein = "888447598"
    employer.employer_name = "Test Organization Name44"
    employer.employer_dba = "Test Organization DBA"
    test_db_session.add(employer)
    test_db_session.commit()

    assert employer.fineos_employer_id is None

    fineos_employer_id = fineos_actions.create_or_update_employer(fineos_client, employer)

    assert employer.fineos_employer_id == fineos_employer_id


def test_update_employer_simple(test_db_session):
    fineos_client = massgov.pfml.fineos.MockFINEOSClient()

    employer = Employer()
    employer.employer_fein = "888447576"
    employer.employer_name = "Test Organization Name"
    employer.employer_dba = "Test Organization DBA"
    employer.fineos_employer_id = 250
    test_db_session.add(employer)
    test_db_session.commit()

    fineos_employer_id = fineos_actions.create_or_update_employer(fineos_client, employer)

    assert employer.fineos_employer_id == fineos_employer_id


def test_employer_creation_exception(test_db_session):
    fineos_client = massgov.pfml.fineos.MockFINEOSClient()

    employer = Employer()
    employer.employer_fein = "999999999"
    employer.employer_name = "Test Organization Dupe"
    employer.employer_dba = "Test Organization Dupe DBA"
    test_db_session.add(employer)
    test_db_session.commit()

    with pytest.raises(FINEOSClientError):
        fineos_actions.create_or_update_employer(fineos_client, employer)


# not an integration test, but marked as such by global pytest.mark.integration
# at top of file
def test_creating_request_payload():
    create_or_update_request = CreateOrUpdateEmployer(
        fineos_customer_nbr="pfml_test_payload",
        employer_fein="888997766",
        employer_legal_name="Test Organization Name",
        employer_dba="Test Organization DBA",
    )
    payload = FINEOSClient._create_or_update_employer_payload(create_or_update_request)

    assert payload is not None
    assert payload.__contains__("<Name>Test Organization Name</Name>")
    assert payload.__contains__("<CustomerNo>pfml_test_payload</CustomerNo>")
    assert payload.__contains__("<CorporateTaxNumber>888997766</CorporateTaxNumber>")
    assert payload.__contains__("<LegalBusinessName>Test Organization Name</LegalBusinessName>")
    assert payload.__contains__("<DoingBusinessAs>Test Organization DBA</DoingBusinessAs>")


# not an integration test, but marked as such by global pytest.mark.integration
# at top of file
def test_creating_request_payload_with_other_names():
    create_or_update_request = CreateOrUpdateEmployer(
        fineos_customer_nbr="pfml_test_payload",
        employer_fein="888997766",
        employer_legal_name="Test Organization Name",
        employer_dba="Test Organization DBA",
    )
    payload = FINEOSClient._create_or_update_employer_payload(create_or_update_request)

    assert payload is not None
    assert payload.__contains__("<Name>Test Organization Name</Name>")
    assert payload.__contains__("<CustomerNo>pfml_test_payload</CustomerNo>")
    assert payload.__contains__("<CorporateTaxNumber>888997766</CorporateTaxNumber>")
    assert payload.__contains__("<LegalBusinessName>Test Organization Name</LegalBusinessName>")
    assert payload.__contains__("<DoingBusinessAs>Test Organization DBA</DoingBusinessAs>")

    assert payload.__contains__("<ShortName>Test Org</ShortName>")
    assert payload.__contains__("<UpperName>TEST ORGANIZATION NAME</UpperName>")
    assert payload.__contains__("<UpperShortName>TEST ORG</UpperShortName>")


def test_build_bonding_date_reflexive_question_birth(user):
    application = ApplicationFactory.create(user=user)
    application.child_birth_date = date(2021, 2, 9)
    application.leave_reason_qualifier_id = LeaveReasonQualifier.NEWBORN.leave_reason_qualifier_id
    reflexive_question = fineos_actions.build_bonding_date_reflexive_question(application)

    assert reflexive_question.reflexiveQuestionLevel == "reason"
    assert (
        reflexive_question.reflexiveQuestionDetails[0].fieldName
        == "FamilyMemberDetailsQuestionGroup.familyMemberDetailsQuestions.dateOfBirth"
    )
    assert reflexive_question.reflexiveQuestionDetails[0].dateValue == date(2021, 2, 9)


def test_build_bonding_date_reflexive_question_adoption(user):
    application = ApplicationFactory.create(user=user)
    application.child_placement_date = date(2021, 2, 9)
    application.leave_reason_qualifier_id = LeaveReasonQualifier.ADOPTION.leave_reason_qualifier_id
    reflexive_question = fineos_actions.build_bonding_date_reflexive_question(application)

    assert (
        reflexive_question.reflexiveQuestionDetails[0].fieldName
        == "PlacementQuestionGroup.placementQuestions.adoptionDate"
    )
    assert reflexive_question.reflexiveQuestionDetails[0].dateValue == date(2021, 2, 9)


def test_build_bonding_date_reflexive_question_foster(user):
    application = ApplicationFactory.create(user=user)
    application.child_placement_date = date(2021, 2, 9)
    application.leave_reason_qualifier_id = (
        LeaveReasonQualifier.FOSTER_CARE.leave_reason_qualifier_id
    )
    reflexive_question = fineos_actions.build_bonding_date_reflexive_question(application)

    assert (
        reflexive_question.reflexiveQuestionDetails[0].fieldName
        == "PlacementQuestionGroup.placementQuestions.adoptionDate"
    )
    assert reflexive_question.reflexiveQuestionDetails[0].dateValue == date(2021, 2, 9)


def test_build_customer_model_no_mass_id(user):
    application = ApplicationFactory.create(user=user)
    customer_model = fineos_actions.build_customer_model(application, user)

    assert application.mass_id is None

    assert customer_model.classExtensionInformation[0].name == "MassachusettsID"
    assert customer_model.classExtensionInformation[0].stringValue == ""


def test_build_customer_address(user):
    residential_address = AddressFactory.create()
    application = ApplicationFactory.create(user=user, residential_address=residential_address)
    customer_address = fineos_actions.build_customer_address(application.residential_address)

    assert customer_address.address.addressLine1 == residential_address.address_line_one
    assert customer_address.address.addressLine2 == residential_address.address_line_two
    assert customer_address.address.addressLine4 == residential_address.city
    assert (
        customer_address.address.addressLine6 == residential_address.geo_state.geo_state_description
    )
    assert customer_address.address.postCode == residential_address.zip_code
    assert customer_address.address.country == Country.USA.country_description


def test_create_service_agreement_for_employer(test_db_session):
    fineos_client = massgov.pfml.fineos.MockFINEOSClient()

    employer = Employer()
    employer.employer_fein = "888447598"
    employer.employer_name = "Test Organization Name"
    employer.employer_dba = "Test Organization DBA"
    test_db_session.add(employer)

    fineos_actions.create_or_update_employer(fineos_client, employer)

    fineos_sa_id = fineos_actions.create_service_agreement_for_employer(fineos_client, employer)

    assert fineos_sa_id is not None
    assert fineos_sa_id == "SA-123"


# not an integration test, but marked as such by global pytest.mark.integration
# at top of file
def test_create_service_agreement_payload():
    service_agreement_inputs = CreateOrUpdateServiceAgreement(
        absence_management_flag=True, leave_plans="MA PFML - Family, MA PFML - Military Care"
    )
    payload = FINEOSClient._create_service_agreement_payload(123, service_agreement_inputs)

    assert payload is not None
    assert payload.__contains__("<config-name>ServiceAgreementService</config-name>")
    assert payload.__contains__("<name>CustomerNumber</name>")
    assert payload.__contains__("<value>123</value>")
    assert payload.__contains__("<name>LeavePlans</name>")
    assert payload.__contains__("<value>MA PFML - Family, MA PFML - Military Care</value>")
    assert not payload.__contains__("<name>AbsenceManagement</name>")
    assert payload.__contains__("<name>UnlinkAllExistingLeavePlans</name>")
    assert (
        re.search("<name>UnlinkAllExistingLeavePlans</name>\\s+<value>True</value>", payload)
        is not None
    )

    service_agreement_inputs = CreateOrUpdateServiceAgreement(
        absence_management_flag=False, leave_plans=""
    )
    payload = FINEOSClient._create_service_agreement_payload(123, service_agreement_inputs)

    assert payload is not None
    assert payload.__contains__("<config-name>ServiceAgreementService</config-name>")
    assert payload.__contains__("<name>CustomerNumber</name>")
    assert payload.__contains__("<value>123</value>")
    assert payload.__contains__("<name>AbsenceManagement</name>")
    assert re.search("<name>AbsenceManagement</name>\\s+<value>False</value>", payload) is not None
    assert not payload.__contains__("<name>LeavePlans</name>")
    assert payload.__contains__("<name>UnlinkAllExistingLeavePlans</name>")
    assert (
        re.search("<name>UnlinkAllExistingLeavePlans</name>\\s+<value>True</value>", payload)
        is not None
    )


# not an integration test, but marked as such by global pytest.mark.integration
# at top of file
def test_resolve_leave_plans():
    # Family Exemption = false
    # Medical Exemption = false
    # Assign: MA PFML Employee, MA PFML Family, MA PFML - Military Care
    leave_plans = fineos_actions.resolve_leave_plans(False, False)
    assert len(leave_plans) == 3
    leave_plans_str = ", ".join(leave_plans)
    assert leave_plans_str.__contains__("MA PFML - Employee")
    assert leave_plans_str.__contains__("MA PFML - Family")
    assert leave_plans_str.__contains__("MA PFML - Military Care")

    # Family Exemption = false
    # Medical Exemption = true
    # Assign: MA PFML Family, MA PFML - Military Care
    leave_plans = fineos_actions.resolve_leave_plans(False, True)
    assert len(leave_plans) == 2
    assert leave_plans_str.__contains__("MA PFML - Family")
    assert leave_plans_str.__contains__("MA PFML - Military Care")

    # Family Exemption = true
    # Medical Exemption = false
    # Assign: MA PFML Employee
    leave_plans = fineos_actions.resolve_leave_plans(True, False)
    assert len(leave_plans) == 1
    assert leave_plans_str.__contains__("MA PFML - Employee")

    # Family Exemption = true
    # Medical Exemption = true
    # Assign: no plans assigned
    leave_plans = fineos_actions.resolve_leave_plans(True, True)
    assert len(leave_plans) == 0
