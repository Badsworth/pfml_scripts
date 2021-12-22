from massgov.pfml.api.models.applications.common import LeaveReason
from massgov.pfml.api.models.common import MaskedPhone, PreviousLeaveQualifyingReason


def test_leave_reason_to_previous_leave_qualifying_reason():
    leave_reasons = [
        LeaveReason.pregnancy,
        LeaveReason.child_bonding,
        LeaveReason.serious_health_condition_employee,
        LeaveReason.caring_leave,
    ]
    expected_previous_leave_reasons = [
        PreviousLeaveQualifyingReason.PREGNANCY_MATERNITY,
        PreviousLeaveQualifyingReason.CHILD_BONDING,
        PreviousLeaveQualifyingReason.AN_ILLNESS_OR_INJURY,
        PreviousLeaveQualifyingReason.CARE_FOR_A_FAMILY_MEMBER,
    ]

    for index, leave_reason in enumerate(leave_reasons):
        assert (
            LeaveReason.to_previous_leave_qualifying_reason(leave_reason)
            == expected_previous_leave_reasons[index]
        )


def test_masked_phone_str_input():
    phone_str = "+15109283075"
    masked = MaskedPhone.from_orm(phone=phone_str)
    assert masked.int_code == "1"
    assert masked.phone_number == "***-***-3075"
