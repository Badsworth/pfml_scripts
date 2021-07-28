import copy
import logging  # noqa: B1
from datetime import date
from unittest import mock

import pytest

import massgov.pfml.fineos.mock_client
from massgov.pfml.api.authorization.exceptions import NotAuthorizedForAccess
from massgov.pfml.api.exceptions import ObjectNotFound
from massgov.pfml.api.models.claims.common import PreviousLeave
from massgov.pfml.api.models.common import ConcurrentLeave
from massgov.pfml.api.services.administrator_fineos_actions import (
    EFORM_TYPES,
    download_document_as_leave_admin,
    get_claim_as_leave_admin,
    get_documents_as_leave_admin,
    get_leave_details,
    register_leave_admin_with_fineos,
)
from massgov.pfml.api.validation.exceptions import ContainsV1AndV2Eforms
from massgov.pfml.db.models.employees import UserLeaveAdministrator
from massgov.pfml.db.models.factories import EmployerFactory
from massgov.pfml.fineos import FINEOSClient, create_client
from massgov.pfml.fineos.common import DOWNLOADABLE_DOC_TYPES
from massgov.pfml.fineos.models import CreateOrUpdateLeaveAdmin, group_client_api
from massgov.pfml.fineos.models.group_client_api import GroupClientDocument


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
def mock_fineos_other_leaves_v2_eform():
    def mock_eform(*args, **kwargs):
        return group_client_api.EForm(
            eformType="Other Leaves - current version",
            eformId=12345,
            eformAttributes=[
                group_client_api.EFormAttribute(
                    name="V2Spacer1",
                    booleanValue=None,
                    dateValue=None,
                    decimalValue=None,
                    integerValue=None,
                    stringValue="",
                    enumValue=None,
                ),
                group_client_api.EFormAttribute(
                    name="V2Spacer3",
                    booleanValue=None,
                    dateValue=None,
                    decimalValue=None,
                    integerValue=None,
                    stringValue="",
                    enumValue=None,
                ),
                group_client_api.EFormAttribute(
                    name="V2Spacer2",
                    booleanValue=None,
                    dateValue=None,
                    decimalValue=None,
                    integerValue=None,
                    stringValue="",
                    enumValue=None,
                ),
                group_client_api.EFormAttribute(
                    name="V2Spacer5",
                    booleanValue=None,
                    dateValue=None,
                    decimalValue=None,
                    integerValue=None,
                    stringValue="",
                    enumValue=None,
                ),
                group_client_api.EFormAttribute(
                    name="V2Spacer4",
                    booleanValue=None,
                    dateValue=None,
                    decimalValue=None,
                    integerValue=None,
                    stringValue="",
                    enumValue=None,
                ),
                group_client_api.EFormAttribute(
                    name="V2Spacer7",
                    booleanValue=None,
                    dateValue=None,
                    decimalValue=None,
                    integerValue=None,
                    stringValue="",
                    enumValue=None,
                ),
                group_client_api.EFormAttribute(
                    name="V2Spacer6",
                    booleanValue=None,
                    dateValue=None,
                    decimalValue=None,
                    integerValue=None,
                    stringValue="",
                    enumValue=None,
                ),
                group_client_api.EFormAttribute(
                    name="V2Spacer9",
                    booleanValue=None,
                    dateValue=None,
                    decimalValue=None,
                    integerValue=None,
                    stringValue="",
                    enumValue=None,
                ),
                group_client_api.EFormAttribute(
                    name="V2AccruedPLEmployer1",
                    booleanValue=None,
                    dateValue=None,
                    decimalValue=None,
                    integerValue=None,
                    stringValue=None,
                    enumValue=group_client_api.ModelEnum(
                        domainName="PleaseSelectYesNo", instanceValue="Yes"
                    ),
                ),
                group_client_api.EFormAttribute(
                    name="V2Leave5",
                    booleanValue=None,
                    dateValue=None,
                    decimalValue=None,
                    integerValue=None,
                    stringValue=None,
                    enumValue=group_client_api.ModelEnum(
                        domainName="PleaseSelectYesNo", instanceValue="No"
                    ),
                ),
                group_client_api.EFormAttribute(
                    name="V2TotalHours5",
                    booleanValue=None,
                    dateValue=None,
                    decimalValue=None,
                    integerValue=60,
                    stringValue=None,
                    enumValue=None,
                ),
                group_client_api.EFormAttribute(
                    name="V2Spacer8",
                    booleanValue=None,
                    dateValue=None,
                    decimalValue=None,
                    integerValue=None,
                    stringValue="",
                    enumValue=None,
                ),
                group_client_api.EFormAttribute(
                    name="V2Leave6",
                    booleanValue=None,
                    dateValue=None,
                    decimalValue=None,
                    integerValue=None,
                    stringValue=None,
                    enumValue=group_client_api.ModelEnum(
                        domainName="PleaseSelectYesNo", instanceValue="No"
                    ),
                ),
                group_client_api.EFormAttribute(
                    name="V2TotalHours6",
                    booleanValue=None,
                    dateValue=None,
                    decimalValue=None,
                    integerValue=60,
                    stringValue=None,
                    enumValue=None,
                ),
                group_client_api.EFormAttribute(
                    name="V2Leave3",
                    booleanValue=None,
                    dateValue=None,
                    decimalValue=None,
                    integerValue=None,
                    stringValue=None,
                    enumValue=group_client_api.ModelEnum(
                        domainName="PleaseSelectYesNo", instanceValue="No"
                    ),
                ),
                group_client_api.EFormAttribute(
                    name="V2TotalHours3",
                    booleanValue=None,
                    dateValue=None,
                    decimalValue=None,
                    integerValue=40,
                    stringValue=None,
                    enumValue=None,
                ),
                group_client_api.EFormAttribute(
                    name="V2Leave4",
                    booleanValue=None,
                    dateValue=None,
                    decimalValue=None,
                    integerValue=None,
                    stringValue=None,
                    enumValue=group_client_api.ModelEnum(
                        domainName="PleaseSelectYesNo", instanceValue="No"
                    ),
                ),
                group_client_api.EFormAttribute(
                    name="V2TotalHours4",
                    booleanValue=None,
                    dateValue=None,
                    decimalValue=None,
                    integerValue=45,
                    stringValue=None,
                    enumValue=None,
                ),
                group_client_api.EFormAttribute(
                    name="V2TotalHours1",
                    booleanValue=None,
                    dateValue=None,
                    decimalValue=None,
                    integerValue=45,
                    stringValue=None,
                    enumValue=None,
                ),
                group_client_api.EFormAttribute(
                    name="V2TotalHours2",
                    booleanValue=None,
                    dateValue=None,
                    decimalValue=None,
                    integerValue=60,
                    stringValue=None,
                    enumValue=None,
                ),
                group_client_api.EFormAttribute(
                    name="V2AccruedEndDate1",
                    booleanValue=None,
                    dateValue=date(2021, 6, 18),
                    decimalValue=None,
                    integerValue=None,
                    stringValue=None,
                    enumValue=None,
                ),
                group_client_api.EFormAttribute(
                    name="V2MinutesWorked3",
                    booleanValue=None,
                    dateValue=None,
                    decimalValue=None,
                    integerValue=None,
                    stringValue=None,
                    enumValue=group_client_api.ModelEnum(
                        domainName="15MinuteIncrements", instanceValue="45"
                    ),
                ),
                group_client_api.EFormAttribute(
                    name="V2MinutesWorked4",
                    booleanValue=None,
                    dateValue=None,
                    decimalValue=None,
                    integerValue=None,
                    stringValue=None,
                    enumValue=group_client_api.ModelEnum(
                        domainName="15MinuteIncrements", instanceValue="15"
                    ),
                ),
                group_client_api.EFormAttribute(
                    name="V2MinutesWorked5",
                    booleanValue=None,
                    dateValue=None,
                    decimalValue=None,
                    integerValue=None,
                    stringValue=None,
                    enumValue=group_client_api.ModelEnum(
                        domainName="15MinuteIncrements", instanceValue="30"
                    ),
                ),
                group_client_api.EFormAttribute(
                    name="V2MinutesWorked6",
                    booleanValue=None,
                    dateValue=None,
                    decimalValue=None,
                    integerValue=None,
                    stringValue=None,
                    enumValue=group_client_api.ModelEnum(
                        domainName="15MinuteIncrements", instanceValue="15"
                    ),
                ),
                group_client_api.EFormAttribute(
                    name="V2Leave1",
                    booleanValue=None,
                    dateValue=None,
                    decimalValue=None,
                    integerValue=None,
                    stringValue=None,
                    enumValue=group_client_api.ModelEnum(
                        domainName="PleaseSelectYesNo", instanceValue="Yes"
                    ),
                ),
                group_client_api.EFormAttribute(
                    name="V2Leave2",
                    booleanValue=None,
                    dateValue=None,
                    decimalValue=None,
                    integerValue=None,
                    stringValue=None,
                    enumValue=group_client_api.ModelEnum(
                        domainName="PleaseSelectYesNo", instanceValue="Yes"
                    ),
                ),
                group_client_api.EFormAttribute(
                    name="V2MinutesWorked1",
                    booleanValue=None,
                    dateValue=None,
                    decimalValue=None,
                    integerValue=None,
                    stringValue=None,
                    enumValue=group_client_api.ModelEnum(
                        domainName="15MinuteIncrements", instanceValue="15"
                    ),
                ),
                group_client_api.EFormAttribute(
                    name="V2MinutesWorked2",
                    booleanValue=None,
                    dateValue=None,
                    decimalValue=None,
                    integerValue=None,
                    stringValue=None,
                    enumValue=group_client_api.ModelEnum(
                        domainName="15MinuteIncrements", instanceValue="30"
                    ),
                ),
                group_client_api.EFormAttribute(
                    name="V2QualifyingReason5",
                    booleanValue=None,
                    dateValue=None,
                    decimalValue=None,
                    integerValue=None,
                    stringValue=None,
                    enumValue=group_client_api.ModelEnum(
                        domainName="QualifyingReasons",
                        instanceValue="Caring for a family member who serves in the armed forces",
                    ),
                ),
                group_client_api.EFormAttribute(
                    name="V2QualifyingReason6",
                    booleanValue=None,
                    dateValue=None,
                    decimalValue=None,
                    integerValue=None,
                    stringValue=None,
                    enumValue=group_client_api.ModelEnum(
                        domainName="QualifyingReasons",
                        instanceValue="Managing family affairs while a family member is on active duty in the armed forces",
                    ),
                ),
                group_client_api.EFormAttribute(
                    name="V2AccruedReasons",
                    booleanValue=None,
                    dateValue=None,
                    decimalValue=None,
                    integerValue=None,
                    stringValue="This includes vacation time, sick time, personal time. Reminder: you can use accrued paid leave for the 7-day waiting period with no impact to your PFML benefit.\n\nThe following are qualifying reasons for taking paid or unpaid leave: \n\nYou had a serious health condition, including illness, injury, or pregnancy. If you were sick, you were out of work for at least 3 days and needed continuing care from your health care provider or needed inpatient care. \n\nYou bonded with your child after birth or placement. \n\nYou needed to manage family affairs while a family member is on active duty in the armed forces. \n\nYou needed to care for a family member who serves in the armed forces. \n\nYou needed to care for a family member with a serious health condition.",
                    enumValue=None,
                ),
                group_client_api.EFormAttribute(
                    name="V2AccruedPaidLeave1",
                    booleanValue=None,
                    dateValue=None,
                    decimalValue=None,
                    integerValue=None,
                    stringValue=None,
                    enumValue=group_client_api.ModelEnum(
                        domainName="PleaseSelectYesNo", instanceValue="Yes"
                    ),
                ),
                group_client_api.EFormAttribute(
                    name="V2LeaveFromEmployer3",
                    booleanValue=None,
                    dateValue=None,
                    decimalValue=None,
                    integerValue=None,
                    stringValue=None,
                    enumValue=group_client_api.ModelEnum(
                        domainName="PleaseSelectYesNo", instanceValue="Yes"
                    ),
                ),
                group_client_api.EFormAttribute(
                    name="V2LeaveFromEmployer2",
                    booleanValue=None,
                    dateValue=None,
                    decimalValue=None,
                    integerValue=None,
                    stringValue=None,
                    enumValue=group_client_api.ModelEnum(
                        domainName="PleaseSelectYesNo", instanceValue="Yes"
                    ),
                ),
                group_client_api.EFormAttribute(
                    name="V2LeaveFromEmployer1",
                    booleanValue=None,
                    dateValue=None,
                    decimalValue=None,
                    integerValue=None,
                    stringValue=None,
                    enumValue=group_client_api.ModelEnum(
                        domainName="PleaseSelectYesNo", instanceValue="Yes"
                    ),
                ),
                group_client_api.EFormAttribute(
                    name="V2LeaveFromEmployer6",
                    booleanValue=None,
                    dateValue=None,
                    decimalValue=None,
                    integerValue=None,
                    stringValue=None,
                    enumValue=group_client_api.ModelEnum(
                        domainName="PleaseSelectYesNo", instanceValue="No"
                    ),
                ),
                group_client_api.EFormAttribute(
                    name="V2LeaveFromEmployer5",
                    booleanValue=None,
                    dateValue=None,
                    decimalValue=None,
                    integerValue=None,
                    stringValue=None,
                    enumValue=group_client_api.ModelEnum(
                        domainName="PleaseSelectYesNo", instanceValue="Yes"
                    ),
                ),
                group_client_api.EFormAttribute(
                    name="V2LeaveFromEmployer4",
                    booleanValue=None,
                    dateValue=None,
                    decimalValue=None,
                    integerValue=None,
                    stringValue=None,
                    enumValue=group_client_api.ModelEnum(
                        domainName="PleaseSelectYesNo", instanceValue="Yes"
                    ),
                ),
                group_client_api.EFormAttribute(
                    name="V2Header1",
                    booleanValue=None,
                    dateValue=None,
                    decimalValue=None,
                    integerValue=None,
                    stringValue="Previous leaves",
                    enumValue=None,
                ),
                group_client_api.EFormAttribute(
                    name="V2Header2",
                    booleanValue=None,
                    dateValue=None,
                    decimalValue=None,
                    integerValue=None,
                    stringValue="Employer-sponsored Accrued Paid Leave",
                    enumValue=None,
                ),
                group_client_api.EFormAttribute(
                    name="V2OtherLeavesPastLeaveEndDate1",
                    booleanValue=None,
                    dateValue=date(2021, 1, 4),
                    decimalValue=None,
                    integerValue=None,
                    stringValue=None,
                    enumValue=None,
                ),
                group_client_api.EFormAttribute(
                    name="V2OtherLeavesPastLeaveEndDate3",
                    booleanValue=None,
                    dateValue=date(2021, 1, 15),
                    decimalValue=None,
                    integerValue=None,
                    stringValue=None,
                    enumValue=None,
                ),
                group_client_api.EFormAttribute(
                    name="V2OtherLeavesPastLeaveEndDate2",
                    booleanValue=None,
                    dateValue=date(2021, 1, 12),
                    decimalValue=None,
                    integerValue=None,
                    stringValue=None,
                    enumValue=None,
                ),
                group_client_api.EFormAttribute(
                    name="V2OtherLeavesPastLeaveEndDate5",
                    booleanValue=None,
                    dateValue=date(2021, 1, 22),
                    decimalValue=None,
                    integerValue=None,
                    stringValue=None,
                    enumValue=None,
                ),
                group_client_api.EFormAttribute(
                    name="V2OtherLeavesPastLeaveEndDate4",
                    booleanValue=None,
                    dateValue=date(2021, 1, 19),
                    decimalValue=None,
                    integerValue=None,
                    stringValue=None,
                    enumValue=None,
                ),
                group_client_api.EFormAttribute(
                    name="V2OtherLeavesPastLeaveEndDate6",
                    booleanValue=None,
                    dateValue=date(2021, 1, 26),
                    decimalValue=None,
                    integerValue=None,
                    stringValue=None,
                    enumValue=None,
                ),
                group_client_api.EFormAttribute(
                    name="V2TotalMinutes3",
                    booleanValue=None,
                    dateValue=None,
                    decimalValue=None,
                    integerValue=None,
                    stringValue=None,
                    enumValue=group_client_api.ModelEnum(
                        domainName="15MinuteIncrements", instanceValue="15"
                    ),
                ),
                group_client_api.EFormAttribute(
                    name="V2TotalMinutes4",
                    booleanValue=None,
                    dateValue=None,
                    decimalValue=None,
                    integerValue=None,
                    stringValue=None,
                    enumValue=group_client_api.ModelEnum(
                        domainName="15MinuteIncrements", instanceValue="15"
                    ),
                ),
                group_client_api.EFormAttribute(
                    name="V2TotalMinutes5",
                    booleanValue=None,
                    dateValue=None,
                    decimalValue=None,
                    integerValue=None,
                    stringValue=None,
                    enumValue=group_client_api.ModelEnum(
                        domainName="15MinuteIncrements", instanceValue="45"
                    ),
                ),
                group_client_api.EFormAttribute(
                    name="V2TotalMinutes6",
                    booleanValue=None,
                    dateValue=None,
                    decimalValue=None,
                    integerValue=None,
                    stringValue=None,
                    enumValue=group_client_api.ModelEnum(
                        domainName="15MinuteIncrements", instanceValue="30"
                    ),
                ),
                group_client_api.EFormAttribute(
                    name="V2TotalMinutes1",
                    booleanValue=None,
                    dateValue=None,
                    decimalValue=None,
                    integerValue=None,
                    stringValue=None,
                    enumValue=group_client_api.ModelEnum(
                        domainName="15MinuteIncrements", instanceValue="45"
                    ),
                ),
                group_client_api.EFormAttribute(
                    name="V2TotalMinutes2",
                    booleanValue=None,
                    dateValue=None,
                    decimalValue=None,
                    integerValue=None,
                    stringValue=None,
                    enumValue=group_client_api.ModelEnum(
                        domainName="15MinuteIncrements", instanceValue="30"
                    ),
                ),
                group_client_api.EFormAttribute(
                    name="V2QualifyingReason1",
                    booleanValue=None,
                    dateValue=None,
                    decimalValue=None,
                    integerValue=None,
                    stringValue=None,
                    enumValue=group_client_api.ModelEnum(
                        domainName="QualifyingReasons", instanceValue="Pregnancy"
                    ),
                ),
                group_client_api.EFormAttribute(
                    name="V2QualifyingReason2",
                    booleanValue=None,
                    dateValue=None,
                    decimalValue=None,
                    integerValue=None,
                    stringValue=None,
                    enumValue=group_client_api.ModelEnum(
                        domainName="QualifyingReasons", instanceValue=" An illness or injury"
                    ),
                ),
                group_client_api.EFormAttribute(
                    name="V2QualifyingReason3",
                    booleanValue=None,
                    dateValue=None,
                    decimalValue=None,
                    integerValue=None,
                    stringValue=None,
                    enumValue=group_client_api.ModelEnum(
                        domainName="QualifyingReasons",
                        instanceValue="Caring for a family member with a serious health condition",
                    ),
                ),
                group_client_api.EFormAttribute(
                    name="V2QualifyingReason4",
                    booleanValue=None,
                    dateValue=None,
                    decimalValue=None,
                    integerValue=None,
                    stringValue=None,
                    enumValue=group_client_api.ModelEnum(
                        domainName="QualifyingReasons",
                        instanceValue="Bonding with my child after birth or placement",
                    ),
                ),
                group_client_api.EFormAttribute(
                    name="V2Applies1",
                    booleanValue=None,
                    dateValue=None,
                    decimalValue=None,
                    integerValue=None,
                    stringValue=None,
                    enumValue=group_client_api.ModelEnum(
                        domainName="PleaseSelectYesNo", instanceValue="Yes"
                    ),
                ),
                group_client_api.EFormAttribute(
                    name="V2Applies3",
                    booleanValue=None,
                    dateValue=None,
                    decimalValue=None,
                    integerValue=None,
                    stringValue=None,
                    enumValue=group_client_api.ModelEnum(
                        domainName="PleaseSelectYesNo", instanceValue="Yes"
                    ),
                ),
                group_client_api.EFormAttribute(
                    name="V2Applies2",
                    booleanValue=None,
                    dateValue=None,
                    decimalValue=None,
                    integerValue=None,
                    stringValue=None,
                    enumValue=group_client_api.ModelEnum(
                        domainName="PleaseSelectYesNo", instanceValue="Yes"
                    ),
                ),
                group_client_api.EFormAttribute(
                    name="V2Applies5",
                    booleanValue=None,
                    dateValue=None,
                    decimalValue=None,
                    integerValue=None,
                    stringValue=None,
                    enumValue=group_client_api.ModelEnum(
                        domainName="PleaseSelectYesNo", instanceValue="Yes"
                    ),
                ),
                group_client_api.EFormAttribute(
                    name="V2Applies4",
                    booleanValue=None,
                    dateValue=None,
                    decimalValue=None,
                    integerValue=None,
                    stringValue=None,
                    enumValue=group_client_api.ModelEnum(
                        domainName="PleaseSelectYesNo", instanceValue="Yes"
                    ),
                ),
                group_client_api.EFormAttribute(
                    name="V2OtherLeavesPastLeaveStartDate2",
                    booleanValue=None,
                    dateValue=date(2021, 1, 11),
                    decimalValue=None,
                    integerValue=None,
                    stringValue=None,
                    enumValue=None,
                ),
                group_client_api.EFormAttribute(
                    name="V2Applies7",
                    booleanValue=None,
                    dateValue=None,
                    decimalValue=None,
                    integerValue=None,
                    stringValue=None,
                    enumValue=group_client_api.ModelEnum(
                        domainName="PleaseSelectYesNo", instanceValue="No"
                    ),
                ),
                group_client_api.EFormAttribute(
                    name="V2OtherLeavesPastLeaveStartDate1",
                    booleanValue=None,
                    dateValue=date(2021, 1, 1),
                    decimalValue=None,
                    integerValue=None,
                    stringValue=None,
                    enumValue=None,
                ),
                group_client_api.EFormAttribute(
                    name="V2Applies6",
                    booleanValue=None,
                    dateValue=None,
                    decimalValue=None,
                    integerValue=None,
                    stringValue=None,
                    enumValue=group_client_api.ModelEnum(
                        domainName="PleaseSelectYesNo", instanceValue="Yes"
                    ),
                ),
                group_client_api.EFormAttribute(
                    name="V2OtherLeavesPastLeaveStartDate4",
                    booleanValue=None,
                    dateValue=date(2021, 1, 18),
                    decimalValue=None,
                    integerValue=None,
                    stringValue=None,
                    enumValue=None,
                ),
                group_client_api.EFormAttribute(
                    name="V2OtherLeavesPastLeaveStartDate3",
                    booleanValue=None,
                    dateValue=date(2021, 1, 14),
                    decimalValue=None,
                    integerValue=None,
                    stringValue=None,
                    enumValue=None,
                ),
                group_client_api.EFormAttribute(
                    name="V2OtherLeavesPastLeaveStartDate6",
                    booleanValue=None,
                    dateValue=date(2021, 1, 25),
                    decimalValue=None,
                    integerValue=None,
                    stringValue=None,
                    enumValue=None,
                ),
                group_client_api.EFormAttribute(
                    name="V2OtherLeavesPastLeaveStartDate5",
                    booleanValue=None,
                    dateValue=date(2021, 1, 20),
                    decimalValue=None,
                    integerValue=None,
                    stringValue=None,
                    enumValue=None,
                ),
                group_client_api.EFormAttribute(
                    name="V2HoursWorked2",
                    booleanValue=None,
                    dateValue=None,
                    decimalValue=None,
                    integerValue=40,
                    stringValue=None,
                    enumValue=None,
                ),
                group_client_api.EFormAttribute(
                    name="V2HoursWorked1",
                    booleanValue=None,
                    dateValue=None,
                    decimalValue=None,
                    integerValue=40,
                    stringValue=None,
                    enumValue=None,
                ),
                group_client_api.EFormAttribute(
                    name="V2Spacer10",
                    booleanValue=None,
                    dateValue=None,
                    decimalValue=None,
                    integerValue=None,
                    stringValue="",
                    enumValue=None,
                ),
                group_client_api.EFormAttribute(
                    name="V2Reasons",
                    booleanValue=None,
                    dateValue=None,
                    decimalValue=None,
                    integerValue=None,
                    stringValue="You had a serious health condition, including illness, injury, or pregnancy. If you were sick, you were out of work for at least 3 days and needed continuing care from your health care provider or needed inpatient care. \n\nYou bonded with your child after birth or placement. \n\nYou needed to manage family affairs while a family member is on active duty in the armed forces. \n\nYou needed to care for a family member who serves in the armed forces. \n\nYou needed to care for a family member with a serious health condition.",
                    enumValue=None,
                ),
                group_client_api.EFormAttribute(
                    name="V2AccruedStartDate1",
                    booleanValue=None,
                    dateValue=date(2021, 6, 4),
                    decimalValue=None,
                    integerValue=None,
                    stringValue=None,
                    enumValue=None,
                ),
                group_client_api.EFormAttribute(
                    name="V2HoursWorked6",
                    booleanValue=None,
                    dateValue=None,
                    decimalValue=None,
                    integerValue=40,
                    stringValue=None,
                    enumValue=None,
                ),
                group_client_api.EFormAttribute(
                    name="V2HoursWorked5",
                    booleanValue=None,
                    dateValue=None,
                    decimalValue=None,
                    integerValue=40,
                    stringValue=None,
                    enumValue=None,
                ),
                group_client_api.EFormAttribute(
                    name="V2HoursWorked4",
                    booleanValue=None,
                    dateValue=None,
                    decimalValue=None,
                    integerValue=40,
                    stringValue=None,
                    enumValue=None,
                ),
                group_client_api.EFormAttribute(
                    name="V2HoursWorked3",
                    booleanValue=None,
                    dateValue=None,
                    decimalValue=None,
                    integerValue=40,
                    stringValue=None,
                    enumValue=None,
                ),
            ],
        )

    def mock_eform_summary(*args, **kwargs):
        return [
            group_client_api.EFormSummary(eformId=12345, eformType=EFORM_TYPES["OTHER_LEAVES"]),
        ]

    mock_client = create_client()
    mock_client.get_eform = mock_eform
    mock_client.get_eform_summary = mock_eform_summary

    return mock_client


