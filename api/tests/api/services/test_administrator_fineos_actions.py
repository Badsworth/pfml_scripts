import logging  # noqa: B1
from datetime import date

import pytest

import massgov.pfml.fineos.mock_client
from massgov.pfml.api.services.administrator_fineos_actions import (
    EFORM_TYPES,
    get_claim_as_leave_admin,
    get_leave_details,
    register_leave_admin_with_fineos,
)
from massgov.pfml.db.models.employees import UserLeaveAdministrator
from massgov.pfml.db.models.factories import EmployerFactory
from massgov.pfml.fineos import FINEOSClient, create_client
from massgov.pfml.fineos.models import CreateOrUpdateLeaveAdmin, group_client_api


@pytest.fixture
def period_decisions():
    return group_client_api.PeriodDecisions.parse_obj(
        {
            "startDate": "2021-01-04",
            "endDate": "2021-02-24",
            "decisions": [
                {
                    "absence": {"id": "NTN-3769-ABS-01", "caseReference": "NTN-3769-ABS-01"},
                    "employee": {"id": "2957", "name": "Emilie Muller"},
                    "period": {
                        "periodReference": "PL-14448-0000004930",
                        "parentPeriodReference": "",
                        "relatedToEpisodic": True,
                        "startDate": "2021-01-15",
                        "endDate": "2021-01-20",
                        "balanceDeduction": 0,
                        "timeRequested": "",
                        "timeDeducted": "",
                        "timeDeductedBasis": "",
                        "timeDecisionStatus": "",
                        "timeDecisionReason": "",
                        "type": "Episodic",
                        "status": "Known",
                        "leavePlan": {
                            "id": "abdc368f-ace6-4d6a-b697-f1016fe8a314",
                            "name": "MA PFML - Employee",
                            "shortName": "MA PFML - Employee",
                            "applicabilityStatus": "Applicable",
                            "eligibilityStatus": "Not Known",
                            "availabilityStatus": "N/A",
                            "adjudicationStatus": "Undecided",
                            "evidenceStatus": "Pending",
                            "category": "Paid",
                            "calculationPeriodMethod": "Rolling Forward - Sunday",
                            "timeBankMethod": "Length / Duration",
                            "timeWithinPeriod": 52,
                            "timeWithinPeriodBasis": "Weeks",
                            "fixedYearStartDay": 0,
                            "fixedYearStartMonth": "Please Select",
                            "timeEntitlement": 20,
                            "timeEntitlementBasis": "Weeks",
                            "paidLeaveCaseId": "",
                        },
                        "leaveRequest": {
                            "id": "PL-14432-0000006172",
                            "reasonName": "Serious Health Condition - Employee",
                            "qualifier1": "Not Work Related",
                            "qualifier2": "Accident / Injury",
                            "decisionStatus": "Pending",
                            "approvalReason": "Please Select",
                            "denialReason": "Please Select",
                        },
                    },
                },
                {
                    "absence": {"id": "NTN-3769-ABS-01", "caseReference": "NTN-3769-ABS-01"},
                    "employee": {"id": "2957", "name": "Emilie Muller"},
                    "period": {
                        "periodReference": "PL-14448-0000004930",
                        "parentPeriodReference": "",
                        "relatedToEpisodic": False,
                        "startDate": "2021-01-04",
                        "endDate": "2021-01-29",
                        "balanceDeduction": 0,
                        "timeRequested": "",
                        "timeDeducted": "",
                        "timeDeductedBasis": "",
                        "timeDecisionStatus": "",
                        "timeDecisionReason": "",
                        "type": "Reduced Schedule",
                        "status": "Known",
                        "leavePlan": {
                            "id": "abdc368f-ace6-4d6a-b697-f1016fe8a314",
                            "name": "MA PFML - Employee",
                            "shortName": "MA PFML - Employee",
                            "applicabilityStatus": "Applicable",
                            "eligibilityStatus": "Not Known",
                            "availabilityStatus": "N/A",
                            "adjudicationStatus": "Undecided",
                            "evidenceStatus": "Pending",
                            "category": "Paid",
                            "calculationPeriodMethod": "Rolling Forward - Sunday",
                            "timeBankMethod": "Length / Duration",
                            "timeWithinPeriod": 52,
                            "timeWithinPeriodBasis": "Weeks",
                            "fixedYearStartDay": 0,
                            "fixedYearStartMonth": "Please Select",
                            "timeEntitlement": 20,
                            "timeEntitlementBasis": "Weeks",
                            "paidLeaveCaseId": "",
                        },
                        "leaveRequest": {
                            "id": "PL-14432-0000006172",
                            "reasonName": "Serious Health Condition - Employee",
                            "qualifier1": "Not Work Related",
                            "qualifier2": "Accident / Injury",
                            "decisionStatus": "Pending",
                            "approvalReason": "Please Select",
                            "denialReason": "Please Select",
                        },
                    },
                },
                {
                    "absence": {"id": "NTN-3769-ABS-01", "caseReference": "NTN-3769-ABS-01"},
                    "employee": {"id": "2957", "name": "Emilie Muller"},
                    "period": {
                        "periodReference": "PL-14449-0000007164",
                        "parentPeriodReference": "",
                        "relatedToEpisodic": False,
                        "startDate": "2021-02-01",
                        "endDate": "2021-02-24",
                        "balanceDeduction": 0,
                        "timeRequested": "",
                        "timeDeducted": "",
                        "timeDeductedBasis": "",
                        "timeDecisionStatus": "",
                        "timeDecisionReason": "",
                        "type": "Time off period",
                        "status": "Known",
                        "leavePlan": {
                            "id": "abdc368f-ace6-4d6a-b697-f1016fe8a314",
                            "name": "MA PFML - Employee",
                            "shortName": "MA PFML - Employee",
                            "applicabilityStatus": "Applicable",
                            "eligibilityStatus": "Not Known",
                            "availabilityStatus": "N/A",
                            "adjudicationStatus": "Undecided",
                            "evidenceStatus": "Pending",
                            "category": "Paid",
                            "calculationPeriodMethod": "Rolling Forward - Sunday",
                            "timeBankMethod": "Length / Duration",
                            "timeWithinPeriod": 52,
                            "timeWithinPeriodBasis": "Weeks",
                            "fixedYearStartDay": 0,
                            "fixedYearStartMonth": "Please Select",
                            "timeEntitlement": 20,
                            "timeEntitlementBasis": "Weeks",
                            "paidLeaveCaseId": "",
                        },
                        "leaveRequest": {
                            "id": "PL-14432-0000006172",
                            "reasonName": "Serious Health Condition - Employee",
                            "qualifier1": "Not Work Related",
                            "qualifier2": "Accident / Injury",
                            "decisionStatus": "Pending",
                            "approvalReason": "Please Select",
                            "denialReason": "Please Select",
                        },
                    },
                },
            ],
        }
    )


