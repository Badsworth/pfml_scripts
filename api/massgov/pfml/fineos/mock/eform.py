#
# Mock EForms for use by MockFINEOSClient or in unit tests.
#

import datetime

from ..models.customer_api import EForm as CustomerEForm
from ..models.customer_api import EFormAttribute as CustomerEFormAttribute
from ..models.customer_api.spec import ModelEnum as CustomerModelEnum
from ..models.group_client_api import EForm, EFormAttribute, ModelEnum

# Retrieved from DT2 using
# fineos.get_eform_summary("PFML_LEAVE_ADMIN_95479384-CBE6-45F1-A8FB-27DC9824D880", "NTN-154476-ABS-01")
# fineos.get_eform("PFML_LEAVE_ADMIN_95479384-CBE6-45F1-A8FB-27DC9824D880", "NTN-154476-ABS-01", 211711)
# ...
MOCK_EFORM_OTHER_INCOME_V2 = EForm(
    eformId=211711,
    eformType="Other Income - current version",
    eformAttributes=[
        EFormAttribute(
            name="V2OtherIncomeNonEmployerBenefitWRT1",
            enumValue=ModelEnum(
                domainName="WageReplacementType2",
                instanceValue="Earnings from another employer or through self-employment",
            ),
        ),
        EFormAttribute(name="V2Spacer1", stringValue=""),
        EFormAttribute(
            name="V2ReceiveWageReplacement7",
            enumValue=ModelEnum(domainName="PleaseSelectYesNo", instanceValue="Yes"),
        ),
        EFormAttribute(name="Spacer11", stringValue=""),
        EFormAttribute(
            name="V2ReceiveWageReplacement8",
            enumValue=ModelEnum(domainName="PleaseSelectYesNo", instanceValue="Please Select"),
        ),
        EFormAttribute(
            name="V2SalaryContinuation1",
            enumValue=ModelEnum(domainName="PleaseSelectYesNo", instanceValue="No"),
        ),
        EFormAttribute(name="V2Spacer3", stringValue=""),
        EFormAttribute(name="V2Spacer2", stringValue=""),
        EFormAttribute(name="V2Spacer5", stringValue=""),
        EFormAttribute(name="V2Spacer4", stringValue=""),
        EFormAttribute(name="V2Spacer7", stringValue=""),
        EFormAttribute(name="V2Spacer6", stringValue=""),
        EFormAttribute(name="V2Header1", stringValue="Employer-Sponsored Benefits"),
        EFormAttribute(name="V2Spacer9", stringValue=""),
        EFormAttribute(name="V2Header2", stringValue="Income from Other Sources"),
        EFormAttribute(name="V2Spacer8", stringValue=""),
        EFormAttribute(
            name="V2ReceiveWageReplacement1",
            enumValue=ModelEnum(domainName="PleaseSelectYesNo", instanceValue="Yes"),
        ),
        EFormAttribute(
            name="V2ReceiveWageReplacement2",
            enumValue=ModelEnum(domainName="PleaseSelectYesNo", instanceValue="Please Select"),
        ),
        EFormAttribute(
            name="V2Examples7",
            stringValue="Workers Compensation, Unemployment Insurance, Social Security "
            "Disability Insurance, Disability benefits under a governmental "
            "retirement plan such as STRS or PERS, Jones Act benefits, Railroad "
            "Retirement benefit, Earnings from another employer or through "
            "self-employment",
        ),
        EFormAttribute(
            name="V2OtherIncomeNonEmployerBenefitStartDate1", dateValue=datetime.date(2021, 11, 7)
        ),
        EFormAttribute(
            name="V2WRT1",
            enumValue=ModelEnum(
                domainName="WageReplacementType",
                instanceValue="Temporary disability insurance (Long- or Short-term)",
            ),
        ),
        EFormAttribute(
            name="V2Frequency1",
            enumValue=ModelEnum(domainName="FrequencyEforms", instanceValue="Per Week"),
        ),
        EFormAttribute(
            name="V2OtherIncomeNonEmployerBenefitEndDate1", dateValue=datetime.date(2021, 12, 19)
        ),
        EFormAttribute(name="V2StartDate1", dateValue=datetime.date(2021, 11, 7)),
        EFormAttribute(name="V2EndDate1", dateValue=datetime.date(2021, 12, 19)),
        EFormAttribute(name="V2Amount1", decimalValue=100.0),
        EFormAttribute(name="V2OtherIncomeNonEmployerBenefitAmount1", decimalValue=200.0),
        EFormAttribute(name="V2Spacer10", stringValue=""),
        EFormAttribute(
            name="V2OtherIncomeNonEmployerBenefitFrequency1",
            enumValue=ModelEnum(domainName="FrequencyEforms", instanceValue="Per Week"),
        ),
    ],
)