@pytest.fixture
def mock_fineos_other_leaves_v2_accrued_leave_different_employer_eform():
    def mock_eform(*args, **kwargs):
        return group_client_api.EForm(
            eformType="Other Leaves - current version",
            eformId=1234,
            eformAttributes=[
                group_client_api.EFormAttribute(
                    name="V2Spacer1",
                    booleanValue=None,
                    dateValue=None,
                    decimalValue=None,
                    integerValue=None,
                    stringValue="",
                    enumValue=None,
                ),
                group_client_api.EFormAttribute(
                    name="V2Spacer5",
                    booleanValue=None,
                    dateValue=None,
                    decimalValue=None,
                    integerValue=None,
                    stringValue="",
                    enumValue=None,
                ),
                group_client_api.EFormAttribute(
                    name="V2Spacer4",
                    booleanValue=None,
                    dateValue=None,
                    decimalValue=None,
                    integerValue=None,
                    stringValue="",
                    enumValue=None,
                ),
                group_client_api.EFormAttribute(
                    name="V2Spacer7",
                    booleanValue=None,
                    dateValue=None,
                    decimalValue=None,
                    integerValue=None,
                    stringValue="",
                    enumValue=None,
                ),
                group_client_api.EFormAttribute(
                    name="V2Spacer6",
                    booleanValue=None,
                    dateValue=None,
                    decimalValue=None,
                    integerValue=None,
                    stringValue="",
                    enumValue=None,
                ),
                group_client_api.EFormAttribute(
                    name="V2Spacer9",
                    booleanValue=None,
                    dateValue=None,
                    decimalValue=None,
                    integerValue=None,
                    stringValue="",
                    enumValue=None,
                ),
                group_client_api.EFormAttribute(
                    name="V2AccruedPLEmployer1",
                    booleanValue=None,
                    dateValue=None,
                    decimalValue=None,
                    integerValue=None,
                    stringValue=None,
                    enumValue=group_client_api.ModelEnum(
                        domainName="PleaseSelectYesNo", instanceValue="No"
                    ),
                ),
                group_client_api.EFormAttribute(
                    name="V2Spacer8",
                    booleanValue=None,
                    dateValue=None,
                    decimalValue=None,
                    integerValue=None,
                    stringValue="",
                    enumValue=None,
                ),
                group_client_api.EFormAttribute(
                    name="V2TotalHours1",
                    booleanValue=None,
                    dateValue=None,
                    decimalValue=None,
                    integerValue=60,
                    stringValue=None,
                    enumValue=None,
                ),
                group_client_api.EFormAttribute(
                    name="V2AccruedEndDate1",
                    booleanValue=None,
                    dateValue=date(2021, 4, 12),
                    decimalValue=None,
                    integerValue=None,
                    stringValue=None,
                    enumValue=None,
                ),
                group_client_api.EFormAttribute(
                    name="V2Leave1",
                    booleanValue=None,
                    dateValue=None,
                    decimalValue=None,
                    integerValue=None,
                    stringValue=None,
                    enumValue=group_client_api.ModelEnum(
                        domainName="PleaseSelectYesNo", instanceValue="Yes"
                    ),
                ),
                group_client_api.EFormAttribute(
                    name="V2MinutesWorked1",
                    booleanValue=None,
                    dateValue=None,
                    decimalValue=None,
                    integerValue=None,
                    stringValue=None,
                    enumValue=group_client_api.ModelEnum(
                        domainName="15MinuteIncrements", instanceValue="00"
                    ),
                ),
                group_client_api.EFormAttribute(
                    name="V2AccruedReasons",
                    booleanValue=None,
                    dateValue=None,
                    decimalValue=None,
                    integerValue=None,
                    stringValue="This includes vacation time, sick time, personal time. Reminder: you can use accrued paid leave for the 7-day waiting period with no impact to your PFML benefit.\n\nThe following are qualifying reasons for taking paid or unpaid leave: \n\nYou had a serious health condition, including illness, injury, or pregnancy. If you were sick, you were out of work for at least 3 days and needed continuing care from your health care provider or needed inpatient care. \n\nYou bonded with your child after birth or placement. \n\nYou needed to manage family affairs while a family member is on active duty in the armed forces. \n\nYou needed to care for a family member who serves in the armed forces. \n\nYou needed to care for a family member with a serious health condition.",
                    enumValue=None,
                ),
                group_client_api.EFormAttribute(
                    name="V2AccruedPaidLeave1",
                    booleanValue=None,
                    dateValue=None,
                    decimalValue=None,
                    integerValue=None,
                    stringValue=None,
                    enumValue=group_client_api.ModelEnum(
                        domainName="PleaseSelectYesNo", instanceValue="Yes"
                    ),
                ),
                group_client_api.EFormAttribute(
                    name="V2LeaveFromEmployer1",
                    booleanValue=None,
                    dateValue=None,
                    decimalValue=None,
                    integerValue=None,
                    stringValue=None,
                    enumValue=group_client_api.ModelEnum(
                        domainName="PleaseSelectYesNo", instanceValue="Yes"
                    ),
                ),
                group_client_api.EFormAttribute(
                    name="V2Header1",
                    booleanValue=None,
                    dateValue=None,
                    decimalValue=None,
                    integerValue=None,
                    stringValue="Previous leaves",
                    enumValue=None,
                ),
                group_client_api.EFormAttribute(
                    name="V2Header2",
                    booleanValue=None,
                    dateValue=None,
                    decimalValue=None,
                    integerValue=None,
                    stringValue="Employer-sponsored Accrued Paid Leave",
                    enumValue=None,
                ),
                group_client_api.EFormAttribute(
                    name="V2OtherLeavesPastLeaveEndDate1",
                    booleanValue=None,
                    dateValue=date(2021, 3, 8),
                    decimalValue=None,
                    integerValue=None,
                    stringValue=None,
                    enumValue=None,
                ),
                group_client_api.EFormAttribute(
                    name="V2TotalMinutes1",
                    booleanValue=None,
                    dateValue=None,
                    decimalValue=None,
                    integerValue=None,
                    stringValue=None,
                    enumValue=group_client_api.ModelEnum(
                        domainName="15MinuteIncrements", instanceValue="00"
                    ),
                ),
                group_client_api.EFormAttribute(
                    name="V2QualifyingReason1",
                    booleanValue=None,
                    dateValue=None,
                    decimalValue=None,
                    integerValue=None,
                    stringValue=None,
                    enumValue=group_client_api.ModelEnum(
                        domainName="QualifyingReasons", instanceValue="Pregnancy"
                    ),
                ),
                group_client_api.EFormAttribute(
                    name="V2Applies1",
                    booleanValue=None,
                    dateValue=None,
                    decimalValue=None,
                    integerValue=None,
                    stringValue=None,
                    enumValue=group_client_api.ModelEnum(
                        domainName="PleaseSelectYesNo", instanceValue="Yes"
                    ),
                ),
                group_client_api.EFormAttribute(
                    name="V2Applies2",
                    booleanValue=None,
                    dateValue=None,
                    decimalValue=None,
                    integerValue=None,
                    stringValue=None,
                    enumValue=group_client_api.ModelEnum(
                        domainName="PleaseSelectYesNo", instanceValue="No"
                    ),
                ),
                group_client_api.EFormAttribute(
                    name="V2OtherLeavesPastLeaveStartDate1",
                    booleanValue=None,
                    dateValue=date(2021, 3, 1),
                    decimalValue=None,
                    integerValue=None,
                    stringValue=None,
                    enumValue=None,
                ),
                group_client_api.EFormAttribute(
                    name="V2HoursWorked1",
                    booleanValue=None,
                    dateValue=None,
                    decimalValue=None,
                    integerValue=40,
                    stringValue=None,
                    enumValue=None,
                ),
                group_client_api.EFormAttribute(
                    name="V2Spacer10",
                    booleanValue=None,
                    dateValue=None,
                    decimalValue=None,
                    integerValue=None,
                    stringValue="",
                    enumValue=None,
                ),
                group_client_api.EFormAttribute(
                    name="V2Reasons",
                    booleanValue=None,
                    dateValue=None,
                    decimalValue=None,
                    integerValue=None,
                    stringValue="You had a serious health condition, including illness, injury, or pregnancy. If you were sick, you were out of work for at least 3 days and needed continuing care from your health care provider or needed inpatient care. \n\nYou bonded with your child after birth or placement. \n\nYou needed to manage family affairs while a family member is on active duty in the armed forces. \n\nYou needed to care for a family member who serves in the armed forces. \n\nYou needed to care for a family member with a serious health condition.",
                    enumValue=None,
                ),
                group_client_api.EFormAttribute(
                    name="V2AccruedStartDate1",
                    booleanValue=None,
                    dateValue=date(2021, 4, 5),
                    decimalValue=None,
                    integerValue=None,
                    stringValue=None,
                    enumValue=None,
                ),
            ],
        )

    def mock_eform_summary(*args, **kwargs):
        return [
            group_client_api.EFormSummary(eformId=12345, eformType=EFORM_TYPES["OTHER_LEAVES"]),
        ]

    mock_client = create_client()
    mock_client.get_eform = mock_eform
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


