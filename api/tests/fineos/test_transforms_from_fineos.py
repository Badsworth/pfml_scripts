from datetime import date

import pytest

from massgov.pfml.api.models.claims.common import EmployerBenefit, PreviousLeave
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
                {"name": "Frequency", "stringValue": "Per Month"},
                {"name": "ProgramType", "stringValue": "Employer"},
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
                        "instanceValue": "Short term disability",
                    },
                },
                {
                    "name": "WRT4",
                    "enumValue": {"domainName": "WageReplacementType", "instanceValue": "Unknown",},
                },
                {"name": "ProgramType2", "stringValue": "Employer"},
            ],
        }
    )


@pytest.fixture
def other_leave_eform():
    return EForm.parse_obj(
        {
            "eformType": "Other Leaves",
            "eformId": 2230,
            "eformAttributes": [
                {"name": "PriorConcurrent", "stringValue": " Prior"},
                {"name": "PriorConcurrent2", "stringValue": "Prior"},
                {"name": "EndDate2", "dateValue": "2019-12-27"},
                {"name": "SecondaryQualifyingReason", "stringValue": "Military caregiver"},
                {"name": "BeginDate2", "dateValue": "2019-12-04"},
                {
                    "name": "Applies1",
                    "enumValue": {"domainName": "PleaseSelectYesNoUnknown", "instanceValue": "Yes"},
                },
                {"name": "EndDate", "dateValue": "2020-05-31"},
                {
                    "name": "Applies2",
                    "enumValue": {"domainName": "PleaseSelectYesNoUnknown", "instanceValue": "Yes"},
                },
                {
                    "name": "QualifyingReasonPrimary",
                    "enumValue": {
                        "domainName": "NotificationReason",
                        "instanceValue": "Accident or treatment required for an injury",
                    },
                },
                {"name": "BeginDate", "dateValue": "2020-04-01"},
                {
                    "name": "QualifyingReasonPrimary2",
                    "enumValue": {
                        "domainName": "NotificationReason",
                        "instanceValue": "Out of work for another reason",
                    },
                },
                {"name": "SecondaryQualifyingReason2", "stringValue": "Military caregiver"},
            ],
        }
    )


@pytest.fixture
def previous_leave():
    return PreviousLeave(
        leave_start_date="2020-05-15", leave_end_date="2020-06-01", leave_type="Medical"
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
        assert benefit_1["program_type"] == "Employer"

        assert type(employer_benefits_list[1]) is EmployerBenefit
        benefit_2 = employer_benefits_list[1].dict()
        assert benefit_2["benefit_amount_dollars"] == 10000
        assert benefit_2["benefit_amount_frequency"] == "Per Month"
        assert benefit_2["benefit_start_date"] == date(2021, 10, 1)
        assert benefit_2["benefit_end_date"] == date(2021, 11, 1)
        assert benefit_2["benefit_type"] == "Short term disability"
        assert benefit_2["program_type"] == "Employer"

    def test_transform_other_leave_eform(self, other_leave_eform):
        other_leaves_list = TransformOtherLeaveEform.from_fineos(other_leave_eform)
        assert len(other_leaves_list) == 2

        assert type(other_leaves_list[0]) is PreviousLeave
        other_leave_1 = other_leaves_list[0].dict()
        assert other_leave_1["leave_start_date"] == date(2020, 4, 1)
        assert other_leave_1["leave_end_date"] == date(2020, 5, 31)
        assert other_leave_1["leave_type"] == "Accident or treatment required for an injury"

        assert type(other_leaves_list[1]) is PreviousLeave
        other_leave_2 = other_leaves_list[1].dict()
        assert other_leave_2["leave_start_date"] == date(2019, 12, 4)
        assert other_leave_2["leave_end_date"] == date(2019, 12, 27)
        assert other_leave_2["leave_type"] == "Out of work for another reason"
