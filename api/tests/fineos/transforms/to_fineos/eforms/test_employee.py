import pytest

from massgov.pfml.api.models.common import PreviousLeave
from massgov.pfml.db.models.factories import ApplicationFactory, PreviousLeaveFactory
from massgov.pfml.fineos.transforms.to_fineos.eforms.employee import PreviousLeavesEFormBuilder

# every test in here requires real resources
pytestmark = pytest.mark.integration


def previous_leave():
    application = ApplicationFactory.create()
    leave = PreviousLeaveFactory.create(
        application_id=application.application_id, is_for_current_employer=True
    )
    return PreviousLeave.from_orm(leave)


def test_transform_previous_leaves(test_db_session, initialize_factories_session):
    leaves = [previous_leave(), previous_leave()]
    leaves[1].is_for_current_employer = False
    eform_body = PreviousLeavesEFormBuilder.build(leaves)
    assert eform_body.eformType == "Other Leaves"
    assert len(eform_body.eformAttributes) == 9
    expected_attributes = [
        {"dateValue": leaves[0].leave_start_date.isoformat(), "name": "BeginDate1"},
        {"dateValue": leaves[0].leave_end_date.isoformat(), "name": "EndDate1"},
        {
            "enumValue": {
                "domainName": "QualifyingReasons",
                "instanceValue": "Pregnancy / Maternity",
            },
            "name": "QualifyingReason1",
        },
        {
            "enumValue": {"domainName": "YesNoUnknown", "instanceValue": "Yes"},
            "name": "LeaveFromEmployer1",
        },
        {
            "enumValue": {"domainName": "PleaseSelectYesNoUnknown", "instanceValue": "Yes"},
            "name": "Applies1",
        },
        {"dateValue": leaves[1].leave_start_date.isoformat(), "name": "BeginDate2"},
        {"dateValue": leaves[1].leave_end_date.isoformat(), "name": "EndDate2"},
        {
            "enumValue": {
                "domainName": "QualifyingReasons",
                "instanceValue": "Pregnancy / Maternity",
            },
            "name": "QualifyingReason2",
        },
        {
            "enumValue": {"domainName": "YesNoUnknown", "instanceValue": "No"},
            "name": "LeaveFromEmployer2",
        },
    ]

    assert eform_body.eformAttributes == expected_attributes