@pytest.fixture
def mock_fineos_other_income_v1_eform():
    def mock_eform_summary(*args, **kwargs):
        return [
            group_client_api.EFormSummary(eformId=12345, eformType=EFORM_TYPES["OTHER_INCOME"]),
        ]

    def mock_get_eform(*args, **kwargs):
        return group_client_api.EForm(
            eformType="Other Income",
            eformId=27701,
            eformAttributes=[
                group_client_api.EFormAttribute(
                    name="StartDate",
                    booleanValue=None,
                    dateValue=date(2021, 5, 3),
                    decimalValue=None,
                    integerValue=None,
                    stringValue=None,
                    enumValue=None,
                ),
                group_client_api.EFormAttribute(
                    name="Frequency2",
                    booleanValue=None,
                    dateValue=None,
                    decimalValue=None,
                    integerValue=None,
                    stringValue="Per Week",
                    enumValue=None,
                ),
                group_client_api.EFormAttribute(
                    name="ProgramType",
                    booleanValue=None,
                    dateValue=None,
                    decimalValue=None,
                    integerValue=None,
                    stringValue=None,
                    enumValue=group_client_api.ModelEnum(
                        domainName="Program Type", instanceValue="Employer"
                    ),
                ),
                group_client_api.EFormAttribute(
                    name="Spacer4",
                    booleanValue=None,
                    dateValue=None,
                    decimalValue=None,
                    integerValue=None,
                    stringValue="",
                    enumValue=None,
                ),
                group_client_api.EFormAttribute(
                    name="ProgramType2",
                    booleanValue=None,
                    dateValue=None,
                    decimalValue=None,
                    integerValue=None,
                    stringValue=None,
                    enumValue=group_client_api.ModelEnum(
                        domainName="Program Type", instanceValue="Non-Employer"
                    ),
                ),
                group_client_api.EFormAttribute(
                    name="ReceiveWageReplacement",
                    booleanValue=None,
                    dateValue=None,
                    decimalValue=None,
                    integerValue=None,
                    stringValue=None,
                    enumValue=group_client_api.ModelEnum(
                        domainName="YesNoI'veApplied", instanceValue="Yes"
                    ),
                ),
                group_client_api.EFormAttribute(
                    name="StartDate2",
                    booleanValue=None,
                    dateValue=date(2021, 5, 5),
                    decimalValue=None,
                    integerValue=None,
                    stringValue=None,
                    enumValue=None,
                ),
                group_client_api.EFormAttribute(
                    name="Spacer1",
                    booleanValue=None,
                    dateValue=None,
                    decimalValue=None,
                    integerValue=None,
                    stringValue="",
                    enumValue=None,
                ),
                group_client_api.EFormAttribute(
                    name="Spacer3",
                    booleanValue=None,
                    dateValue=None,
                    decimalValue=None,
                    integerValue=None,
                    stringValue="",
                    enumValue=None,
                ),
                group_client_api.EFormAttribute(
                    name="Spacer2",
                    booleanValue=None,
                    dateValue=None,
                    decimalValue=None,
                    integerValue=None,
                    stringValue="",
                    enumValue=None,
                ),
                group_client_api.EFormAttribute(
                    name="Spacer",
                    booleanValue=None,
                    dateValue=None,
                    decimalValue=None,
                    integerValue=None,
                    stringValue="",
                    enumValue=None,
                ),
                group_client_api.EFormAttribute(
                    name="WRT1",
                    booleanValue=None,
                    dateValue=None,
                    decimalValue=None,
                    integerValue=None,
                    stringValue=None,
                    enumValue=group_client_api.ModelEnum(
                        domainName="WageReplacementType",
                        instanceValue="Permanent disability insurance",
                    ),
                ),
                group_client_api.EFormAttribute(
                    name="WRT2",
                    booleanValue=None,
                    dateValue=None,
                    decimalValue=None,
                    integerValue=None,
                    stringValue=None,
                    enumValue=group_client_api.ModelEnum(
                        domainName="WageReplacementType2", instanceValue="Please Select"
                    ),
                ),
                group_client_api.EFormAttribute(
                    name="WRT3",
                    booleanValue=None,
                    dateValue=None,
                    decimalValue=None,
                    integerValue=None,
                    stringValue=None,
                    enumValue=group_client_api.ModelEnum(
                        domainName="WageReplacementType", instanceValue="Please Select"
                    ),
                ),
                group_client_api.EFormAttribute(
                    name="WRT4",
                    booleanValue=None,
                    dateValue=None,
                    decimalValue=None,
                    integerValue=None,
                    stringValue=None,
                    enumValue=group_client_api.ModelEnum(
                        domainName="WageReplacementType2", instanceValue="SSDI"
                    ),
                ),
                group_client_api.EFormAttribute(
                    name="EndDate2",
                    booleanValue=None,
                    dateValue=date(2021, 5, 29),
                    decimalValue=None,
                    integerValue=None,
                    stringValue=None,
                    enumValue=None,
                ),
                group_client_api.EFormAttribute(
                    name="Amount",
                    booleanValue=None,
                    dateValue=None,
                    decimalValue=500.0,
                    integerValue=None,
                    stringValue=None,
                    enumValue=None,
                ),
                group_client_api.EFormAttribute(
                    name="EndDate",
                    booleanValue=None,
                    dateValue=date(2021, 5, 29),
                    decimalValue=None,
                    integerValue=None,
                    stringValue=None,
                    enumValue=None,
                ),
                group_client_api.EFormAttribute(
                    name="Amount2",
                    booleanValue=None,
                    dateValue=None,
                    decimalValue=500.0,
                    integerValue=None,
                    stringValue=None,
                    enumValue=None,
                ),
                group_client_api.EFormAttribute(
                    name="ReceiveWageReplacement3",
                    booleanValue=None,
                    dateValue=None,
                    decimalValue=None,
                    integerValue=None,
                    stringValue=None,
                    enumValue=group_client_api.ModelEnum(
                        domainName="YesNoI'veApplied", instanceValue="Please Select"
                    ),
                ),
                group_client_api.EFormAttribute(
                    name="Frequency",
                    booleanValue=None,
                    dateValue=None,
                    decimalValue=None,
                    integerValue=None,
                    stringValue="Per Week",
                    enumValue=None,
                ),
                group_client_api.EFormAttribute(
                    name="ReceiveWageReplacement2",
                    booleanValue=None,
                    dateValue=None,
                    decimalValue=None,
                    integerValue=None,
                    stringValue=None,
                    enumValue=group_client_api.ModelEnum(
                        domainName="YesNoI'veApplied", instanceValue="Yes"
                    ),
                ),
            ],
        )

    mock_client = create_client()
    mock_client.get_eform_summary = mock_eform_summary
    mock_client.get_eform = mock_get_eform

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
def test_get_claim_eform_type_contains_neither_version_no_feature_toggle(
    mock_fineos_period_decisions, initialize_factories_session
):
    fineos_user_id = "Friendly_HR"
    absence_id = "NTN-001-ABS-001"
    employer = EmployerFactory.create()
    leave_details = get_claim_as_leave_admin(
        fineos_user_id,
        absence_id,
        employer,
        fineos_client=mock_fineos_period_decisions,
        default_to_v2=False,
    )
    assert leave_details.uses_second_eform_version is False


