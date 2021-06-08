from datetime import date

import faker

from massgov.pfml.api.models.applications.common import OtherIncome
from massgov.pfml.api.models.common import ConcurrentLeave, EmployerBenefit, PreviousLeave
from massgov.pfml.db.models.applications import (
    AmountFrequency,
    EmployerBenefitType,
    OtherIncomeType,
    PreviousLeaveQualifyingReason,
)
from massgov.pfml.fineos.transforms.to_fineos.eforms.employee import (
    OtherIncomesEFormBuilder,
    PreviousLeavesEFormBuilder,
)

fake = faker.Faker()


def previous_leave():
    start_date = fake.date_between("-3m", "today")
    return PreviousLeave(
        leave_start_date=start_date,
        leave_end_date=fake.date_between_dates(start_date, date.today()),
        is_for_current_employer=True,
        leave_reason=PreviousLeaveQualifyingReason.PREGNANCY_MATERNITY,
        worked_per_week_minutes=2430,
        leave_minutes=3600,
    )


def concurrent_leave():
    start_date = fake.date_between("-3m", "today")
    return ConcurrentLeave(
        leave_start_date=start_date,
        leave_end_date=fake.date_between_dates(start_date, date.today()),
        is_for_current_employer=False,
    )


def employer_benefit():
    start_date = fake.date_between("-3m", "today")
    return EmployerBenefit(
        benefit_start_date=start_date,
        benefit_end_date=fake.date_between_dates(start_date, date.today()),
        benefit_type=EmployerBenefitType.ACCRUED_PAID_LEAVE,
        benefit_amount_dollars=fake.random_int(),
        benefit_amount_frequency=AmountFrequency.PER_MONTH,
    )


def other_income():
    start_date = fake.date_between("-3m", "today")
    return OtherIncome(
        income_start_date=start_date,
        income_end_date=fake.date_between_dates(start_date, date.today()),
        income_type=OtherIncomeType.SSDI,
        income_amount_dollars=fake.random_int(),
        income_amount_frequency=AmountFrequency.PER_MONTH,
    )


def test_other_incomes():
    incomes = [other_income(), other_income()]
    benefits = [employer_benefit(), employer_benefit()]
    eform_body = OtherIncomesEFormBuilder.build(benefits, incomes, False)
    assert eform_body.eformType == "Other Income"

    expected_attributes = [
        {"dateValue": benefits[0].benefit_start_date.isoformat(), "name": "StartDate"},
        {"dateValue": benefits[0].benefit_end_date.isoformat(), "name": "EndDate"},
        {"decimalValue": benefits[0].benefit_amount_dollars, "name": "Amount"},
        {"name": "Frequency", "stringValue": "Per Month"},
        {
            "enumValue": {
                "domainName": "WageReplacementType",
                "instanceValue": "Accrued paid leave",
            },
            "name": "WRT1",
        },
        {
            "enumValue": {"domainName": "WageReplacementType2", "instanceValue": "Please Select"},
            "name": "WRT2",
        },
        {
            "enumValue": {"domainName": "Program Type", "instanceValue": "Employer"},
            "name": "ProgramType",
        },
        {
            "enumValue": {"domainName": "YesNoI'veApplied", "instanceValue": "Yes"},
            "name": "ReceiveWageReplacement",
        },
        {"dateValue": benefits[1].benefit_start_date.isoformat(), "name": "StartDate2"},
        {"dateValue": benefits[1].benefit_end_date.isoformat(), "name": "EndDate2"},
        {"decimalValue": benefits[1].benefit_amount_dollars, "name": "Amount2"},
        {"name": "Frequency2", "stringValue": "Per Month"},
        {
            "enumValue": {
                "domainName": "WageReplacementType",
                "instanceValue": "Accrued paid leave",
            },
            "name": "WRT3",
        },
        {
            "enumValue": {"domainName": "WageReplacementType2", "instanceValue": "Please Select"},
            "name": "WRT4",
        },
        {
            "enumValue": {"domainName": "Program Type", "instanceValue": "Employer"},
            "name": "ProgramType2",
        },
        {
            "enumValue": {"domainName": "YesNoI'veApplied", "instanceValue": "Yes"},
            "name": "ReceiveWageReplacement2",
        },
        {"dateValue": incomes[0].income_start_date.isoformat(), "name": "StartDate3"},
        {"dateValue": incomes[0].income_end_date.isoformat(), "name": "EndDate3"},
        {"decimalValue": incomes[0].income_amount_dollars, "name": "Amount3"},
        {"name": "Frequency3", "stringValue": "Per Month"},
        {
            "enumValue": {"domainName": "WageReplacementType2", "instanceValue": "SSDI"},
            "name": "WRT6",
        },
        {
            "enumValue": {"domainName": "WageReplacementType", "instanceValue": "Please Select"},
            "name": "WRT5",
        },
        {
            "enumValue": {"domainName": "Program Type", "instanceValue": "Non-Employer"},
            "name": "ProgramType3",
        },
        {
            "enumValue": {"domainName": "YesNoI'veApplied", "instanceValue": "Yes"},
            "name": "ReceiveWageReplacement3",
        },
        {"dateValue": incomes[1].income_start_date.isoformat(), "name": "StartDate4"},
        {"dateValue": incomes[1].income_end_date.isoformat(), "name": "EndDate4"},
        {"decimalValue": incomes[1].income_amount_dollars, "name": "Amount4"},
        {"name": "Frequency4", "stringValue": "Per Month"},
        {
            "enumValue": {"domainName": "WageReplacementType2", "instanceValue": "SSDI"},
            "name": "WRT8",
        },
        {
            "enumValue": {"domainName": "WageReplacementType", "instanceValue": "Please Select"},
            "name": "WRT7",
        },
        {
            "enumValue": {"domainName": "Program Type", "instanceValue": "Non-Employer"},
            "name": "ProgramType4",
        },
        {
            "enumValue": {"domainName": "YesNoI'veApplied", "instanceValue": "Yes"},
            "name": "ReceiveWageReplacement4",
        },
    ]

    assert eform_body.eformAttributes == expected_attributes


