from concurrent.futures import ThreadPoolExecutor
from datetime import date

import massgov.pfml.fineos
import massgov.pfml.fineos.mock.field
import massgov.pfml.fineos.mock_client
import massgov.pfml.fineos.models
import massgov.pfml.services.applications as application_service
from massgov.pfml.db.models.applications import (
    Application,
    ContinuousLeavePeriod,
    EmploymentStatus,
    FINEOSWebIdExt,
    LeaveReason,
    LeaveReasonQualifier,
    Phone,
    RelationshipToCaregiver,
)
from massgov.pfml.db.models.employees import Gender
from massgov.pfml.db.models.factories import (
    AddressFactory,
    ApplicationFactory,
    CaringLeaveMetadataFactory,
    ClaimFactory,
    EmployeeFactory,
    EmployerFactory,
    WagesAndContributionsFactory,
    WorkPatternFixedFactory,
)
from massgov.pfml.fineos.models.customer_api.overrides import AdditionalInformation, Attribute


def test_submit_multiple_applications_same_employee_employer(user, test_db_session):
    employer = EmployerFactory.create()
    employee = EmployeeFactory.create()
    application_one: Application = ApplicationFactory.create(
        user=user, employer_fein=employer.employer_fein, tax_identifier=employee.tax_identifier
    )
    WagesAndContributionsFactory.create(employer=employer, employee=employee)
    application_one.first_name = "First"
    application_one.middle_name = "Middle"
    application_one.last_name = "Last"
    application_one.date_of_birth = date(1977, 7, 27)
    application_one.mass_id = "S12345678"
    application_one.hours_worked_per_week = 70
    application_one.employer_notified = True
    application_one.phone = Phone(phone_number="+12404879945", phone_type_id=1, fineos_phone_id=111)
    application_one.employer_notification_date = date(2021, 1, 7)
    application_one.employment_status_id = EmploymentStatus.UNEMPLOYED.employment_status_id
    application_one.residential_address = AddressFactory.create()
    application_one.gender_id = Gender.WOMAN.gender_id
    application_one.work_pattern = WorkPatternFixedFactory.create()
    application_one.has_continuous_leave_periods = True

    application_two: Application = ApplicationFactory.create(
        user=user, employer_fein=employer.employer_fein, tax_identifier=employee.tax_identifier
    )
    WagesAndContributionsFactory.create(employer=employer, employee=employee)
    application_two.first_name = "First"
    application_two.middle_name = "Middle"
    application_two.last_name = "Last"
    application_two.date_of_birth = date(1977, 7, 27)
    application_two.mass_id = "S12345678"
    application_two.hours_worked_per_week = 70
    application_two.employer_notified = True
    application_two.phone = Phone(phone_number="+12404879945", phone_type_id=1, fineos_phone_id=111)
    application_two.employer_notification_date = date(2021, 1, 7)
    application_two.employment_status_id = EmploymentStatus.UNEMPLOYED.employment_status_id
    application_two.residential_address = AddressFactory.create()
    application_two.gender_id = Gender.WOMAN.gender_id
    application_two.work_pattern = WorkPatternFixedFactory.create()
    application_two.has_continuous_leave_periods = True

    leave_period_one = ContinuousLeavePeriod(
        start_date=date(2021, 1, 1),
        end_date=date(2021, 2, 9),
        application_id=application_one.application_id,
    )
    test_db_session.add(leave_period_one)
    leave_period_two = ContinuousLeavePeriod(
        start_date=date(2021, 1, 1),
        end_date=date(2021, 2, 9),
        application_id=application_two.application_id,
    )
    test_db_session.add(leave_period_two)

    test_db_session.commit()

    massgov.pfml.fineos.mock_client.start_capture()

    with ThreadPoolExecutor() as executor:
        application_service.submit(
            test_db_session, [application_one, application_two], user, executor
        )
    capture = massgov.pfml.fineos.mock_client.get_capture()

    # This is generated randomly and changes each time.
    fineos_user_id = (
        test_db_session.query(FINEOSWebIdExt.fineos_web_id)
        .filter(
            FINEOSWebIdExt.employee_tax_identifier == application_one.tax_identifier.tax_identifier,
            FINEOSWebIdExt.employer_fein == application_one.employer_fein,
        )
        .scalar()
    )
    assert len([call for call in capture if call[0] == "read_employer"]) == 1
    assert ("read_employer", None, {"employer_fein": application_one.employer_fein}) in capture
    _assert_customer_fineos_calls(capture, application_one, fineos_user_id)
    _assert_claim_fineos_call(
        capture,
        application_one,
        fineos_user_id,
        "Sickness",
        "Accident or treatment required for an injury",
        None,
        None,
    )
    _assert_claim_fineos_call(
        capture,
        application_two,
        fineos_user_id,
        "Sickness",
        "Accident or treatment required for an injury",
        None,
        None,
    )
    _assert_fineos_call_count(
        capture,
        [
            ("read_employer", 1),
            ("register_api_user", 1),
            ("update_customer_details", 1),
            ("get_customer_occupations_customer_api", 1),
            ("update_customer_contact_details", 1),
            ("add_week_based_work_pattern", 2),
            ("start_absence", 2),
            ("complete_intake", 2),
        ],
    )