@pytest.mark.integration
def test_get_claim_eform_type_contains_neither_version_with_feature_toggle(
    mock_fineos_period_decisions, initialize_factories_session
):
    fineos_user_id = "Friendly_HR"
    absence_id = "NTN-001-ABS-001"
    employer = EmployerFactory.create()
    leave_details = get_claim_as_leave_admin(
        fineos_user_id,
        absence_id,
        employer,
        fineos_client=mock_fineos_period_decisions,
        default_to_v2=True,
    )
    assert leave_details.uses_second_eform_version is True


@pytest.mark.integration
def test_get_claim_other_income_eform_type_contains_both_versions(
    mock_fineos_other_income_eform_both_versions, initialize_factories_session
):
    fineos_user_id = "Friendly_HR"
    absence_id = "NTN-001-ABS-001"
    employer = EmployerFactory.create()
    with pytest.raises(ContainsV1AndV2Eforms):
        get_claim_as_leave_admin(
            fineos_user_id,
            absence_id,
            employer,
            fineos_client=mock_fineos_other_income_eform_both_versions,
        )


@pytest.mark.integration
def test_get_claim_other_leaves_v2_eform(
    mock_fineos_other_leaves_v2_eform, initialize_factories_session
):
    fineos_user_id = "Friendly_HR"
    absence_id = "NTN-001-ABS-001"
    employer = EmployerFactory.create()
    leave_details = get_claim_as_leave_admin(
        fineos_user_id, absence_id, employer, fineos_client=mock_fineos_other_leaves_v2_eform,
    )

    assert leave_details.uses_second_eform_version is True
    assert leave_details.previous_leaves == [
        PreviousLeave(
            is_for_current_employer=True,
            leave_start_date=date(2021, 1, 1),
            leave_end_date=date(2021, 1, 4),
            leave_reason="Pregnancy",
            previous_leave_id=None,
            worked_per_week_minutes=None,
            leave_minutes=None,
            type="same_reason",
        ),
        PreviousLeave(
            is_for_current_employer=True,
            leave_start_date=date(2021, 1, 11),
            leave_end_date=date(2021, 1, 12),
            leave_reason="An illness or injury",
            previous_leave_id=None,
            worked_per_week_minutes=None,
            leave_minutes=None,
            type="same_reason",
        ),
        PreviousLeave(
            is_for_current_employer=True,
            leave_start_date=date(2021, 1, 14),
            leave_end_date=date(2021, 1, 15),
            leave_reason="Caring for a family member with a serious health condition",
            previous_leave_id=None,
            worked_per_week_minutes=None,
            leave_minutes=None,
            type="other_reason",
        ),
        PreviousLeave(
            is_for_current_employer=True,
            leave_start_date=date(2021, 1, 18),
            leave_end_date=date(2021, 1, 19),
            leave_reason="Bonding with my child after birth or placement",
            previous_leave_id=None,
            worked_per_week_minutes=None,
            leave_minutes=None,
            type="other_reason",
        ),
        PreviousLeave(
            is_for_current_employer=True,
            leave_start_date=date(2021, 1, 20),
            leave_end_date=date(2021, 1, 22),
            leave_reason="Caring for a family member who serves in the armed forces",
            previous_leave_id=None,
            worked_per_week_minutes=None,
            leave_minutes=None,
            type="other_reason",
        ),
    ]
    assert (
        PreviousLeave(
            is_for_current_employer=False,
            leave_start_date=date(2021, 1, 25),
            leave_end_date=date(2021, 1, 26),
            leave_reason="Managing family affairs while a family member is on active duty in the armed forces",
            previous_leave_id=None,
            worked_per_week_minutes=None,
            leave_minutes=None,
            type="other_reason",
        )
        not in leave_details.previous_leaves
    )
    assert leave_details.concurrent_leave == ConcurrentLeave(
        is_for_current_employer=True,
        leave_start_date=date(2021, 6, 4),
        leave_end_date=date(2021, 6, 18),
    )