def test_other_incomes_benefits_only():
    benefits = [employer_benefit(), employer_benefit()]
    eform_body = OtherIncomesEFormBuilder.build(benefits, [], False)
    assert eform_body.eformType == "Other Income"

    expected_attributes = [
        {"dateValue": benefits[0].benefit_start_date.isoformat(), "name": "StartDate"},
        {"dateValue": benefits[0].benefit_end_date.isoformat(), "name": "EndDate"},
        {"decimalValue": benefits[0].benefit_amount_dollars, "name": "Amount"},
        {"name": "Frequency", "stringValue": "Per Month"},
        {
            "enumValue": {
                "domainName": "WageReplacementType",
                "instanceValue": "Accrued paid leave",
            },
            "name": "WRT1",
        },
        {
            "enumValue": {"domainName": "WageReplacementType2", "instanceValue": "Please Select"},
            "name": "WRT2",
        },
        {
            "enumValue": {"domainName": "Program Type", "instanceValue": "Employer"},
            "name": "ProgramType",
        },
        {
            "enumValue": {"domainName": "YesNoI'veApplied", "instanceValue": "Yes"},
            "name": "ReceiveWageReplacement",
        },
        {"dateValue": benefits[1].benefit_start_date.isoformat(), "name": "StartDate2"},
        {"dateValue": benefits[1].benefit_end_date.isoformat(), "name": "EndDate2"},
        {"decimalValue": benefits[1].benefit_amount_dollars, "name": "Amount2"},
        {"name": "Frequency2", "stringValue": "Per Month"},
        {
            "enumValue": {
                "domainName": "WageReplacementType",
                "instanceValue": "Accrued paid leave",
            },
            "name": "WRT3",
        },
        {
            "enumValue": {"domainName": "WageReplacementType2", "instanceValue": "Please Select"},
            "name": "WRT4",
        },
        {
            "enumValue": {"domainName": "Program Type", "instanceValue": "Employer"},
            "name": "ProgramType2",
        },
        {
            "enumValue": {"domainName": "YesNoI'veApplied", "instanceValue": "Yes"},
            "name": "ReceiveWageReplacement2",
        },
    ]

    assert eform_body.eformAttributes == expected_attributes