def test_submit_multiple_applications_same_employee_different_employer(user, test_db_session):
    employer_one = EmployerFactory.create()
    employer_two = EmployerFactory.create()
    employee = EmployeeFactory.create()
    application_one: Application = ApplicationFactory.create(
        user=user, employer_fein=employer_one.employer_fein, tax_identifier=employee.tax_identifier
    )
    WagesAndContributionsFactory.create(employer=employer_one, employee=employee)
    application_one.first_name = "First"
    application_one.middle_name = "Middle"
    application_one.last_name = "Last"
    application_one.date_of_birth = date(1977, 7, 27)
    application_one.mass_id = "S12345678"
    application_one.hours_worked_per_week = 70
    application_one.employer_notified = True
    application_one.phone = Phone(phone_number="+12404879945", phone_type_id=1, fineos_phone_id=111)
    application_one.employer_notification_date = date(2021, 1, 7)
    application_one.employment_status_id = EmploymentStatus.UNEMPLOYED.employment_status_id
    application_one.residential_address = AddressFactory.create()
    application_one.gender_id = Gender.WOMAN.gender_id
    application_one.work_pattern = WorkPatternFixedFactory.create()
    application_one.has_continuous_leave_periods = True

    application_two: Application = ApplicationFactory.create(
        user=user, employer_fein=employer_two.employer_fein, tax_identifier=employee.tax_identifier
    )
    WagesAndContributionsFactory.create(employer=employer_two, employee=employee)
    application_two.first_name = "First"
    application_two.middle_name = "Middle"
    application_two.last_name = "Last"
    application_two.date_of_birth = date(1977, 7, 27)
    application_two.mass_id = "S12345678"
    application_two.hours_worked_per_week = 70
    application_two.employer_notified = True
    application_two.phone = Phone(phone_number="+12404879945", phone_type_id=1, fineos_phone_id=111)
    application_two.employer_notification_date = date(2021, 1, 7)
    application_two.employment_status_id = EmploymentStatus.UNEMPLOYED.employment_status_id
    application_two.residential_address = AddressFactory.create()
    application_two.gender_id = Gender.WOMAN.gender_id
    application_two.work_pattern = WorkPatternFixedFactory.create()
    application_two.has_continuous_leave_periods = True

    leave_period_one = ContinuousLeavePeriod(
        start_date=date(2021, 1, 1),
        end_date=date(2021, 2, 9),
        application_id=application_one.application_id,
    )
    test_db_session.add(leave_period_one)
    leave_period_two = ContinuousLeavePeriod(
        start_date=date(2021, 1, 1),
        end_date=date(2021, 2, 9),
        application_id=application_two.application_id,
    )
    test_db_session.add(leave_period_two)

    test_db_session.commit()

    massgov.pfml.fineos.mock_client.start_capture()

    with ThreadPoolExecutor() as executor:
        application_service.submit(
            test_db_session, [application_one, application_two], user, executor
        )
    capture = massgov.pfml.fineos.mock_client.get_capture()
    fineos_user_id_one = (
        test_db_session.query(FINEOSWebIdExt.fineos_web_id)
        .filter(
            FINEOSWebIdExt.employee_tax_identifier == application_one.tax_identifier.tax_identifier,
            FINEOSWebIdExt.employer_fein == application_one.employer_fein,
        )
        .scalar()
    )
    fineos_user_id_two = (
        test_db_session.query(FINEOSWebIdExt.fineos_web_id)
        .filter(
            FINEOSWebIdExt.employee_tax_identifier == application_two.tax_identifier.tax_identifier,
            FINEOSWebIdExt.employer_fein == application_two.employer_fein,
        )
        .scalar()
    )

    assert ("read_employer", None, {"employer_fein": application_one.employer_fein}) in capture
    assert ("read_employer", None, {"employer_fein": application_two.employer_fein}) in capture
    _assert_customer_fineos_calls(capture, application_one, fineos_user_id_one)
    _assert_customer_fineos_calls(capture, application_two, fineos_user_id_two)
    _assert_claim_fineos_call(
        capture,
        application_one,
        fineos_user_id_one,
        "Sickness",
        "Accident or treatment required for an injury",
        None,
        None,
    )
    _assert_claim_fineos_call(
        capture,
        application_two,
        fineos_user_id_two,
        "Sickness",
        "Accident or treatment required for an injury",
        None,
        None,
    )
    _assert_fineos_call_count(
        capture,
        [
            ("read_employer", 2),
            ("register_api_user", 2),
            ("update_customer_details", 2),
            ("get_customer_occupations_customer_api", 2),
            ("update_customer_contact_details", 2),
            ("add_week_based_work_pattern", 2),
            ("start_absence", 2),
            ("complete_intake", 2),
        ],
    )