@pytest.fixture
def period_decisions_no_plan():
    return group_client_api.PeriodDecisions.parse_obj(
        {
            "startDate": "2021-01-01",
            "endDate": "2021-01-31",
            "decisions": [
                {
                    "absence": {"id": "NTN-111111-ABS-01", "caseReference": "NTN-111111-ABS-01"},
                    "employee": {"id": "111222333", "name": "Fake Person"},
                    "period": {
                        "periodReference": "PL-00000-0000000000",
                        "parentPeriodReference": "",
                        "relatedToEpisodic": False,
                        "startDate": "2021-01-01",
                        "endDate": "2021-01-31",
                        "balanceDeduction": 0,
                        "timeRequested": "",
                        "timeDeducted": "",
                        "timeDeductedBasis": "",
                        "timeDecisionStatus": "",
                        "timeDecisionReason": "",
                        "type": "Time off period",
                        "status": "Known",
                        "leaveRequest": {
                            "id": "PL-00000-0000000000",
                            "reasonName": "Child Bonding",
                            "qualifier1": "Newborn",
                            "qualifier2": "",
                            "decisionStatus": "Denied",
                            "approvalReason": "Please Select",
                            "denialReason": "No Applicable Plans",
                        },
                    },
                }
            ],
        }
    )


def mock_fineos_client_period_decisions(period_decisions_data):
    def mock_period_decisions(*args, **kwargs):
        return period_decisions_data

    mock_client = create_client()
    mock_client.get_absence_period_decisions = mock_period_decisions
    return mock_client


