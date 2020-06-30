import pytest

import massgov.pfml.db.lookups as lookups
import massgov.pfml.db.models.applications as application_models


def test_by_value(test_db_session):
    # setup
    leave_reason = application_models.LeaveReasonQualifier(leave_reason_qualifier_description="Foo")
    test_db_session.add(leave_reason)
    test_db_session.commit()

    # test
    lookup_model = lookups.by_value(test_db_session, application_models.LeaveReasonQualifier, "Foo")

    assert lookup_model == leave_reason


def test_by_value_none(test_db_session):
    lookup_model = lookups.by_value(test_db_session, application_models.LeaveReasonQualifier, "Foo")

    assert lookup_model is None


def test_by_value_exception(test_db_session):
    # Application doesn't have a `_description` column
    with pytest.raises(AttributeError):
        lookups.by_value(test_db_session, application_models.Application, "Foo")
