from datetime import date

import pytest

from massgov.pfml.api.services.administrator_fineos_actions import (
    get_leave_details,
    register_leave_admin_with_fineos,
)
from massgov.pfml.db.models.employees import UserLeaveAdministrator
from massgov.pfml.db.models.factories import EmployerFactory
from massgov.pfml.fineos import FINEOSClient
from massgov.pfml.fineos.models import CreateOrUpdateLeaveAdmin


@pytest.fixture
def period_decisions():
    return {
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


def test_get_leave_details(period_decisions):
    leave_details = get_leave_details(period_decisions)

    assert leave_details.continuous_leave_periods[0].start_date == date(2021, 2, 1)
    assert leave_details.continuous_leave_periods[0].end_date == date(2021, 2, 24)
    assert leave_details.intermittent_leave_periods[0].start_date == date(2021, 1, 1)
    assert leave_details.intermittent_leave_periods[0].end_date == date(2021, 2, 1)
    assert leave_details.reduced_schedule_leave_periods[0].start_date == date(2021, 1, 4)
    assert leave_details.reduced_schedule_leave_periods[0].end_date == date(2021, 1, 29)