def test_other_incomes_incomes_only():
    incomes = [other_income(), other_income()]
    eform_body = OtherIncomesEFormBuilder.build([], incomes, False)
    assert eform_body.eformType == "Other Income"

    expected_attributes = [
        {"dateValue": incomes[0].income_start_date.isoformat(), "name": "StartDate"},
        {"dateValue": incomes[0].income_end_date.isoformat(), "name": "EndDate"},
        {"decimalValue": incomes[0].income_amount_dollars, "name": "Amount"},
        {"name": "Frequency", "stringValue": "Per Month"},
        {
            "enumValue": {"domainName": "WageReplacementType2", "instanceValue": "SSDI"},
            "name": "WRT2",
        },
        {
            "enumValue": {"domainName": "WageReplacementType", "instanceValue": "Please Select"},
            "name": "WRT1",
        },
        {
            "enumValue": {"domainName": "Program Type", "instanceValue": "Non-Employer"},
            "name": "ProgramType",
        },
        {
            "enumValue": {"domainName": "YesNoI'veApplied", "instanceValue": "Yes"},
            "name": "ReceiveWageReplacement",
        },
        {"dateValue": incomes[1].income_start_date.isoformat(), "name": "StartDate2"},
        {"dateValue": incomes[1].income_end_date.isoformat(), "name": "EndDate2"},
        {"decimalValue": incomes[1].income_amount_dollars, "name": "Amount2"},
        {"name": "Frequency2", "stringValue": "Per Month"},
        {
            "enumValue": {"domainName": "WageReplacementType2", "instanceValue": "SSDI"},
            "name": "WRT4",
        },
        {
            "enumValue": {"domainName": "WageReplacementType", "instanceValue": "Please Select"},
            "name": "WRT3",
        },
        {
            "enumValue": {"domainName": "Program Type", "instanceValue": "Non-Employer"},
            "name": "ProgramType2",
        },
        {
            "enumValue": {"domainName": "YesNoI'veApplied", "instanceValue": "Yes"},
            "name": "ReceiveWageReplacement2",
        },
    ]

    assert eform_body.eformAttributes == expected_attributes


def test_other_incomes_awaiting_approval():
    eform_body = OtherIncomesEFormBuilder.build([], [], True)
    assert eform_body.eformType == "Other Income"

    expected_attributes = [
        {
            "enumValue": {
                "domainName": "YesNoI'veApplied",
                "instanceValue": "I've applied, but haven't been approved",
            },
            "name": "ReceiveWageReplacement",
        },
    ]

    assert eform_body.eformAttributes == expected_attributes


def test_other_incomes_benefits_and_awaiting_approval():
    benefits = [employer_benefit(), employer_benefit()]
    eform_body = OtherIncomesEFormBuilder.build(benefits, [], True)
    assert eform_body.eformType == "Other Income"

    expected_attributes = [
        {"name": "StartDate", "dateValue": benefits[0].benefit_start_date.isoformat(),},
        {"name": "EndDate", "dateValue": benefits[0].benefit_end_date.isoformat(),},
        {"name": "Amount", "decimalValue": benefits[0].benefit_amount_dollars,},
        {"name": "Frequency", "stringValue": "Per Month"},
        {
            "name": "WRT1",
            "enumValue": {
                "domainName": "WageReplacementType",
                "instanceValue": "Accrued paid leave",
            },
        },
        {
            "name": "WRT2",
            "enumValue": {"domainName": "WageReplacementType2", "instanceValue": "Please Select"},
        },
        {
            "name": "ProgramType",
            "enumValue": {"domainName": "Program Type", "instanceValue": "Employer"},
        },
        {
            "name": "ReceiveWageReplacement",
            "enumValue": {"domainName": "YesNoI'veApplied", "instanceValue": "Yes"},
        },
        {"name": "StartDate2", "dateValue": benefits[1].benefit_start_date.isoformat(),},
        {"name": "EndDate2", "dateValue": benefits[1].benefit_end_date.isoformat(),},
        {"name": "Amount2", "decimalValue": benefits[1].benefit_amount_dollars,},
        {"name": "Frequency2", "stringValue": "Per Month"},
        {
            "name": "WRT3",
            "enumValue": {
                "domainName": "WageReplacementType",
                "instanceValue": "Accrued paid leave",
            },
        },
        {
            "name": "WRT4",
            "enumValue": {"domainName": "WageReplacementType2", "instanceValue": "Please Select"},
        },
        {
            "name": "ProgramType2",
            "enumValue": {"domainName": "Program Type", "instanceValue": "Employer"},
        },
        {
            "name": "ReceiveWageReplacement2",
            "enumValue": {"domainName": "YesNoI'veApplied", "instanceValue": "Yes"},
        },
        {
            "name": "ReceiveWageReplacement3",
            "enumValue": {
                "domainName": "YesNoI'veApplied",
                "instanceValue": "I've applied, but haven't been approved",
            },
        },
    ]

    assert eform_body.eformAttributes == expected_attributes


