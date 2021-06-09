from datetime import date

import pytest

from massgov.pfml.api.models.common import (
    EmployerBenefit,
    PreviousLeave,
    PreviousLeaveQualifyingReason,
)
from massgov.pfml.fineos.models.group_client_api import EForm
from massgov.pfml.fineos.transforms.from_fineos.eforms import (
    TransformEmployerBenefitsFromOtherIncomeEform,
    TransformOtherIncomeEform,
    TransformPreviousLeaveFromOtherLeaveEform,
)


@pytest.fixture
def deprecated_other_income_eform():
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
                        "instanceValue": "Short-term disability insurance",
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
def other_income_eform():
    return EForm.parse_obj(
        {
            "eformType": "Other Income - current version",
            "eformAttributes": [
                {
                    "name": "V2OtherIncomeNonEmployerBenefitWRT1",
                    "enumValue": {
                        "domainName": "WageReplacementType2",
                        "instanceValue": "Social Security Disability Insurance",
                    },
                },
                {"name": "V2Spacer1", "stringValue": ""},
                {
                    "name": "V2ReceiveWageReplacement7",
                    "enumValue": {"domainName": "PleaseSelectYesNo", "instanceValue": "Yes"},
                },
                {"name": "Spacer11", "stringValue": ""},
                {
                    "name": "V2ReceiveWageReplacement8",
                    "enumValue": {"domainName": "PleaseSelectYesNo", "instanceValue": "No"},
                },
                {
                    "name": "V2SalaryContinuation1",
                    "enumValue": {
                        "domainName": "PleaseSelectYesNo",
                        "instanceValue": "Please Select",
                    },
                },
                {"name": "V2Spacer3", "stringValue": ""},
                {"name": "V2Spacer2", "stringValue": ""},
                {
                    "name": "V2SalaryContinuation2",
                    "enumValue": {"domainName": "PleaseSelectYesNo", "instanceValue": "No"},
                },
                {"name": "V2Spacer5", "stringValue": ""},
                {
                    "name": "V2ReceiveWageReplacement3",
                    "enumValue": {"domainName": "PleaseSelectYesNo", "instanceValue": "No"},
                },
                {"name": "V2Spacer4", "stringValue": ""},
                {"name": "V2Spacer7", "stringValue": ""},
                {"name": "V2Spacer6", "stringValue": ""},
                {"name": "V2Header1", "stringValue": "Employer-Sponsored Benefits"},
                {"name": "V2Spacer9", "stringValue": ""},
                {"name": "V2Header2", "stringValue": "Income from Other Sources"},
                {"name": "V2Spacer8", "stringValue": ""},
                {
                    "name": "V2ReceiveWageReplacement1",
                    "enumValue": {"domainName": "PleaseSelectYesNo", "instanceValue": "Yes"},
                },
                {
                    "name": "V2ReceiveWageReplacement2",
                    "enumValue": {"domainName": "PleaseSelectYesNo", "instanceValue": "Yes"},
                },
                {
                    "name": "V2Examples7",
                    "stringValue": "Workers Compensation, Unemployment Insurance, Social Security Disability Insurance, Disability benefits under a governmental retirement plan such as STRS or PERS, Jones Act benefits, Railroad Retirement benefit, Earnings from another employer or through self-employment",
                },
                {"name": "V2OtherIncomeNonEmployerBenefitStartDate1", "dateValue": "2021-05-04"},
                {
                    "name": "V2WRT1",
                    "enumValue": {
                        "domainName": "WageReplacementType",
                        "instanceValue": "Permanent disability insurance",
                    },
                },
                {
                    "name": "V2WRT2",
                    "enumValue": {
                        "domainName": "WageReplacementType",
                        "instanceValue": "Temporary disability insurance (Long- or Short-term)",
                    },
                },
                {
                    "name": "V2Frequency2",
                    "enumValue": {
                        "domainName": "FrequencyEforms",
                        "instanceValue": "One Time / Lump Sum",
                    },
                },
                {
                    "name": "V2Frequency1",
                    "enumValue": {"domainName": "FrequencyEforms", "instanceValue": "Per Day"},
                },
                {"name": "V2OtherIncomeNonEmployerBenefitEndDate1", "dateValue": "2021-05-29"},
                {"name": "V2StartDate1", "dateValue": "2021-05-11"},
                {"name": "V2EndDate1", "dateValue": "2021-05-29"},
                {"name": "V2Amount1", "decimalValue": 40},
                {"name": "V2EndDate2", "dateValue": "2021-05-29"},
                {"name": "V2Amount2", "decimalValue": 100},
                {"name": "V2StartDate2", "dateValue": "2021-05-18"},
                {"name": "V2OtherIncomeNonEmployerBenefitAmount1", "decimalValue": 100.0},
                {"name": "V2Spacer10", "stringValue": ""},
                {
                    "name": "V2OtherIncomeNonEmployerBenefitFrequency1",
                    "enumValue": {
                        "domainName": "FrequencyEforms",
                        "instanceValue": "One Time / Lump Sum",
                    },
                },
            ],
            "eformId": 8296,
        }
    )