MOCK_EFORM_OTHER_LEAVES = EForm(
    eformId=211713,
    eformType="Other Leaves - current version",
    eformAttributes=[
        EFormAttribute(name="V2Spacer1", stringValue=""),
        EFormAttribute(name="V2Spacer5", stringValue=""),
        EFormAttribute(name="V2Spacer4", stringValue=""),
        EFormAttribute(name="V2Spacer7", stringValue=""),
        EFormAttribute(name="V2Spacer6", stringValue=""),
        EFormAttribute(name="V2Spacer9", stringValue=""),
        EFormAttribute(
            name="V2AccruedPLEmployer1",
            enumValue=ModelEnum(domainName="PleaseSelectYesNo", instanceValue="Yes"),
        ),
        EFormAttribute(name="V2Spacer8", stringValue=""),
        EFormAttribute(name="V2TotalHours1", integerValue=40),
        EFormAttribute(name="V2AccruedEndDate1", dateValue=datetime.date(2021, 12, 19)),
        EFormAttribute(
            name="V2Leave1", enumValue=ModelEnum(domainName="PleaseSelectYesNo", instanceValue="No")
        ),
        EFormAttribute(
            name="V2MinutesWorked1",
            enumValue=ModelEnum(domainName="15MinuteIncrements", instanceValue="00"),
        ),
        EFormAttribute(
            name="V2AccruedReasons",
            stringValue="This includes vacation time, sick time, personal time. Reminder: you "
            "can use accrued paid leave for the 7-day waiting period with no "
            "impact to your PFML benefit.\n\nThe following are qualifying reasons "
            "for taking paid or unpaid leave: \n\nYou had a serious health "
            "condition, including illness, injury, or pregnancy. If you were "
            "sick, you were out of work for at least 3 days and needed continuing "
            "care from your health care provider or needed inpatient care. "
            "\n\nYou bonded with your child after birth or placement. \n\nYou "
            "needed to manage family affairs while a family member is on active "
            "duty in the armed forces. \n\nYou needed to care for a family member "
            "who serves in the armed forces. \n\nYou needed to care for a family "
            "member with a serious health condition.",
        ),
        EFormAttribute(
            name="V2AccruedPaidLeave1",
            enumValue=ModelEnum(domainName="PleaseSelectYesNo", instanceValue="Yes"),
        ),
        EFormAttribute(
            name="V2LeaveFromEmployer1",
            enumValue=ModelEnum(domainName="PleaseSelectYesNo", instanceValue="Yes"),
        ),
        EFormAttribute(name="V2Header1", stringValue="Previous leaves"),
        EFormAttribute(name="V2Header2", stringValue="Employer-sponsored Accrued Paid Leave"),
        EFormAttribute(
            name="V2OtherLeavesPastLeaveEndDate1", dateValue=datetime.date(2021, 10, 24)
        ),
        EFormAttribute(
            name="V2TotalMinutes1",
            enumValue=ModelEnum(domainName="15MinuteIncrements", instanceValue="00"),
        ),
        EFormAttribute(
            name="V2QualifyingReason1",
            enumValue=ModelEnum(
                domainName="QualifyingReasons",
                instanceValue="Bonding with my child after birth or placement",
            ),
        ),
        EFormAttribute(
            name="V2Applies1",
            enumValue=ModelEnum(domainName="PleaseSelectYesNo", instanceValue="Yes"),
        ),
        EFormAttribute(
            name="V2Applies2",
            enumValue=ModelEnum(domainName="PleaseSelectYesNo", instanceValue="Please Select"),
        ),
        EFormAttribute(
            name="V2OtherLeavesPastLeaveStartDate1", dateValue=datetime.date(2021, 9, 12)
        ),
        EFormAttribute(name="V2HoursWorked1", integerValue=20),
        EFormAttribute(name="V2Spacer10", stringValue=""),
        EFormAttribute(
            name="V2Reasons",
            stringValue="You had a serious health condition, including illness, injury, "
            "or pregnancy. If you were sick, you were out of work for at least 3 "
            "days and needed continuing care from your health care provider or "
            "needed inpatient care. \n\nYou bonded with your child after birth or "
            "placement. \n\nYou needed to manage family affairs while a family "
            "member is on active duty in the armed forces. \n\nYou needed to care "
            "for a family member who serves in the armed forces. \n\nYou needed "
            "to care for a family member with a serious health condition.",
        ),
        EFormAttribute(name="V2AccruedStartDate1", dateValue=datetime.date(2021, 11, 7)),
    ],
)