def test_submit_multiple_applications_different_employee_different_employer(user, test_db_session):
    employer_one = EmployerFactory.create()
    employer_two = EmployerFactory.create()
    employee_one = EmployeeFactory.create()
    employee_two = EmployeeFactory.create()
    application_one: Application = ApplicationFactory.create(
        user=user,
        employer_fein=employer_one.employer_fein,
        tax_identifier=employee_one.tax_identifier,
    )
    WagesAndContributionsFactory.create(employer=employer_one, employee=employee_one)
    application_one.first_name = "First"
    application_one.middle_name = "Middle"
    application_one.last_name = "Last"
    application_one.date_of_birth = date(1977, 7, 27)
    application_one.mass_id = "S12345678"
    application_one.hours_worked_per_week = 70
    application_one.employer_notified = True
    application_one.phone = Phone(phone_number="+12404879945", phone_type_id=1, fineos_phone_id=111)
    application_one.employer_notification_date = date(2021, 1, 7)
    application_one.employment_status_id = EmploymentStatus.UNEMPLOYED.employment_status_id
    application_one.residential_address = AddressFactory.create()
    application_one.gender_id = Gender.WOMAN.gender_id
    application_one.work_pattern = WorkPatternFixedFactory.create()
    application_one.has_continuous_leave_periods = True

    application_two: Application = ApplicationFactory.create(
        user=user,
        employer_fein=employer_two.employer_fein,
        tax_identifier=employee_two.tax_identifier,
    )
    WagesAndContributionsFactory.create(employer=employer_two, employee=employee_two)
    application_two.first_name = "First"
    application_two.middle_name = "Middle"
    application_two.last_name = "Last"
    application_two.date_of_birth = date(1977, 7, 27)
    application_two.mass_id = "S12345678"
    application_two.hours_worked_per_week = 70
    application_two.employer_notified = True
    application_two.phone = Phone(phone_number="+12404879945", phone_type_id=1, fineos_phone_id=111)
    application_two.employer_notification_date = date(2021, 1, 7)
    application_two.employment_status_id = EmploymentStatus.UNEMPLOYED.employment_status_id
    application_two.residential_address = AddressFactory.create()
    application_two.gender_id = Gender.WOMAN.gender_id
    application_two.work_pattern = WorkPatternFixedFactory.create()
    application_two.has_continuous_leave_periods = True

    leave_period_one = ContinuousLeavePeriod(
        start_date=date(2021, 1, 1),
        end_date=date(2021, 2, 9),
        application_id=application_one.application_id,
    )
    test_db_session.add(leave_period_one)
    leave_period_two = ContinuousLeavePeriod(
        start_date=date(2021, 1, 1),
        end_date=date(2021, 2, 9),
        application_id=application_two.application_id,
    )
    test_db_session.add(leave_period_two)

    test_db_session.commit()

    massgov.pfml.fineos.mock_client.start_capture()

    with ThreadPoolExecutor() as executor:
        application_service.submit(
            test_db_session, [application_one, application_two], user, executor
        )
    capture = massgov.pfml.fineos.mock_client.get_capture()
    fineos_user_id_one = (
        test_db_session.query(FINEOSWebIdExt.fineos_web_id)
        .filter(
            FINEOSWebIdExt.employee_tax_identifier == application_one.tax_identifier.tax_identifier,
            FINEOSWebIdExt.employer_fein == application_one.employer_fein,
        )
        .scalar()
    )
    fineos_user_id_two = (
        test_db_session.query(FINEOSWebIdExt.fineos_web_id)
        .filter(
            FINEOSWebIdExt.employee_tax_identifier == application_two.tax_identifier.tax_identifier,
            FINEOSWebIdExt.employer_fein == application_two.employer_fein,
        )
        .scalar()
    )

    assert ("read_employer", None, {"employer_fein": application_one.employer_fein}) in capture
    _assert_customer_fineos_calls(capture, application_one, fineos_user_id_one)
    _assert_customer_fineos_calls(capture, application_two, fineos_user_id_two)
    _assert_claim_fineos_call(
        capture,
        application_one,
        fineos_user_id_one,
        "Sickness",
        "Accident or treatment required for an injury",
        None,
        None,
    )
    _assert_claim_fineos_call(
        capture,
        application_two,
        fineos_user_id_two,
        "Sickness",
        "Accident or treatment required for an injury",
        None,
        None,
    )
    _assert_fineos_call_count(
        capture,
        [
            ("read_employer", 2),
            ("register_api_user", 2),
            ("update_customer_details", 2),
            ("get_customer_occupations_customer_api", 2),
            ("update_customer_contact_details", 2),
            ("add_week_based_work_pattern", 2),
            ("start_absence", 2),
            ("complete_intake", 2),
        ],
    )


