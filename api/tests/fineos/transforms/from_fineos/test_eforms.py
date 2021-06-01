from datetime import date

import pytest

from massgov.pfml.api.models.common import (
    EmployerBenefit,
    PreviousLeave,
    PreviousLeaveQualifyingReason,
)
from massgov.pfml.fineos.models.group_client_api import EForm
from massgov.pfml.fineos.transforms.from_fineos.eforms import (
    TransformOtherIncomeEform,
    TransformOtherLeaveEform,
)


@pytest.fixture
def other_income_eform():
    return EForm.parse_obj(
        {
            "eformType": "Other Income",
            "eformId": 2229,
            "eformAttributes": [
                {"name": "Amount", "decimalValue": 5000},
                {
                    "name": "ReceiveWageReplacement",
                    "enumValue": {"domainName": "PleaseSelectYesNoUnknown", "instanceValue": "Yes"},
                },
                {"name": "EndDate", "dateValue": "2020-10-30"},
                {
                    "name": "WRT1",
                    "enumValue": {
                        "domainName": "WageReplacementType",
                        "instanceValue": "Accrued paid leave",
                    },
                },
                {
                    "name": "WRT2",
                    "enumValue": {"domainName": "WageReplacementType", "instanceValue": "Unknown",},
                },
                {"name": "StartDate", "dateValue": "2020-10-01"},
                {"name": "Spacer", "stringValue": ""},
                {"name": "Frequency", "stringValue": "Per Month "},
                {
                    "name": "ProgramType",
                    "enumValue": {"domainName": "Program Type", "instanceValue": "Non-Employer"},
                },
                {
                    "name": "ReceiveWageReplacement2",
                    "enumValue": {"domainName": "PleaseSelectYesNoUnknown", "instanceValue": "No"},
                },
                {"name": "Amount2", "decimalValue": 10000},
                {"name": "StartDate2", "dateValue": "2021-10-01"},
                {"name": "EndDate2", "dateValue": "2021-11-01"},
                {"name": "Frequency2", "stringValue": "Per Month"},
                {
                    "name": "WRT3",
                    "enumValue": {
                        "domainName": "WageReplacementType",
                        "instanceValue": "Short-term disability insurance",
                    },
                },
                {
                    "name": "WRT4",
                    "enumValue": {"domainName": "WageReplacementType", "instanceValue": "Unknown",},
                },
                {
                    "name": "ProgramType2",
                    "enumValue": {"domainName": "Program Type", "instanceValue": "Employer"},
                },
            ],
        }
    )


@pytest.fixture
def other_leave_eform():
    return EForm.parse_obj(
        {
            "eformType": "Other Leaves",
            "eformId": 11475,
            "eformAttributes": [
                {"name": "SecondaryQualifyingReason", "stringValue": "Military caregiver"},
                {
                    "name": "QualifyingReason2",
                    "enumValue": {
                        "domainName": "QualifyingReasons",
                        "instanceValue": "Child bonding",
                    },
                },
                {
                    "name": "QualifyingReason1",
                    "enumValue": {
                        "domainName": "QualifyingReasons",
                        "instanceValue": "Pregnancy / Maternity",
                    },
                },
                {"name": "EndDate2", "dateValue": "2020-12-15"},
                {"name": "EndDate1", "dateValue": "2020-09-22"},
                {"name": "BeginDate2", "dateValue": "2020-09-23"},
                {
                    "name": "Applies1",
                    "enumValue": {"domainName": "PleaseSelectYesNoUnknown", "instanceValue": "Yes"},
                },
                {"name": "BeginDate1", "dateValue": "2020-09-01"},
                {
                    "name": "Applies2",
                    "enumValue": {"domainName": "PleaseSelectYesNoUnknown", "instanceValue": "Yes"},
                },
                {
                    "name": "Applies3",
                    "enumValue": {"domainName": "PleaseSelectYesNoUnknown", "instanceValue": "No"},
                },
                {
                    "name": "LeaveFromEmployer2",
                    "enumValue": {"domainName": "PleaseSelectYesNoUnknown", "instanceValue": "Yes"},
                },
                {
                    "name": "LeaveFromEmployer1",
                    "enumValue": {"domainName": "PleaseSelectYesNoUnknown", "instanceValue": "Yes"},
                },
                {"name": "SecondaryQualifyingReason2", "stringValue": "Military caregiver"},
            ],
        }
    )