@pytest.fixture
def other_leave_eform():
    return EForm.parse_obj(
        {
            "eformType": "Other Leaves",
            "eformId": 11475,
            "eformAttributes": [
                {"name": "V2SecondaryQualifyingReason", "stringValue": "Military caregiver"},
                {
                    "name": "V2QualifyingReason2",
                    "enumValue": {
                        "domainName": "QualifyingReasons",
                        "instanceValue": "Bonding with my child after birth or placement",
                    },
                },
                {
                    "name": "V2QualifyingReason1",
                    "enumValue": {"domainName": "QualifyingReasons", "instanceValue": "Pregnancy",},
                },
                {"name": "V2OtherLeavesPastLeaveEndDate2", "dateValue": "2020-12-15"},
                {"name": "V2OtherLeavesPastLeaveEndDate1", "dateValue": "2020-09-22"},
                {"name": "V2OtherLeavesPastLeaveStartDate2", "dateValue": "2020-09-23"},
                {
                    "name": "V2Applies1",
                    "enumValue": {"domainName": "PleaseSelectYesNoUnknown", "instanceValue": "Yes"},
                },
                {"name": "V2OtherLeavesPastLeaveStartDate1", "dateValue": "2020-09-01"},
                {
                    "name": "V2Applies2",
                    "enumValue": {"domainName": "PleaseSelectYesNoUnknown", "instanceValue": "Yes"},
                },
                {
                    "name": "V2Applies3",
                    "enumValue": {"domainName": "PleaseSelectYesNoUnknown", "instanceValue": "No"},
                },
                {
                    "name": "V2LeaveFromEmployer2",
                    "enumValue": {"domainName": "PleaseSelectYesNoUnknown", "instanceValue": "Yes"},
                },
                {
                    "name": "V2LeaveFromEmployer1",
                    "enumValue": {"domainName": "PleaseSelectYesNoUnknown", "instanceValue": "Yes"},
                },
                {"name": "V2SecondaryQualifyingReason2", "stringValue": "Military caregiver"},
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
                {"name": "V2SecondaryQualifyingReason", "stringValue": "Military caregiver"},
                {
                    "name": "V2QualifyingReason2",
                    "enumValue": {
                        "domainName": "QualifyingReasons",
                        "instanceValue": "Please Select",
                    },
                },
                {
                    "name": "V2QualifyingReason1",
                    "enumValue": {
                        "domainName": "QualifyingReasons",
                        "instanceValue": "Please Select",
                    },
                },
                {"name": "V2OtherLeavesPastLeaveEndDate2", "dateValue": "2020-12-15"},
                {"name": "V2OtherLeavesPastLeaveEndDate1", "dateValue": "2020-09-22"},
                {"name": "V2OtherLeavesPastLeaveStartDate2", "dateValue": "2020-09-23"},
                {
                    "name": "V2Applies1",
                    "enumValue": {"domainName": "PleaseSelectYesNoUnknown", "instanceValue": "Yes"},
                },
                {"name": "V2OtherLeavesPastLeaveStartDate1", "dateValue": "2020-09-01"},
                {
                    "name": "V2Applies2",
                    "enumValue": {"domainName": "PleaseSelectYesNoUnknown", "instanceValue": "Yes"},
                },
                {
                    "name": "V2Applies3",
                    "enumValue": {"domainName": "PleaseSelectYesNoUnknown", "instanceValue": "No"},
                },
                {
                    "name": "V2LeaveFromEmployer2",
                    "enumValue": {"domainName": "PleaseSelectYesNoUnknown", "instanceValue": "Yes"},
                },
                {
                    "name": "V2LeaveFromEmployer1",
                    "enumValue": {"domainName": "PleaseSelectYesNoUnknown", "instanceValue": "Yes"},
                },
                {"name": "V2SecondaryQualifyingReason2", "stringValue": "Military caregiver"},
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
    def test_transform_deprecated_other_income_eform(self, deprecated_other_income_eform):
        employer_benefits_list = TransformOtherIncomeEform.from_fineos(
            deprecated_other_income_eform
        )
        assert len(employer_benefits_list) == 2

        assert type(employer_benefits_list[0]) is EmployerBenefit
        benefit_1 = employer_benefits_list[0].dict()
        assert benefit_1["benefit_amount_dollars"] == 5000
        assert benefit_1["benefit_amount_frequency"] == "Per Month"
        assert benefit_1["benefit_start_date"] == date(2020, 10, 1)
        assert benefit_1["benefit_end_date"] == date(2020, 10, 30)
        assert benefit_1["benefit_type"] == "Short-term disability insurance"
        assert benefit_1["program_type"] == "Non-Employer"

        assert type(employer_benefits_list[1]) is EmployerBenefit
        benefit_2 = employer_benefits_list[1].dict()
        assert benefit_2["benefit_amount_dollars"] == 10000
        assert benefit_2["benefit_amount_frequency"] == "Per Month"
        assert benefit_2["benefit_start_date"] == date(2021, 10, 1)
        assert benefit_2["benefit_end_date"] == date(2021, 11, 1)
        assert benefit_2["benefit_type"] == "Short-term disability insurance"
        assert benefit_2["program_type"] == "Employer"

    def test_transform_employer_benefits_from_other_income_eform(self, other_income_eform):
        employer_benefits_list = TransformEmployerBenefitsFromOtherIncomeEform.from_fineos(
            other_income_eform
        )
        assert len(employer_benefits_list) == 2

        assert type(employer_benefits_list[0]) is EmployerBenefit
        benefit_1 = employer_benefits_list[0].dict()
        assert benefit_1["benefit_amount_dollars"] == 40
        assert benefit_1["benefit_amount_frequency"] == "Per Day"
        assert benefit_1["benefit_start_date"] == date(2021, 5, 11)
        assert benefit_1["benefit_end_date"] == date(2021, 5, 29)
        assert benefit_1["benefit_type"] == "Permanent disability insurance"
        assert benefit_1["is_full_salary_continuous"] is None

        assert type(employer_benefits_list[1]) is EmployerBenefit
        benefit_2 = employer_benefits_list[1].dict()
        assert benefit_2["benefit_amount_dollars"] == 100
        assert benefit_2["benefit_amount_frequency"] == "In Total"
        assert benefit_2["benefit_start_date"] == date(2021, 5, 18)
        assert benefit_2["benefit_end_date"] == date(2021, 5, 29)
        assert benefit_2["benefit_type"] == "Short-term disability insurance"
        assert benefit_2["is_full_salary_continuous"] is False

    def test_transform_other_leave_eform(self, other_leave_eform):
        other_leaves_list = TransformPreviousLeaveFromOtherLeaveEform.from_fineos(other_leave_eform)
        assert len(other_leaves_list) == 2

        assert type(other_leaves_list[0]) is PreviousLeave
        other_leave_1 = other_leaves_list[0].dict()
        assert other_leave_1["leave_start_date"] == date(2020, 9, 1)
        assert other_leave_1["leave_end_date"] == date(2020, 9, 22)
        assert other_leave_1["leave_reason"] == "Pregnancy"

        assert type(other_leaves_list[1]) is PreviousLeave
        other_leave_2 = other_leaves_list[1].dict()
        assert other_leave_2["leave_start_date"] == date(2020, 9, 23)
        assert other_leave_2["leave_end_date"] == date(2020, 12, 15)
        assert other_leave_2["leave_reason"] == "Bonding with my child after birth or placement"

    def test_transform_eform_with_bad_values(self, other_leave_eform_bad_values):
        other_leaves_list = TransformPreviousLeaveFromOtherLeaveEform.from_fineos(
            other_leave_eform_bad_values
        )
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