@pytest.mark.integration
def test_get_claim_other_leaves_v2_accrued_leave_different_employer_eform(
    mock_fineos_other_leaves_v2_accrued_leave_different_employer_eform, initialize_factories_session
):
    fineos_user_id = "Friendly_HR"
    absence_id = "NTN-001-ABS-001"
    employer = EmployerFactory.create()
    leave_details = get_claim_as_leave_admin(
        fineos_user_id,
        absence_id,
        employer,
        fineos_client=mock_fineos_other_leaves_v2_accrued_leave_different_employer_eform,
    )

    assert leave_details.previous_leaves == [
        PreviousLeave(
            is_for_current_employer=True,
            leave_start_date=date(2021, 3, 1),
            leave_end_date=date(2021, 3, 8),
            leave_reason="Pregnancy",
            previous_leave_id=None,
            worked_per_week_minutes=None,
            leave_minutes=None,
            type="same_reason",
        )
    ]
    assert leave_details.concurrent_leave is None


@pytest.mark.integration
def test_get_claim_other_income(mock_fineos_other_income_v1_eform, initialize_factories_session):
    fineos_user_id = "Friendly_HR"
    absence_id = "NTN-001-ABS-001"
    employer = EmployerFactory.create()
    leave_details = get_claim_as_leave_admin(
        fineos_user_id, absence_id, employer, fineos_client=mock_fineos_other_income_v1_eform,
    )
    assert leave_details.date_of_birth == "****-12-25"
    assert len(leave_details.employer_benefits) == 1
    assert leave_details.employer_benefits[0].benefit_amount_dollars == 500
    assert leave_details.employer_benefits[0].benefit_amount_frequency == "Per Week"
    assert leave_details.employer_benefits[0].benefit_start_date == date(2021, 5, 3)
    assert leave_details.employer_benefits[0].benefit_end_date == date(2021, 5, 29)
    assert leave_details.employer_benefits[0].benefit_type == "Permanent disability insurance"
    assert leave_details.employer_benefits[0].program_type == "Employer"
    assert leave_details.employer_dba == employer.employer_dba
    assert leave_details.employer_id == employer.employer_id
    assert leave_details.fineos_absence_id == absence_id
    assert leave_details.first_name == "Bud"
    assert leave_details.middle_name == ""
    assert leave_details.last_name == "Baxter"
    assert leave_details.hours_worked_per_week == 37.5
    assert leave_details.leave_details.reason == "Serious Health Condition - Employee"
    assert leave_details.previous_leaves == []
    assert leave_details.residential_address.line_1 == "55 Trinity Ave."
    assert leave_details.residential_address.line_2 == "Suite 3450"
    assert leave_details.residential_address.city == "Atlanta"
    assert leave_details.residential_address.state == "GA"
    assert leave_details.residential_address.zip == "30303"
    assert leave_details.tax_identifier == "***-**-1234"
    assert leave_details.follow_up_date == date(2021, 2, 1)
    assert leave_details.is_reviewable is False
    assert leave_details.status == "Known"
    assert leave_details.uses_second_eform_version is False