@pytest.fixture
def other_leave_eform_bad_values():
    return EForm.parse_obj(
        {
            "eformType": "Other Leaves",
            "eformId": 11475,
            "eformAttributes": [
                {"name": "SecondaryQualifyingReason", "stringValue": "Military caregiver"},
                {
                    "name": "QualifyingReason2",
                    "enumValue": {
                        "domainName": "QualifyingReasons",
                        "instanceValue": "Please Select",
                    },
                },
                {
                    "name": "QualifyingReason1",
                    "enumValue": {
                        "domainName": "QualifyingReasons",
                        "instanceValue": "Please Select",
                    },
                },
                {"name": "EndDate2", "dateValue": "2020-12-15"},
                {"name": "EndDate1", "dateValue": "2020-09-22"},
                {"name": "BeginDate2", "dateValue": "2020-09-23"},
                {
                    "name": "Applies1",
                    "enumValue": {"domainName": "PleaseSelectYesNoUnknown", "instanceValue": "Yes"},
                },
                {"name": "BeginDate1", "dateValue": "2020-09-01"},
                {
                    "name": "Applies2",
                    "enumValue": {"domainName": "PleaseSelectYesNoUnknown", "instanceValue": "Yes"},
                },
                {
                    "name": "Applies3",
                    "enumValue": {"domainName": "PleaseSelectYesNoUnknown", "instanceValue": "No"},
                },
                {
                    "name": "LeaveFromEmployer2",
                    "enumValue": {"domainName": "PleaseSelectYesNoUnknown", "instanceValue": "Yes"},
                },
                {
                    "name": "LeaveFromEmployer1",
                    "enumValue": {"domainName": "PleaseSelectYesNoUnknown", "instanceValue": "Yes"},
                },
                {"name": "SecondaryQualifyingReason2", "stringValue": "Military caregiver"},
            ],
        }
    )


@pytest.fixture
def previous_leave():
    return PreviousLeave(
        leave_start_date="2020-05-15",
        leave_end_date="2020-06-01",
        leave_reason=PreviousLeaveQualifyingReason.SERIOUS_HEALTH_CONDITION,
    )


class TestTransformEformBody:
    def test_transform_other_income_eform(self, other_income_eform):
        employer_benefits_list = TransformOtherIncomeEform.from_fineos(other_income_eform)
        assert len(employer_benefits_list) == 2

        assert type(employer_benefits_list[0]) is EmployerBenefit
        benefit_1 = employer_benefits_list[0].dict()
        assert benefit_1["benefit_amount_dollars"] == 5000
        assert benefit_1["benefit_amount_frequency"] == "Per Month"
        assert benefit_1["benefit_start_date"] == date(2020, 10, 1)
        assert benefit_1["benefit_end_date"] == date(2020, 10, 30)
        assert benefit_1["benefit_type"] == "Accrued paid leave"
        assert benefit_1["program_type"] == "Non-Employer"

        assert type(employer_benefits_list[1]) is EmployerBenefit
        benefit_2 = employer_benefits_list[1].dict()
        assert benefit_2["benefit_amount_dollars"] == 10000
        assert benefit_2["benefit_amount_frequency"] == "Per Month"
        assert benefit_2["benefit_start_date"] == date(2021, 10, 1)
        assert benefit_2["benefit_end_date"] == date(2021, 11, 1)
        assert benefit_2["benefit_type"] == "Short-term disability insurance"
        assert benefit_2["program_type"] == "Employer"

    def test_transform_other_leave_eform(self, other_leave_eform):
        other_leaves_list = TransformOtherLeaveEform.from_fineos(other_leave_eform)
        assert len(other_leaves_list) == 2

        assert type(other_leaves_list[0]) is PreviousLeave
        other_leave_1 = other_leaves_list[0].dict()
        assert other_leave_1["leave_start_date"] == date(2020, 9, 1)
        assert other_leave_1["leave_end_date"] == date(2020, 9, 22)
        assert other_leave_1["leave_reason"] == "Pregnancy / Maternity"

        assert type(other_leaves_list[1]) is PreviousLeave
        other_leave_2 = other_leaves_list[1].dict()
        assert other_leave_2["leave_start_date"] == date(2020, 9, 23)
        assert other_leave_2["leave_end_date"] == date(2020, 12, 15)
        assert other_leave_2["leave_reason"] == "Child bonding"

    def test_transform_eform_with_bad_values(self, other_leave_eform_bad_values):
        other_leaves_list = TransformOtherLeaveEform.from_fineos(other_leave_eform_bad_values)
        assert len(other_leaves_list) == 2

        assert type(other_leaves_list[0]) is PreviousLeave
        other_leave_1 = other_leaves_list[0].dict()
        assert other_leave_1["leave_start_date"] == date(2020, 9, 1)
        assert other_leave_1["leave_end_date"] == date(2020, 9, 22)
        assert other_leave_1["leave_reason"] == "Unknown"

        assert type(other_leaves_list[1]) is PreviousLeave
        other_leave_2 = other_leaves_list[1].dict()
        assert other_leave_2["leave_start_date"] == date(2020, 9, 23)
        assert other_leave_2["leave_end_date"] == date(2020, 12, 15)
        assert other_leave_2["leave_reason"] == "Unknown"