def test_transform_previous_leaves():
    previous_leaves = [previous_leave(), previous_leave()]
    previous_leaves[1].is_for_current_employer = False
    concurrent_leave_one = concurrent_leave()
    eform_body = PreviousLeavesEFormBuilder.build(previous_leaves, concurrent_leave_one)
    assert eform_body.eformType == "Other Leaves - current version"
    expected_attributes = [
        {
            "dateValue": previous_leaves[0].leave_start_date.isoformat(),
            "name": "V2OtherLeavesPastLeaveStartDate1",
        },
        {
            "dateValue": previous_leaves[0].leave_end_date.isoformat(),
            "name": "V2OtherLeavesPastLeaveEndDate1",
        },
        {
            "enumValue": {"domainName": "QualifyingReasons", "instanceValue": "Pregnancy",},
            "name": "V2QualifyingReason1",
        },
        {
            "enumValue": {"domainName": "PleaseSelectYesNo", "instanceValue": "Yes"},
            "name": "V2LeaveFromEmployer1",
        },
        {
            "enumValue": {"domainName": "PleaseSelectYesNo", "instanceValue": "No"},
            "name": "V2Leave1",
        },
        {"integerValue": 40, "name": "V2HoursWorked1"},
        {
            "enumValue": {"domainName": "15MinuteIncrements", "instanceValue": "30"},
            "name": "V2MinutesWorked1",
        },
        {"integerValue": 60, "name": "V2TotalHours1"},
        {
            "enumValue": {"domainName": "15MinuteIncrements", "instanceValue": "00"},
            "name": "V2TotalMinutes1",
        },
        {
            "enumValue": {"domainName": "PleaseSelectYesNo", "instanceValue": "Yes"},
            "name": "V2Applies1",
        },
        {
            "dateValue": previous_leaves[1].leave_start_date.isoformat(),
            "name": "V2OtherLeavesPastLeaveStartDate2",
        },
        {
            "dateValue": previous_leaves[1].leave_end_date.isoformat(),
            "name": "V2OtherLeavesPastLeaveEndDate2",
        },
        {
            "enumValue": {"domainName": "QualifyingReasons", "instanceValue": "Pregnancy",},
            "name": "V2QualifyingReason2",
        },
        {
            "enumValue": {"domainName": "PleaseSelectYesNo", "instanceValue": "No"},
            "name": "V2LeaveFromEmployer2",
        },
        {
            "enumValue": {"domainName": "PleaseSelectYesNo", "instanceValue": "No"},
            "name": "V2Leave2",
        },
        {"integerValue": 40, "name": "V2HoursWorked2"},
        {
            "enumValue": {"domainName": "15MinuteIncrements", "instanceValue": "30"},
            "name": "V2MinutesWorked2",
        },
        {"integerValue": 60, "name": "V2TotalHours2"},
        {
            "enumValue": {"domainName": "15MinuteIncrements", "instanceValue": "00"},
            "name": "V2TotalMinutes2",
        },
        {
            "enumValue": {"domainName": "PleaseSelectYesNo", "instanceValue": "Yes"},
            "name": "V2Applies2",
        },
        {
            "dateValue": concurrent_leave_one.leave_start_date.isoformat(),
            "name": "V2AccruedStartDate1",
        },
        {"dateValue": concurrent_leave_one.leave_end_date.isoformat(), "name": "V2AccruedEndDate1"},
        {
            "enumValue": {"domainName": "PleaseSelectYesNo", "instanceValue": "No"},
            "name": "V2AccruedPLEmployer1",
        },
        {
            "enumValue": {"domainName": "PleaseSelectYesNo", "instanceValue": "Yes"},
            "name": "V2AccruedPaidLeave1",
        },
    ]

    assert eform_body.eformAttributes == expected_attributes