# testing class for get_documents_as_leave_admin
class TestGetDocumentsAsLeaveAdmin:
    @pytest.fixture
    def absence_id(self):
        # TODO: (EMPLOYER-1584): Don't rely on FINEOS mock_client and magic strings for mocking
        return "leave_admin_mixed_allowable_doc_types"

    def test_get_documents(self, absence_id):
        documents = get_documents_as_leave_admin("fake_id", absence_id)
        assert len(documents) > 0

    def test_filters_non_downloadable_documents(self, absence_id):
        documents = get_documents_as_leave_admin("fake_id", absence_id)

        for document in documents:
            assert document.document_type.lower() in DOWNLOADABLE_DOC_TYPES


# testing class for download_document_as_leave_admin
class TestDownloadDocumentAsLeaveAdmin:
    @pytest.fixture
    def documents(self, downloadable_doc, non_downloadable_doc):
        return [downloadable_doc, non_downloadable_doc]

    @pytest.fixture
    def document(self):
        return GroupClientDocument(
            caseId="absence_id",
            rootCaseId="NTN-111",
            documentId=3000,
            name="state managed paid leave confirmation",
            type="Document",
            fileExtension=".pdf",
            fileName="26e82dd7-dbfc-4e7b-9804-ea955627253d.png",
            originalFilename="test.pdf",
            receivedDate=date(2020, 9, 1),
            effectiveFrom=date(2020, 9, 2),
            effectiveTo=date(2020, 9, 3),
            description="Mock File",
            title="",
            isRead=False,
            createdBy="Roberto Carlos",
            dateCreated=None,
            extensionAttributes=[],
            status=None,
            privacyTag=None,
            readForMyOrganisation=None,
        )

    @pytest.fixture
    def downloadable_doc(self, document):
        doc = copy.deepcopy(document)
        doc.documentId = 3001

        return doc

    @pytest.fixture
    def non_downloadable_doc(self, document):
        doc = copy.deepcopy(document)
        doc.documentId = 3002
        doc.name = "Identification Proof"

        return doc

    @mock.patch("massgov.pfml.fineos.mock_client.MockFINEOSClient.group_client_get_documents")
    def test_download_document(self, mock_get_docs, documents, downloadable_doc):
        mock_get_docs.return_value = documents

        doc_id = str(downloadable_doc.documentId)
        document_data = download_document_as_leave_admin("fake_id", "foo", doc_id)

        assert document_data is not None

    @mock.patch("massgov.pfml.fineos.mock_client.MockFINEOSClient.group_client_get_documents")
    def test_document_not_found(self, mock_get_docs, documents):
        mock_get_docs.return_value = documents

        with pytest.raises(ObjectNotFound) as exc_info:
            download_document_as_leave_admin("fake_id", "foo", "bad_doc_id")

        error = exc_info.value
        assert error.description == "Unable to find FINEOS document for user"

    @mock.patch("massgov.pfml.fineos.mock_client.MockFINEOSClient.group_client_get_documents")
    def test_not_authorized_for_document_type(self, mock_get_docs, documents, non_downloadable_doc):
        mock_get_docs.return_value = documents

        doc_id = str(non_downloadable_doc.documentId)
        with pytest.raises(NotAuthorizedForAccess) as exc_info:
            download_document_as_leave_admin("fake_id", "foo", doc_id)

        expected_msg = "User is not authorized to access documents of type: identification proof"
        error = exc_info.value
        assert error.description == expected_msg