def test_submit_only_calls_complete_intake_if_claim_exists(user, test_db_session):
    employer = EmployerFactory.create()
    employee = EmployeeFactory.create()
    application: Application = ApplicationFactory.create(
        user=user, employer_fein=employer.employer_fein, tax_identifier=employee.tax_identifier
    )
    claim = ClaimFactory.create(
        fineos_notification_id="NTN-1989", fineos_absence_id="NTN-1989-ABS-01"
    )
    WagesAndContributionsFactory.create(employer=employer, employee=employee)
    application.first_name = "First"
    application.middle_name = "Middle"
    application.last_name = "Last"
    application.date_of_birth = date(1977, 7, 27)
    application.mass_id = "S12345678"
    application.hours_worked_per_week = 70
    application.employer_notified = True
    application.phone = Phone(phone_number="+12404879945", phone_type_id=1, fineos_phone_id=111)
    application.employer_notification_date = date(2021, 1, 7)
    application.employment_status_id = EmploymentStatus.UNEMPLOYED.employment_status_id
    application.residential_address = AddressFactory.create()
    application.gender_id = Gender.WOMAN.gender_id
    application.work_pattern = WorkPatternFixedFactory.create()
    application.has_continuous_leave_periods = True
    application.claim = claim

    leave_period = ContinuousLeavePeriod(
        start_date=date(2021, 1, 1),
        end_date=date(2021, 2, 9),
        application_id=application.application_id,
    )
    test_db_session.add(leave_period)

    test_db_session.commit()

    massgov.pfml.fineos.mock_client.start_capture()

    with ThreadPoolExecutor() as executor:
        application_service.submit(test_db_session, [application], user, executor)
    capture = massgov.pfml.fineos.mock_client.get_capture()
    # This is generated randomly and changes each time.
    fineos_user_id = capture[2][1]
    # Capture contains a find_employer call and the complete_intake call
    assert capture == [
        ("read_employer", None, {"employer_fein": application.employer_fein}),
        (
            "register_api_user",
            None,
            {
                "employee_registration": massgov.pfml.fineos.models.EmployeeRegistration(
                    user_id=fineos_user_id,
                    customer_number=None,
                    employer_id=str(
                        massgov.pfml.fineos.mock.field.fake_customer_no(application.employer_fein)
                    ),
                    date_of_birth=date(1753, 1, 1),
                    email=None,
                    first_name=None,
                    last_name=None,
                    national_insurance_no=application.tax_identifier.tax_identifier,
                )
            },
        ),
        ("complete_intake", fineos_user_id, {"notification_case_id": "NTN-1989"}),
    ]