MOCK_CUSTOMER_EFORM_OTHER_LEAVES = CustomerEForm(
    eformId=211714,
    eformType="Other Leaves - current version",
    eformAttributes=[
        CustomerEFormAttribute(name="V2Spacer1", stringValue=""),
        CustomerEFormAttribute(name="V2Spacer5", stringValue=""),
        CustomerEFormAttribute(name="V2Spacer4", stringValue=""),
        CustomerEFormAttribute(name="V2Spacer7", stringValue=""),
        CustomerEFormAttribute(name="V2Spacer6", stringValue=""),
        CustomerEFormAttribute(name="V2Spacer9", stringValue=""),
        CustomerEFormAttribute(
            name="V2AccruedPLEmployer1",
            enumValue=CustomerModelEnum(domainName="PleaseSelectYesNo", instanceValue="Yes"),
        ),
        CustomerEFormAttribute(name="V2Spacer8", stringValue=""),
        CustomerEFormAttribute(name="V2TotalHours1", integerValue=40),
        CustomerEFormAttribute(name="V2AccruedEndDate1", dateValue=datetime.date(2021, 12, 19)),
        CustomerEFormAttribute(
            name="V2Leave1",
            enumValue=CustomerModelEnum(domainName="PleaseSelectYesNo", instanceValue="No"),
        ),
        CustomerEFormAttribute(
            name="V2MinutesWorked1",
            enumValue=CustomerModelEnum(domainName="15MinuteIncrements", instanceValue="45"),
        ),
        CustomerEFormAttribute(
            name="V2AccruedReasons",
            stringValue="This includes vacation time, sick time, personal time. Reminder: you "
            "can use accrued paid leave for the 7-day waiting period with no "
            "impact to your PFML benefit.\n\nThe following are qualifying reasons "
            "for taking paid or unpaid leave: \n\nYou had a serious health "
            "condition, including illness, injury, or pregnancy. If you were "
            "sick, you were out of work for at least 3 days and needed continuing "
            "care from your health care provider or needed inpatient care. "
            "\n\nYou bonded with your child after birth or placement. \n\nYou "
            "needed to manage family affairs while a family member is on active "
            "duty in the armed forces. \n\nYou needed to care for a family member "
            "who serves in the armed forces. \n\nYou needed to care for a family "
            "member with a serious health condition.",
        ),
        CustomerEFormAttribute(
            name="V2AccruedPaidLeave1",
            enumValue=CustomerModelEnum(domainName="PleaseSelectYesNo", instanceValue="Yes"),
        ),
        CustomerEFormAttribute(
            name="V2LeaveFromEmployer1",
            enumValue=CustomerModelEnum(domainName="PleaseSelectYesNo", instanceValue="Yes"),
        ),
        CustomerEFormAttribute(name="V2Header1", stringValue="Previous leaves"),
        CustomerEFormAttribute(
            name="V2Header2", stringValue="Employer-sponsored Accrued Paid Leave"
        ),
        CustomerEFormAttribute(
            name="V2OtherLeavesPastLeaveEndDate1", dateValue=datetime.date(2021, 10, 24)
        ),
        CustomerEFormAttribute(
            name="V2TotalMinutes1",
            enumValue=CustomerModelEnum(
                domainName="15MinuteIncrements", instanceValue="Please Select"
            ),
        ),
        CustomerEFormAttribute(
            name="V2QualifyingReason1",
            enumValue=CustomerModelEnum(
                domainName="QualifyingReasons",
                instanceValue="Bonding with my child after birth or placement",
            ),
        ),
        CustomerEFormAttribute(
            name="V2Applies1",
            enumValue=CustomerModelEnum(domainName="PleaseSelectYesNo", instanceValue="Yes"),
        ),
        CustomerEFormAttribute(
            name="V2Applies2",
            enumValue=CustomerModelEnum(
                domainName="PleaseSelectYesNo", instanceValue="Please Select"
            ),
        ),
        CustomerEFormAttribute(
            name="V2OtherLeavesPastLeaveStartDate1", dateValue=datetime.date(2021, 9, 12)
        ),
        CustomerEFormAttribute(name="V2HoursWorked1", integerValue=20),
        CustomerEFormAttribute(name="V2Spacer10", stringValue=""),
        CustomerEFormAttribute(
            name="V2Reasons",
            stringValue="You had a serious health condition, including illness, injury, "
            "or pregnancy. If you were sick, you were out of work for at least 3 "
            "days and needed continuing care from your health care provider or "
            "needed inpatient care. \n\nYou bonded with your child after birth or "
            "placement. \n\nYou needed to manage family affairs while a family "
            "member is on active duty in the armed forces. \n\nYou needed to care "
            "for a family member who serves in the armed forces. \n\nYou needed "
            "to care for a family member with a serious health condition.",
        ),
        CustomerEFormAttribute(name="V2AccruedStartDate1", dateValue=datetime.date(2021, 11, 7)),
    ],
)