@pytest.fixture
def mock_fineos_period_decisions_no_plan(period_decisions_no_plan):
    return mock_fineos_client_period_decisions(period_decisions_no_plan)


@pytest.fixture
def mock_fineos_period_decisions(period_decisions):
    return mock_fineos_client_period_decisions(period_decisions)


@pytest.fixture
def mock_fineos_other_leaves_eform_both_versions(period_decisions):
    def mock_eform_summary(*args, **kwargs):
        return [
            group_client_api.EFormSummary(eformId=12345, eformType=EFORM_TYPES["OTHER_LEAVES"]),
            group_client_api.EFormSummary(eformId=12354, eformType=EFORM_TYPES["OTHER_LEAVES_V2"]),
        ]

    mock_client = create_client()
    mock_client.get_eform_summary = mock_eform_summary

    return mock_client


@pytest.fixture
def mock_fineos_other_income_eform_both_versions(period_decisions):
    def mock_eform_summary(*args, **kwargs):
        return [
            group_client_api.EFormSummary(eformId=12345, eformType=EFORM_TYPES["OTHER_INCOME"]),
            group_client_api.EFormSummary(eformId=12354, eformType=EFORM_TYPES["OTHER_INCOME_V2"]),
        ]

    mock_client = create_client()
    mock_client.get_eform_summary = mock_eform_summary

    return mock_client


def test_create_leave_admin_request_payload():
    create_or_update_request = CreateOrUpdateLeaveAdmin(
        fineos_web_id="testID",
        fineos_employer_id=1005,
        admin_full_name="Bob Smith",
        admin_area_code="817",
        admin_phone_number="1234560",
        admin_email="test@test.com",
    )
    payload = FINEOSClient._create_or_update_leave_admin_payload(create_or_update_request)

    assert payload is not None
    assert payload.__contains__("<ns0:partyReference>1005</ns0:partyReference>")
    assert payload.__contains__("<ns0:userID>testID</ns0:userID>")
    assert payload.__contains__("<ns0:fullName>Bob Smith</ns0:fullName>")
    assert payload.__contains__("<ns0:contactAreaCode>817</ns0:contactAreaCode>")
    assert payload.__contains__("<ns0:contactNumber>1234560</ns0:contactNumber>")
    assert payload.__contains__("<ns0:userRole>AllPermissions</ns0:userRole>")
    assert payload.__contains__("<ns0:enabled>true</ns0:enabled>")


@pytest.mark.integration
def test_register_leave_admin_with_fineos(employer_user, test_db_session):
    employer = EmployerFactory.create()
    register_leave_admin_with_fineos(
        "Bob Smith",
        "test@test.com",
        "817",
        "1234560",
        employer,
        employer_user,
        test_db_session,
        None,
    )
    created_leave_admin = (
        test_db_session.query(UserLeaveAdministrator)
        .filter(UserLeaveAdministrator.user_id == employer_user.user_id)
        .one()
    )

    assert created_leave_admin is not None
    assert created_leave_admin.fineos_web_id.startswith("pfml_leave_admin_")
    assert created_leave_admin.employer_id == employer.employer_id


@pytest.mark.integration
def test_register_previously_registered_leave_admin_with_fineos(
    employer_user, test_db_session, caplog
):
    employer = EmployerFactory.create()
    ula = UserLeaveAdministrator(
        user=employer_user, employer=employer, fineos_web_id="EXISTING_USER"
    )
    test_db_session.add(ula)
    test_db_session.commit()
    fineos_client = create_client()
    caplog.set_level(logging.INFO)  # noqa: B1
    capture = massgov.pfml.fineos.mock_client.start_capture()

    register_leave_admin_with_fineos(
        admin_full_name="Bob Smith",
        admin_email="test@test.com",
        admin_area_code="817",
        admin_phone_number="1234560",
        employer=employer,
        user=employer_user,
        db_session=test_db_session,
        fineos_client=fineos_client,
        force_register=False,
    )

    assert "User previously registered in FINEOS and force_register off" in caplog.text

    capture = massgov.pfml.fineos.mock_client.get_capture()
    # Assert no calls to FINEOS made
    assert not capture
    created_leave_admin = (
        test_db_session.query(UserLeaveAdministrator)
        .filter(UserLeaveAdministrator.user_id == employer_user.user_id)
        .one()
    )

    assert created_leave_admin is not None
    assert created_leave_admin.fineos_web_id == "EXISTING_USER"
    caplog.clear()
    register_leave_admin_with_fineos(
        admin_full_name="Bob Smith",
        admin_email="test@test.com",
        admin_area_code="817",
        admin_phone_number="1234560",
        employer=employer,
        user=employer_user,
        db_session=test_db_session,
        fineos_client=fineos_client,
        force_register=True,
    )
    capture = massgov.pfml.fineos.mock_client.get_capture()
    assert capture[0][0] == "create_or_update_leave_admin"

    created_leave_admin = (
        test_db_session.query(UserLeaveAdministrator)
        .filter(UserLeaveAdministrator.user_id == employer_user.user_id)
        .one()
    )
    assert created_leave_admin.fineos_web_id != "EXISTING_USER"
    assert created_leave_admin.fineos_web_id.startswith("pfml_leave_admin_")