def test_submit_with_reflexive_questions(user, test_db_session):
    employer = EmployerFactory.create()
    employee = EmployeeFactory.create()
    application_one: Application = ApplicationFactory.create(
        user=user, employer_fein=employer.employer_fein, tax_identifier=employee.tax_identifier
    )
    WagesAndContributionsFactory.create(employer=employer, employee=employee)
    application_one.first_name = "First"
    application_one.middle_name = "Middle"
    application_one.last_name = "Last"
    application_one.date_of_birth = date(1977, 7, 27)
    application_one.mass_id = "S12345678"
    application_one.hours_worked_per_week = 70
    application_one.employer_notified = True
    application_one.phone = Phone(phone_number="+12404879945", phone_type_id=1, fineos_phone_id=111)
    application_one.employer_notification_date = date(2021, 1, 7)
    application_one.employment_status_id = EmploymentStatus.UNEMPLOYED.employment_status_id
    application_one.residential_address = AddressFactory.create()
    application_one.gender_id = Gender.WOMAN.gender_id
    application_one.work_pattern = WorkPatternFixedFactory.create()
    application_one.has_continuous_leave_periods = True
    application_one.leave_reason_id = LeaveReason.CHILD_BONDING.leave_reason_id
    application_one.leave_reason_qualifier_id = (
        LeaveReasonQualifier.NEWBORN.leave_reason_qualifier_id
    )

    leave_period_one = ContinuousLeavePeriod(
        start_date=date(2021, 1, 1),
        end_date=date(2021, 2, 9),
        application_id=application_one.application_id,
    )

    application_two: Application = ApplicationFactory.create(
        user=user, employer_fein=employer.employer_fein, tax_identifier=employee.tax_identifier
    )
    WagesAndContributionsFactory.create(employer=employer, employee=employee)
    application_two.first_name = "First"
    application_two.middle_name = "Middle"
    application_two.last_name = "Last"
    application_two.date_of_birth = date(1977, 7, 27)
    application_two.mass_id = "S12345678"
    application_two.hours_worked_per_week = 70
    application_two.employer_notified = True
    application_two.phone = Phone(phone_number="+12404879945", phone_type_id=1, fineos_phone_id=111)
    application_two.employer_notification_date = date(2021, 1, 7)
    application_two.employment_status_id = EmploymentStatus.UNEMPLOYED.employment_status_id
    application_two.residential_address = AddressFactory.create()
    application_two.gender_id = Gender.WOMAN.gender_id
    application_two.work_pattern = WorkPatternFixedFactory.create()
    application_two.has_continuous_leave_periods = True
    application_two.leave_reason_id = LeaveReason.CARE_FOR_A_FAMILY_MEMBER.leave_reason_id
    application_two.caring_leave_metadata = CaringLeaveMetadataFactory.create()
    application_two.leave_reason_qualifier_id = (
        LeaveReasonQualifier.SERIOUS_HEALTH_CONDITION.leave_reason_qualifier_id
    )
    application_two.caring_leave_metadata.relationship_to_caregiver_id = (
        RelationshipToCaregiver.PARENT.relationship_to_caregiver_id
    )

    leave_period_two = ContinuousLeavePeriod(
        start_date=date(2021, 1, 1),
        end_date=date(2021, 2, 9),
        application_id=application_two.application_id,
    )
    test_db_session.add(leave_period_one)
    test_db_session.add(leave_period_two)

    test_db_session.commit()

    massgov.pfml.fineos.mock_client.start_capture()

    with ThreadPoolExecutor() as executor:
        application_service.submit(
            test_db_session, [application_one, application_two], user, executor
        )

    assert application_one.submitted_time is not None
    assert application_one.claim is not None
    capture = massgov.pfml.fineos.mock_client.get_capture()

    # This is generated randomly and changes each time.
    fineos_user_id = (
        test_db_session.query(FINEOSWebIdExt.fineos_web_id)
        .filter(
            FINEOSWebIdExt.employee_tax_identifier == application_one.tax_identifier.tax_identifier,
            FINEOSWebIdExt.employer_fein == application_one.employer_fein,
        )
        .scalar()
    )

    assert ("read_employer", None, {"employer_fein": application_one.employer_fein}) in capture
    _assert_customer_fineos_calls(capture, application_one, fineos_user_id)
    _assert_claim_fineos_call(
        capture,
        application_one,
        fineos_user_id,
        None,
        "Bonding with a new child (adoption/ foster care/ newborn)",
        "Child",
        "Biological",
    )
    _assert_claim_fineos_call(
        capture,
        application_two,
        fineos_user_id,
        None,
        "Caring for a family member",
        "Parent",
        "Biological",
    )
    assert (
        "update_reflexive_questions",
        fineos_user_id,
        {
            "absence_id": application_one.claim.fineos_absence_id,
            "additional_information": AdditionalInformation(
                reflexiveQuestionLevel="reason",
                reflexiveQuestionDetails=[
                    Attribute(
                        fieldName="FamilyMemberDetailsQuestionGroup.familyMemberDetailsQuestions.dateOfBirth",
                        booleanValue=None,
                        dateValue=None,
                        decimalValue=None,
                        integerValue=None,
                        stringValue=None,
                        enumValue=None,
                    )
                ],
            ),
        },
    ) in capture
    assert (
        "update_reflexive_questions",
        fineos_user_id,
        {
            "absence_id": application_two.claim.fineos_absence_id,
            "additional_information": AdditionalInformation(
                reflexiveQuestionLevel="primary relationship",
                reflexiveQuestionDetails=[
                    Attribute(
                        fieldName="FamilyMemberDetailsQuestionGroup.familyMemberDetailsQuestions.firstName",
                        booleanValue=None,
                        dateValue=None,
                        decimalValue=None,
                        integerValue=None,
                        stringValue=application_two.caring_leave_metadata.family_member_first_name,
                        enumValue=None,
                    ),
                    Attribute(
                        fieldName="FamilyMemberDetailsQuestionGroup.familyMemberDetailsQuestions.middleInital",
                        booleanValue=None,
                        dateValue=None,
                        decimalValue=None,
                        integerValue=None,
                        stringValue=application_two.caring_leave_metadata.family_member_middle_name,
                        enumValue=None,
                    ),
                    Attribute(
                        fieldName="FamilyMemberDetailsQuestionGroup.familyMemberDetailsQuestions.lastName",
                        booleanValue=None,
                        dateValue=None,
                        decimalValue=None,
                        integerValue=None,
                        stringValue=application_two.caring_leave_metadata.family_member_last_name,
                        enumValue=None,
                    ),
                    Attribute(
                        fieldName="FamilyMemberDetailsQuestionGroup.familyMemberDetailsQuestions.dateOfBirth",
                        booleanValue=None,
                        dateValue=application_two.caring_leave_metadata.family_member_date_of_birth,
                        decimalValue=None,
                        integerValue=None,
                        stringValue=None,
                        enumValue=None,
                    ),
                ],
            ),
        },
    ) in capture
    _assert_fineos_call_count(
        capture,
        [
            ("read_employer", 1),
            ("register_api_user", 1),
            ("update_customer_details", 1),
            ("get_customer_occupations_customer_api", 1),
            ("update_customer_contact_details", 1),
            ("add_week_based_work_pattern", 2),
            ("start_absence", 2),
            ("update_reflexive_questions", 2),
            ("complete_intake", 2),
        ],
    )


