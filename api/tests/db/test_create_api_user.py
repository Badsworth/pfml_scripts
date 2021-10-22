import pydantic
import pytest

from massgov.pfml.db.create_api_user import create_fineos_user_helper
from massgov.pfml.db.models.employees import Role, User
from massgov.pfml.db.models.factories import UserFactory


def test_create_fineos_user_helper(test_db_session, monkeypatch):
    monkeypatch.setenv("COGNITO_FINEOS_APP_CLIENT_ID", "123abc")
    monkeypatch.setenv("COGNITO_INTERNAL_FINEOS_ROLE_APP_CLIENT_ID", "456def")
    create_fineos_user_helper(test_db_session)

    fineos_user = test_db_session.query(User).filter_by(sub_id="123abc").one()
    assert fineos_user is not None
    assert len(fineos_user.roles) == 1
    assert fineos_user.roles[0].role_id == Role.FINEOS.role_id

    internal_user = test_db_session.query(User).filter_by(sub_id="456def").one()
    assert internal_user is not None
    assert len(internal_user.roles) == 1
    assert internal_user.roles[0].role_id == Role.FINEOS.role_id


def test_create_fineos_user_helper_exception(test_db_session, monkeypatch):
    monkeypatch.delenv("COGNITO_FINEOS_APP_CLIENT_ID", raising=False)
    monkeypatch.delenv("COGNITO_INTERNAL_FINEOS_ROLE_APP_CLIENT_ID", raising=False)

    with pytest.raises(pydantic.ValidationError):
        create_fineos_user_helper(test_db_session)


def test_create_fineos_user_helper_existing_user(
    test_db_session, monkeypatch, initialize_factories_session
):
    existing_user = UserFactory.create()

    monkeypatch.setenv("COGNITO_FINEOS_APP_CLIENT_ID", existing_user.sub_id)
    monkeypatch.setenv("COGNITO_INTERNAL_FINEOS_ROLE_APP_CLIENT_ID", "456def")

    create_fineos_user_helper(test_db_session)

    fineos_user = test_db_session.query(User).filter_by(sub_id=existing_user.sub_id).one()
    assert fineos_user is not None
    assert len(fineos_user.roles) == 0
