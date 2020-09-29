import pydantic
import pytest

from massgov.pfml.db.create_api_user import create_fineos_user_helper
from massgov.pfml.db.models.employees import Role, User


def test_create_fineos_user_helper(test_db_session, monkeypatch):
    monkeypatch.setenv("COGNITO_FINEOS_APP_CLIENT_ID", "123abc")
    create_fineos_user_helper(test_db_session)

    test_user = test_db_session.query(User).filter_by(active_directory_id="123abc").first()
    assert test_user is not None
    assert len(test_user.roles) == 1
    assert test_user.roles[0].role_id == Role.FINEOS.role_id


def test_test_create_fineos_user_helper_exception(test_db_session, monkeypatch):
    monkeypatch.delenv("COGNITO_FINEOS_APP_CLIENT_ID", raising=False)

    with pytest.raises(pydantic.ValidationError):
        create_fineos_user_helper(test_db_session)