def test_submit_one_application(user, test_db_session):
    employer = EmployerFactory.create()
    employee = EmployeeFactory.create()
    application: Application = ApplicationFactory.create(
        user=user, employer_fein=employer.employer_fein, tax_identifier=employee.tax_identifier
    )
    WagesAndContributionsFactory.create(employer=employer, employee=employee)
    application.first_name = "First"
    application.middle_name = "Middle"
    application.last_name = "Last"
    application.date_of_birth = date(1977, 7, 27)
    application.mass_id = "S12345678"
    application.hours_worked_per_week = 70
    application.employer_notified = True
    application.phone = Phone(phone_number="+12404879945", phone_type_id=1, fineos_phone_id=111)
    application.employer_notification_date = date(2021, 1, 7)
    application.employment_status_id = EmploymentStatus.UNEMPLOYED.employment_status_id
    application.residential_address = AddressFactory.create()
    application.gender_id = Gender.WOMAN.gender_id
    application.work_pattern = WorkPatternFixedFactory.create()
    application.has_continuous_leave_periods = True

    leave_period = ContinuousLeavePeriod(
        start_date=date(2021, 1, 1),
        end_date=date(2021, 2, 9),
        application_id=application.application_id,
    )
    test_db_session.add(leave_period)

    test_db_session.commit()

    massgov.pfml.fineos.mock_client.start_capture()

    with ThreadPoolExecutor() as executor:
        application_service.submit(test_db_session, [application], user, executor)

    assert application.submitted_time is not None
    assert application.claim is not None
    capture = massgov.pfml.fineos.mock_client.get_capture()

    # This is generated randomly and changes each time.
    fineos_user_id = (
        test_db_session.query(FINEOSWebIdExt.fineos_web_id)
        .filter(
            FINEOSWebIdExt.employee_tax_identifier == application.tax_identifier.tax_identifier,
            FINEOSWebIdExt.employer_fein == application.employer_fein,
        )
        .scalar()
    )

    assert ("read_employer", None, {"employer_fein": application.employer_fein}) in capture
    _assert_customer_fineos_calls(capture, application, fineos_user_id)
    _assert_claim_fineos_call(
        capture,
        application,
        fineos_user_id,
        "Sickness",
        "Accident or treatment required for an injury",
        None,
        None,
    )
    _assert_fineos_call_count(
        capture,
        [
            ("read_employer", 1),
            ("register_api_user", 1),
            ("update_customer_details", 1),
            ("get_customer_occupations_customer_api", 1),
            ("update_customer_contact_details", 1),
            ("add_week_based_work_pattern", 1),
            ("start_absence", 1),
            ("complete_intake", 1),
        ],
    )