MOCK_EFORM_EMPLOYER_RESPONSE_V2 = EForm(
    eformId=211721,
    eformType="Employer Response to Leave Request - current version",
    eformAttributes=[
        EFormAttribute(name="V2Amount1", decimalValue=100.0),
        EFormAttribute(
            name="V2Frequency1",
            enumValue=ModelEnum(domainName="FrequencyEforms", instanceValue="Per Week"),
        ),
        EFormAttribute(name="V2EmployerBenefitStartDate1", dateValue=datetime.date(2021, 11, 7)),
        EFormAttribute(name="V2EmployerBenefitEndDate1", dateValue=datetime.date(2021, 12, 19)),
        EFormAttribute(
            name="V2ERBenefitType1",
            enumValue=ModelEnum(
                domainName="WageReplacementType",
                instanceValue="Temporary disability insurance (Long- or Short-term)",
            ),
        ),
        EFormAttribute(
            name="V2SalaryCont1",
            enumValue=ModelEnum(domainName="PleaseSelectYesNo", instanceValue="No"),
        ),
        EFormAttribute(
            name="V2ReceiveWageReplacement1",
            enumValue=ModelEnum(domainName="PleaseSelectYesNo", instanceValue="Yes"),
        ),
        EFormAttribute(name="V2PastLeaveStartDate1", dateValue=datetime.date(2021, 9, 12)),
        EFormAttribute(name="V2PastLeaveEndDate1", dateValue=datetime.date(2021, 10, 24)),
        EFormAttribute(
            name="V2NatureOfLeave1",
            enumValue=ModelEnum(
                domainName="Nature of leave",
                instanceValue="Bonding with my child after birth or placement",
            ),
        ),
        EFormAttribute(
            name="V2PastLeaveSame1",
            enumValue=ModelEnum(domainName="PleaseSelectYesNo", instanceValue="No"),
        ),
        EFormAttribute(
            name="V2Applies1",
            enumValue=ModelEnum(domainName="PleaseSelectYesNo", instanceValue="Yes"),
        ),
        EFormAttribute(
            name="V2Comment",
            stringValue="This is a generic explanation of the leave admin's response.",
        ),
        EFormAttribute(name="V2AverageWeeklyHoursWorked", decimalValue=40.0),
        EFormAttribute(name="V2EmployerDecision", stringValue="Deny"),
        EFormAttribute(name="Fraud1", stringValue="No"),
        EFormAttribute(
            name="V2NatureOfLeave",
            enumValue=ModelEnum(domainName="Nature of leave", instanceValue="An illness or injury"),
        ),
        EFormAttribute(name="V2AccruedStartDate", dateValue=datetime.date(2021, 11, 7)),
        EFormAttribute(name="V2AccruedEndDate", dateValue=datetime.date(2021, 12, 19)),
        EFormAttribute(
            name="V2AccruedPaidLeave",
            enumValue=ModelEnum(domainName="PleaseSelectYesNo", instanceValue="Yes"),
        ),
    ],
)

