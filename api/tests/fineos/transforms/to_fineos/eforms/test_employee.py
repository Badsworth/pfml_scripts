import pytest

from massgov.pfml.db.models.factories import ApplicationFactory, PreviousLeaveFactory
from massgov.pfml.fineos.models.group_client_api import EFormAttribute, ModelEnum
from massgov.pfml.fineos.transforms.to_fineos.eforms.employee import (
    TransformPreviousLeave,
    TransformPreviousLeaves,
)


@pytest.fixture
def previous_leave():
    application = ApplicationFactory.create()
    return PreviousLeaveFactory.create(
        application_id=application.application_id, is_for_current_employer=True
    )


@pytest.fixture
def application():
    application = ApplicationFactory.create()
    application.previous_leaves = [
        PreviousLeaveFactory.create(
            application_id=application.application_id, is_for_current_employer=True
        ),
        PreviousLeaveFactory.create(
            application_id=application.application_id, is_for_current_employer=False
        ),
    ]
    return application


def test_transform_previous_leave(test_db_session, initialize_factories_session, previous_leave):
    result = TransformPreviousLeave.to_attributes(previous_leave)
    assert len(result) == 4
    start, end, reason, is_for_current_employer = result
    assert start.name == "BeginDate"
    assert start.dateValue == previous_leave.leave_start_date.isoformat()
    assert reason.enumValue.instanceValue == "Pregnancy / Maternity"
    assert is_for_current_employer.enumValue.instanceValue == "Yes"


def test_transform_previous_leaves(test_db_session, initialize_factories_session, application):
    leaves = application.previous_leaves
    eform_body = TransformPreviousLeaves.to_fineos(application)
    assert eform_body.eformType == "Other Leaves"
    assert len(eform_body.eformAttributes) == 10

    expected_attributes = [
        EFormAttribute(
            name="BeginDate1",
            booleanValue=None,
            dateValue=leaves[0].leave_start_date,
            decimalValue=None,
            integerValue=None,
            stringValue=None,
            enumValue=None,
        ),
        EFormAttribute(
            name="EndDate1",
            booleanValue=None,
            dateValue=leaves[0].leave_end_date,
            decimalValue=None,
            integerValue=None,
            stringValue=None,
            enumValue=None,
        ),
        EFormAttribute(
            name="QualifyingReason1",
            booleanValue=None,
            dateValue=None,
            decimalValue=None,
            integerValue=None,
            stringValue=None,
            enumValue=ModelEnum(
                domainName="QualifyingReasons", instanceValue="Pregnancy / Maternity"
            ),
        ),
        EFormAttribute(
            name="LeaveFromEmployer1",
            booleanValue=None,
            dateValue=None,
            decimalValue=None,
            integerValue=None,
            stringValue=None,
            enumValue=ModelEnum(domainName="YesNoUnknown", instanceValue="Yes"),
        ),
        EFormAttribute(
            name="Applies1",
            booleanValue=None,
            dateValue=None,
            decimalValue=None,
            integerValue=None,
            stringValue=None,
            enumValue=ModelEnum(domainName="PleaseSelectYesNoUnknown", instanceValue="Yes"),
        ),
        EFormAttribute(
            name="BeginDate2",
            booleanValue=None,
            dateValue=leaves[1].leave_start_date,
            decimalValue=None,
            integerValue=None,
            stringValue=None,
            enumValue=None,
        ),
        EFormAttribute(
            name="EndDate2",
            booleanValue=None,
            dateValue=leaves[1].leave_end_date,
            decimalValue=None,
            integerValue=None,
            stringValue=None,
            enumValue=None,
        ),
        EFormAttribute(
            name="QualifyingReason2",
            booleanValue=None,
            dateValue=None,
            decimalValue=None,
            integerValue=None,
            stringValue=None,
            enumValue=ModelEnum(
                domainName="QualifyingReasons", instanceValue="Pregnancy / Maternity"
            ),
        ),
        EFormAttribute(
            name="LeaveFromEmployer2",
            booleanValue=None,
            dateValue=None,
            decimalValue=None,
            integerValue=None,
            stringValue=None,
            enumValue=ModelEnum(domainName="YesNoUnknown", instanceValue="No"),
        ),
        EFormAttribute(
            name="Applies2",
            booleanValue=None,
            dateValue=None,
            decimalValue=None,
            integerValue=None,
            stringValue=None,
            enumValue=ModelEnum(domainName="PleaseSelectYesNoUnknown", instanceValue="Yes"),
        ),
    ]

    # required because the constructor coerces strings into date objects
    expected_attributes[0].dateValue = expected_attributes[0].dateValue.isoformat()
    expected_attributes[1].dateValue = expected_attributes[1].dateValue.isoformat()
    expected_attributes[5].dateValue = expected_attributes[5].dateValue.isoformat()
    expected_attributes[6].dateValue = expected_attributes[6].dateValue.isoformat()
    assert eform_body.eformAttributes == expected_attributes