def _assert_claim_fineos_call(
    capture,
    application,
    fineos_user_id,
    reason_qualifier_2,
    notification_reason,
    primary_relationship=None,
    primary_rel_qualifier=None,
):
    assert (
        "add_week_based_work_pattern",
        fineos_user_id,
        {
            "week_based_work_pattern": massgov.pfml.fineos.models.customer_api.WeekBasedWorkPattern(
                workPatternType="Fixed",
                workWeekStarts="Sunday",
                patternStartDate=None,
                patternStatus=None,
                workPatternDays=[
                    massgov.pfml.fineos.models.customer_api.WorkPatternDay(
                        dayOfWeek="Sunday", weekNumber=1, hours=8, minutes=15
                    ),
                    massgov.pfml.fineos.models.customer_api.WorkPatternDay(
                        dayOfWeek="Monday", weekNumber=1, hours=8, minutes=15
                    ),
                    massgov.pfml.fineos.models.customer_api.WorkPatternDay(
                        dayOfWeek="Tuesday", weekNumber=1, hours=8, minutes=15
                    ),
                    massgov.pfml.fineos.models.customer_api.WorkPatternDay(
                        dayOfWeek="Wednesday", weekNumber=1, hours=8, minutes=15
                    ),
                    massgov.pfml.fineos.models.customer_api.WorkPatternDay(
                        dayOfWeek="Thursday", weekNumber=1, hours=8, minutes=15
                    ),
                    massgov.pfml.fineos.models.customer_api.WorkPatternDay(
                        dayOfWeek="Friday", weekNumber=1, hours=8, minutes=15
                    ),
                    massgov.pfml.fineos.models.customer_api.WorkPatternDay(
                        dayOfWeek="Saturday", weekNumber=1, hours=8, minutes=15
                    ),
                ],
            )
        },
    ) in capture
    assert (
        "start_absence",
        fineos_user_id,
        {
            "absence_case": massgov.pfml.fineos.models.customer_api.AbsenceCase(
                additionalComments="PFML API " + str(application.application_id),
                intakeSource="Self-Service",
                notifiedBy="Employee",
                reason=application.leave_reason.leave_reason_description
                if application.leave_reason
                else None,
                reasonQualifier1=application.leave_reason_qualifier.leave_reason_qualifier_description
                if application.leave_reason_qualifier
                else "Not Work Related",
                reasonQualifier2=reason_qualifier_2,
                notificationReason=notification_reason,
                primaryRelationship=primary_relationship,
                primaryRelQualifier1=primary_rel_qualifier,
                primaryRelQualifier2=None,
                timeOffLeavePeriods=[
                    massgov.pfml.fineos.models.customer_api.TimeOffLeavePeriod(
                        startDate=date(2021, 1, 1),
                        endDate=date(2021, 2, 9),
                        startDateFullDay=True,
                        endDateFullDay=True,
                        status="known",
                    )
                ],
                employerNotified=True,
                employerNotificationDate=date(2021, 1, 7),
                employerNotificationMethod=None,
            )
        },
    ) in capture
    assert (
        "complete_intake",
        fineos_user_id,
        {"notification_case_id": application.claim.fineos_notification_id},
    ) in capture