def test_get_leave_details(period_decisions):
    leave_details = get_leave_details(period_decisions.dict())

    assert leave_details.continuous_leave_periods[0].start_date == date(2021, 2, 1)
    assert leave_details.continuous_leave_periods[0].end_date == date(2021, 2, 24)
    assert leave_details.intermittent_leave_periods[0].start_date == date(2021, 1, 1)
    assert leave_details.intermittent_leave_periods[0].end_date == date(2021, 2, 1)
    assert leave_details.reduced_schedule_leave_periods[0].start_date == date(2021, 1, 4)
    assert leave_details.reduced_schedule_leave_periods[0].end_date == date(2021, 1, 29)


@pytest.mark.integration
def test_get_claim_plan(mock_fineos_period_decisions, initialize_factories_session):
    fineos_user_id = "Friendly_HR"
    absence_id = "NTN-001-ABS-001"
    employer = EmployerFactory.create()
    leave_details = get_claim_as_leave_admin(
        fineos_user_id, absence_id, employer, fineos_client=mock_fineos_period_decisions
    )
    assert leave_details.status == "Known"


@pytest.mark.integration
def test_get_claim_no_plan(mock_fineos_period_decisions_no_plan, initialize_factories_session):
    fineos_user_id = "Friendly_HR"
    absence_id = "NTN-001-ABS-001"
    employer = EmployerFactory.create()
    leave_details = get_claim_as_leave_admin(
        fineos_user_id, absence_id, employer, fineos_client=mock_fineos_period_decisions_no_plan
    )
    assert leave_details.status == "Known"


@pytest.mark.integration
def test_get_claim_eform_type_contains_neither_version(
    mock_fineos_period_decisions, initialize_factories_session
):
    fineos_user_id = "Friendly_HR"
    absence_id = "NTN-001-ABS-001"
    employer = EmployerFactory.create()
    leave_details = get_claim_as_leave_admin(
        fineos_user_id, absence_id, employer, fineos_client=mock_fineos_period_decisions
    )
    assert leave_details.contains_version_one_eforms is False
    assert leave_details.contains_version_two_eforms is False


@pytest.mark.integration
def test_get_claim_other_leaves_eform_type_contains_both_versions(
    mock_fineos_other_leaves_eform_both_versions, initialize_factories_session
):
    fineos_user_id = "Friendly_HR"
    absence_id = "NTN-001-ABS-001"
    employer = EmployerFactory.create()
    leave_details = get_claim_as_leave_admin(
        fineos_user_id,
        absence_id,
        employer,
        fineos_client=mock_fineos_other_leaves_eform_both_versions,
    )
    assert leave_details.contains_version_one_eforms is True
    assert leave_details.contains_version_two_eforms is True


@pytest.mark.integration
def test_get_claim_other_income_eform_type_contains_both_versions(
    mock_fineos_other_income_eform_both_versions, initialize_factories_session
):
    fineos_user_id = "Friendly_HR"
    absence_id = "NTN-001-ABS-001"
    employer = EmployerFactory.create()
    leave_details = get_claim_as_leave_admin(
        fineos_user_id,
        absence_id,
        employer,
        fineos_client=mock_fineos_other_income_eform_both_versions,
    )
    assert leave_details.contains_version_one_eforms is True
    assert leave_details.contains_version_two_eforms is True
