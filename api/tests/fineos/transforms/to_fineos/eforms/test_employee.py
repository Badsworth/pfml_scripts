from datetime import date

import faker

from massgov.pfml.api.models.applications.common import OtherIncome
from massgov.pfml.api.models.common import AmountFrequency as ApiAmountFrequency
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


def employer_benefit(benefit_type=EmployerBenefitType.SHORT_TERM_DISABILITY):
    start_date = fake.date_between("-3m", "today")
    return EmployerBenefit(
        benefit_start_date=start_date,
        benefit_end_date=fake.date_between_dates(start_date, date.today()),
        benefit_type=benefit_type,
        benefit_amount_dollars=fake.random_int(),
        benefit_amount_frequency=AmountFrequency.PER_MONTH,
    )


def other_income(income_type=OtherIncomeType.SSDI):
    start_date = fake.date_between("-3m", "today")
    return OtherIncome(
        income_start_date=start_date,
        income_end_date=fake.date_between_dates(start_date, date.today()),
        income_type=income_type,
        income_amount_dollars=fake.random_int(),
        income_amount_frequency=AmountFrequency.PER_MONTH,
    )


def test_other_incomes():
    income_types = [
        OtherIncomeType.WORKERS_COMP,
        OtherIncomeType.SSDI,
        OtherIncomeType.UNEMPLOYMENT,
        OtherIncomeType.RETIREMENT_DISABILITY,
        OtherIncomeType.JONES_ACT,
        OtherIncomeType.RAILROAD_RETIREMENT,
        OtherIncomeType.OTHER_EMPLOYER,
    ]
    incomes = [other_income(income_type) for income_type in income_types]
    # test all of the amount frequency types
    incomes[0].income_amount_frequency = ApiAmountFrequency.per_day
    incomes[1].income_amount_frequency = ApiAmountFrequency.per_week
    incomes[2].income_amount_frequency = ApiAmountFrequency.all_at_once
    benefit_types = [
        EmployerBenefitType.SHORT_TERM_DISABILITY,
        EmployerBenefitType.PERMANENT_DISABILITY_INSURANCE,
        EmployerBenefitType.FAMILY_OR_MEDICAL_LEAVE_INSURANCE,
    ]
    benefits = [employer_benefit(benefit_type) for benefit_type in benefit_types]
    eform_body = OtherIncomesEFormBuilder.build(benefits, incomes)
    assert eform_body.eformType == "Other Income - current version"

    expected_attributes = [
        {"dateValue": benefits[0].benefit_start_date.isoformat(), "name": "V2StartDate1"},
        {"dateValue": benefits[0].benefit_end_date.isoformat(), "name": "V2EndDate1"},
        {"decimalValue": benefits[0].benefit_amount_dollars, "name": "V2Amount1"},
        {
            "enumValue": {"domainName": "FrequencyEforms", "instanceValue": "Per Month"},
            "name": "V2Frequency1",
        },
        {
            "enumValue": {"domainName": "PleaseSelectYesNo", "instanceValue": "No"},
            "name": "V2SalaryContinuation1",
        },
        {
            "enumValue": {
                "domainName": "WageReplacementType",
                "instanceValue": "Temporary disability insurance (Long- or Short-term)",
            },
            "name": "V2WRT1",
        },
        {
            "enumValue": {"domainName": "PleaseSelectYesNo", "instanceValue": "Yes"},
            "name": "V2ReceiveWageReplacement1",
        },
        {"dateValue": benefits[1].benefit_start_date.isoformat(), "name": "V2StartDate2"},
        {"dateValue": benefits[1].benefit_end_date.isoformat(), "name": "V2EndDate2"},
        {"decimalValue": benefits[1].benefit_amount_dollars, "name": "V2Amount2"},
        {
            "enumValue": {"domainName": "FrequencyEforms", "instanceValue": "Per Month"},
            "name": "V2Frequency2",
        },
        {
            "enumValue": {"domainName": "PleaseSelectYesNo", "instanceValue": "No"},
            "name": "V2SalaryContinuation2",
        },
        {
            "enumValue": {
                "domainName": "WageReplacementType",
                "instanceValue": "Permanent disability insurance",
            },
            "name": "V2WRT2",
        },
        {
            "enumValue": {"domainName": "PleaseSelectYesNo", "instanceValue": "Yes"},
            "name": "V2ReceiveWageReplacement2",
        },
        {"dateValue": benefits[2].benefit_start_date.isoformat(), "name": "V2StartDate3"},
        {"dateValue": benefits[2].benefit_end_date.isoformat(), "name": "V2EndDate3"},
        {"decimalValue": benefits[2].benefit_amount_dollars, "name": "V2Amount3"},
        {
            "enumValue": {"domainName": "FrequencyEforms", "instanceValue": "Per Month"},
            "name": "V2Frequency3",
        },
        {
            "enumValue": {"domainName": "PleaseSelectYesNo", "instanceValue": "No"},
            "name": "V2SalaryContinuation3",
        },
        {
            "enumValue": {
                "domainName": "WageReplacementType",
                "instanceValue": "Family or medical leave, such as a parental leave policy",
            },
            "name": "V2WRT3",
        },
        {
            "enumValue": {"domainName": "PleaseSelectYesNo", "instanceValue": "Yes"},
            "name": "V2ReceiveWageReplacement3",
        },
        {
            "dateValue": incomes[0].income_start_date.isoformat(),
            "name": "V2OtherIncomeNonEmployerBenefitStartDate1",
        },
        {
            "dateValue": incomes[0].income_end_date.isoformat(),
            "name": "V2OtherIncomeNonEmployerBenefitEndDate1",
        },
        {
            "decimalValue": incomes[0].income_amount_dollars,
            "name": "V2OtherIncomeNonEmployerBenefitAmount1",
        },
        {
            "enumValue": {"domainName": "FrequencyEforms", "instanceValue": "Per Day"},
            "name": "V2OtherIncomeNonEmployerBenefitFrequency1",
        },
        {
            "enumValue": {
                "domainName": "WageReplacementType2",
                "instanceValue": "Workers Compensation",
            },
            "name": "V2OtherIncomeNonEmployerBenefitWRT1",
        },
        {
            "enumValue": {"domainName": "YesNoI'veApplied", "instanceValue": "Yes"},
            "name": "V2ReceiveWageReplacement7",
        },
        {
            "dateValue": incomes[1].income_start_date.isoformat(),
            "name": "V2OtherIncomeNonEmployerBenefitStartDate2",
        },
        {
            "dateValue": incomes[1].income_end_date.isoformat(),
            "name": "V2OtherIncomeNonEmployerBenefitEndDate2",
        },
        {
            "decimalValue": incomes[1].income_amount_dollars,
            "name": "V2OtherIncomeNonEmployerBenefitAmount2",
        },
        {
            "enumValue": {"domainName": "FrequencyEforms", "instanceValue": "Per Week"},
            "name": "V2OtherIncomeNonEmployerBenefitFrequency2",
        },
        {
            "enumValue": {
                "domainName": "WageReplacementType2",
                "instanceValue": "Social Security Disability Insurance",
            },
            "name": "V2OtherIncomeNonEmployerBenefitWRT2",
        },
        {
            "enumValue": {"domainName": "YesNoI'veApplied", "instanceValue": "Yes"},
            "name": "V2ReceiveWageReplacement8",
        },
        {
            "dateValue": incomes[2].income_start_date.isoformat(),
            "name": "V2OtherIncomeNonEmployerBenefitStartDate3",
        },
        {
            "dateValue": incomes[2].income_end_date.isoformat(),
            "name": "V2OtherIncomeNonEmployerBenefitEndDate3",
        },
        {
            "decimalValue": incomes[2].income_amount_dollars,
            "name": "V2OtherIncomeNonEmployerBenefitAmount3",
        },
        {
            "enumValue": {"domainName": "FrequencyEforms", "instanceValue": "One Time / Lump Sum"},
            "name": "V2OtherIncomeNonEmployerBenefitFrequency3",
        },
        {
            "enumValue": {
                "domainName": "WageReplacementType2",
                "instanceValue": "Unemployment Insurance",
            },
            "name": "V2OtherIncomeNonEmployerBenefitWRT3",
        },
        {
            "enumValue": {"domainName": "YesNoI'veApplied", "instanceValue": "Yes"},
            "name": "V2ReceiveWageReplacement9",
        },
        {
            "dateValue": incomes[3].income_start_date.isoformat(),
            "name": "V2OtherIncomeNonEmployerBenefitStartDate4",
        },
        {
            "dateValue": incomes[3].income_end_date.isoformat(),
            "name": "V2OtherIncomeNonEmployerBenefitEndDate4",
        },
        {
            "decimalValue": incomes[3].income_amount_dollars,
            "name": "V2OtherIncomeNonEmployerBenefitAmount4",
        },
        {
            "enumValue": {"domainName": "FrequencyEforms", "instanceValue": "Per Month"},
            "name": "V2OtherIncomeNonEmployerBenefitFrequency4",
        },
        {
            "enumValue": {
                "domainName": "WageReplacementType2",
                "instanceValue": "Disability benefits under a governmental retirement plan such as STRS or PERS",
            },
            "name": "V2OtherIncomeNonEmployerBenefitWRT4",
        },
        {
            "enumValue": {"domainName": "YesNoI'veApplied", "instanceValue": "Yes"},
            "name": "V2ReceiveWageReplacement10",
        },
        {
            "dateValue": incomes[4].income_start_date.isoformat(),
            "name": "V2OtherIncomeNonEmployerBenefitStartDate5",
        },
        {
            "dateValue": incomes[4].income_end_date.isoformat(),
            "name": "V2OtherIncomeNonEmployerBenefitEndDate5",
        },
        {
            "decimalValue": incomes[4].income_amount_dollars,
            "name": "V2OtherIncomeNonEmployerBenefitAmount5",
        },
        {
            "enumValue": {"domainName": "FrequencyEforms", "instanceValue": "Per Month"},
            "name": "V2OtherIncomeNonEmployerBenefitFrequency5",
        },
        {
            "enumValue": {
                "domainName": "WageReplacementType2",
                "instanceValue": "Jones Act benefits",
            },
            "name": "V2OtherIncomeNonEmployerBenefitWRT5",
        },
        {
            "enumValue": {"domainName": "YesNoI'veApplied", "instanceValue": "Yes"},
            "name": "V2ReceiveWageReplacement11",
        },
        {
            "dateValue": incomes[5].income_start_date.isoformat(),
            "name": "V2OtherIncomeNonEmployerBenefitStartDate6",
        },
        {
            "dateValue": incomes[5].income_end_date.isoformat(),
            "name": "V2OtherIncomeNonEmployerBenefitEndDate6",
        },
        {
            "decimalValue": incomes[5].income_amount_dollars,
            "name": "V2OtherIncomeNonEmployerBenefitAmount6",
        },
        {
            "enumValue": {"domainName": "FrequencyEforms", "instanceValue": "Per Month"},
            "name": "V2OtherIncomeNonEmployerBenefitFrequency6",
        },
        {
            "enumValue": {
                "domainName": "WageReplacementType2",
                "instanceValue": "Railroad Retirement benefits",
            },
            "name": "V2OtherIncomeNonEmployerBenefitWRT6",
        },
        {
            "enumValue": {"domainName": "YesNoI'veApplied", "instanceValue": "Yes"},
            "name": "V2ReceiveWageReplacement12",
        },
        {
            "dateValue": incomes[6].income_start_date.isoformat(),
            "name": "V2OtherIncomeNonEmployerBenefitStartDate7",
        },
        {
            "dateValue": incomes[6].income_end_date.isoformat(),
            "name": "V2OtherIncomeNonEmployerBenefitEndDate7",
        },
        {
            "decimalValue": incomes[6].income_amount_dollars,
            "name": "V2OtherIncomeNonEmployerBenefitAmount7",
        },
        {
            "enumValue": {"domainName": "FrequencyEforms", "instanceValue": "Per Month"},
            "name": "V2OtherIncomeNonEmployerBenefitFrequency7",
        },
        {
            "enumValue": {
                "domainName": "WageReplacementType2",
                "instanceValue": "Earnings from another employer or through self-employment",
            },
            "name": "V2OtherIncomeNonEmployerBenefitWRT7",
        },
        {
            "enumValue": {"domainName": "YesNoI'veApplied", "instanceValue": "Yes"},
            "name": "V2ReceiveWageReplacement13",
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