def _assert_customer_fineos_calls(capture, application, fineos_user_id):
    assert (
        "register_api_user",
        None,
        {
            "employee_registration": massgov.pfml.fineos.models.EmployeeRegistration(
                user_id=fineos_user_id,
                employer_id=str(
                    massgov.pfml.fineos.mock.field.fake_customer_no(application.employer_fein)
                ),
                date_of_birth=date(1753, 1, 1),
                national_insurance_no=application.tax_identifier.tax_identifier,
            )
        },
    ) in capture
    assert (
        "update_customer_details",
        fineos_user_id,
        {
            "customer": massgov.pfml.fineos.models.customer_api.Customer(
                firstName="First",
                lastName="Last",
                secondName="Middle",
                dateOfBirth=date(1977, 7, 27),
                idNumber=application.tax_identifier.tax_identifier,
                customerAddress=massgov.pfml.fineos.models.customer_api.CustomerAddress(
                    address=massgov.pfml.fineos.models.customer_api.Address(
                        addressLine1=application.residential_address.address_line_one,
                        addressLine2=application.residential_address.address_line_two,
                        addressLine4=application.residential_address.city,
                        addressLine6=application.residential_address.geo_state.geo_state_description,
                        postCode=application.residential_address.zip_code,
                        country="USA",
                    )
                ),
                gender="Female",
                classExtensionInformation=[
                    massgov.pfml.fineos.models.customer_api.ExtensionAttribute(
                        name="MassachusettsID", stringValue=application.mass_id
                    ),
                    massgov.pfml.fineos.models.customer_api.ExtensionAttribute(
                        name="Confirmed", booleanValue=True
                    ),
                    massgov.pfml.fineos.models.customer_api.ExtensionAttribute(
                        name="ConsenttoShareData", booleanValue=False
                    ),
                ],
            )
        },
    ) in capture
    assert (
        "get_customer_occupations_customer_api",
        fineos_user_id,
        {"customer_id": application.tax_identifier.tax_identifier},
    ) in capture
    assert (
        "update_customer_contact_details",
        fineos_user_id,
        {
            "contact_details": massgov.pfml.fineos.models.customer_api.ContactDetails(
                phoneNumbers=[
                    massgov.pfml.fineos.models.customer_api.PhoneNumber(
                        id=111,
                        preferred=None,
                        phoneNumberType="Cell",
                        intCode="1",
                        areaCode="240",
                        telephoneNo="4879945",
                        classExtensionInformation=None,
                    )
                ],
                emailAddresses=[
                    massgov.pfml.fineos.models.customer_api.EmailAddressV20(
                        emailAddress=application.user.email_address
                    )
                ],
            )
        },
    ) in capture


def _assert_fineos_call_count(capture, expected_counts):
    for (call_name, expected_count) in expected_counts:
        assert len([call for call in capture if call[0] == call_name]) == expected_count