MOCK_EFORM_OTHER_INCOME_V1 = EForm(
    eformId=27701,
    eformType="Other Income",
    eformAttributes=[
        EFormAttribute(name="StartDate", dateValue=datetime.date(2021, 5, 3)),
        EFormAttribute(name="Frequency2", stringValue="Per Week"),
        EFormAttribute(
            name="ProgramType",
            enumValue=ModelEnum(domainName="Program Type", instanceValue="Employer"),
        ),
        EFormAttribute(name="Spacer4", stringValue=""),
        EFormAttribute(
            name="ProgramType2",
            enumValue=ModelEnum(domainName="Program Type", instanceValue="Non-Employer"),
        ),
        EFormAttribute(
            name="ReceiveWageReplacement",
            enumValue=ModelEnum(domainName="YesNoI'veApplied", instanceValue="Yes"),
        ),
        EFormAttribute(name="StartDate2", dateValue=datetime.date(2021, 5, 5)),
        EFormAttribute(name="Spacer1", stringValue=""),
        EFormAttribute(name="Spacer3", stringValue=""),
        EFormAttribute(name="Spacer2", stringValue=""),
        EFormAttribute(name="Spacer", stringValue=""),
        EFormAttribute(
            name="WRT1",
            enumValue=ModelEnum(
                domainName="WageReplacementType", instanceValue="Permanent disability insurance"
            ),
        ),
        EFormAttribute(
            name="WRT2",
            enumValue=ModelEnum(domainName="WageReplacementType2", instanceValue="Please Select"),
        ),
        EFormAttribute(
            name="WRT3",
            enumValue=ModelEnum(domainName="WageReplacementType", instanceValue="Please Select"),
        ),
        EFormAttribute(
            name="WRT4",
            enumValue=ModelEnum(domainName="WageReplacementType2", instanceValue="SSDI"),
        ),
        EFormAttribute(name="EndDate2", dateValue=datetime.date(2021, 5, 29)),
        EFormAttribute(name="Amount", decimalValue=500.0),
        EFormAttribute(name="EndDate", dateValue=datetime.date(2021, 5, 29)),
        EFormAttribute(name="Amount2", decimalValue=500.0),
        EFormAttribute(
            name="ReceiveWageReplacement3",
            enumValue=ModelEnum(domainName="YesNoI'veApplied", instanceValue="Please Select"),
        ),
        EFormAttribute(name="Frequency", stringValue="Per Week"),
        EFormAttribute(
            name="ReceiveWageReplacement2",
            enumValue=ModelEnum(domainName="YesNoI'veApplied", instanceValue="Yes"),
        ),
    ],
)

MOCK_EFORMS = (MOCK_EFORM_OTHER_INCOME_V2, MOCK_EFORM_OTHER_LEAVES, MOCK_EFORM_EMPLOYER_RESPONSE_V2)

MOCK_CUSTOMER_EFORMS = (MOCK_CUSTOMER_EFORM_OTHER_LEAVES,)
