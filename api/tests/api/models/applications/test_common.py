import pytest

from massgov.pfml.api.models.applications.common import LeaveReason
from massgov.pfml.api.models.common import MaskedPhoneResponse, Phone, PreviousLeaveQualifyingReason
from massgov.pfml.api.validation.exceptions import ValidationException


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
    masked = MaskedPhoneResponse.from_orm(phone=phone_str)
    assert masked.int_code == "1"
    assert masked.phone_number == "***-***-3075"


def test_phone_str_input_matches_e164():
    phone_str = "224-705-2345"
    phone = Phone(phone_number=phone_str)
    assert phone.e164 == "+12247052345"

    phone_str = "510-928-3075"
    phone = Phone(phone_number=phone_str, int_code="1")
    assert phone.e164 == "+15109283075"


def test_phone_str_input_does_not_match_e164():
    phone_str = "510-928-3075"
    wrong_e164 = "+15109283076"

    with pytest.raises(ValidationException):
        Phone(phone_number=phone_str, e164=wrong_e164)
