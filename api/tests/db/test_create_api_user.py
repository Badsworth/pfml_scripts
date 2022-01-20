import pydantic
import pytest

from massgov.pfml.db.create_api_user import FineosUserConfig, SnowUserConfig, create_user_helper
from massgov.pfml.db.models.employees import Role, User
from massgov.pfml.db.models.factories import UserFactory


def test_create_user_helper(test_db_session, monkeypatch):
    monkeypatch.setenv("COGNITO_FINEOS_APP_CLIENT_ID", "123abc")
    monkeypatch.setenv("COGNITO_INTERNAL_FINEOS_ROLE_APP_CLIENT_ID", "456def")
    role_id = Role.FINEOS.role_id
    fineos_config = FineosUserConfig()
    create_user_helper(test_db_session, fineos_config, role_id)

    fineos_user = test_db_session.query(User).filter_by(sub_id="123abc").one()
    assert fineos_user is not None
    assert len(fineos_user.roles) == 1
    assert fineos_user.roles[0].role_id == Role.FINEOS.role_id

    internal_user = test_db_session.query(User).filter_by(sub_id="456def").one()
    assert internal_user is not None
    assert len(internal_user.roles) == 1
    assert internal_user.roles[0].role_id == Role.FINEOS.role_id

    monkeypatch.setenv("COGNITO_SERVICENOW_APP_CLIENT_ID", "999rst")
    monkeypatch.setenv("COGNITO_INTERNAL_SERVICENOW_ROLE_APP_CLIENT_ID", "789ghi")
    role_id = Role.PFML_CRM.role_id
    snow_config = SnowUserConfig()
    create_user_helper(test_db_session, snow_config, role_id)

    snow_user = test_db_session.query(User).filter_by(sub_id="999rst").one()
    assert snow_user is not None
    assert len(snow_user.roles) == 1
    assert snow_user.roles[0].role_id == Role.PFML_CRM.role_id

    snow_internal_user = test_db_session.query(User).filter_by(sub_id="789ghi").one()
    assert snow_internal_user is not None
    assert len(snow_internal_user.roles) == 1
    assert snow_internal_user.roles[0].role_id == Role.PFML_CRM.role_id


def test_create_user_helper_exception(test_db_session, monkeypatch):
    monkeypatch.delenv("COGNITO_FINEOS_APP_CLIENT_ID", raising=False)
    monkeypatch.delenv("COGNITO_INTERNAL_FINEOS_ROLE_APP_CLIENT_ID", raising=False)

    with pytest.raises(pydantic.ValidationError):
        role_id = Role.FINEOS.role_id
        fineos_config = FineosUserConfig()
        create_user_helper(test_db_session, fineos_config, role_id)

    monkeypatch.delenv("COGNITO_SERVICENOW_APP_CLIENT_ID", raising=False)
    monkeypatch.delenv("COGNITO_INTERNAL_SERVICENOW_ROLE_APP_CLIENT_ID", raising=False)

    with pytest.raises(pydantic.ValidationError):
        role_id = Role.PFML_CRM.role_id
        snow_config = SnowUserConfig()
        create_user_helper(test_db_session, snow_config, role_id)


def test_create_user_helper_existing_user(
    test_db_session, monkeypatch, initialize_factories_session
):
    existing_fineos_user = UserFactory.create()

    monkeypatch.setenv("COGNITO_FINEOS_APP_CLIENT_ID", existing_fineos_user.sub_id)
    monkeypatch.setenv("COGNITO_INTERNAL_FINEOS_ROLE_APP_CLIENT_ID", "456def")
    role_id = Role.FINEOS.role_id
    fineos_config = FineosUserConfig()
    create_user_helper(test_db_session, fineos_config, role_id)

    fineos_user = test_db_session.query(User).filter_by(sub_id=existing_fineos_user.sub_id).one()
    assert fineos_user is not None
    assert len(fineos_user.roles) == 0

    existing_snow_user = UserFactory.create()

    monkeypatch.setenv("COGNITO_SERVICENOW_APP_CLIENT_ID", existing_snow_user.sub_id)
    monkeypatch.setenv("COGNITO_INTERNAL_SERVICENOW_ROLE_APP_CLIENT_ID", "789ghi")
    role_id = Role.PFML_CRM.role_id
    snow_config = SnowUserConfig()
    create_user_helper(test_db_session, snow_config, role_id)

    snow_user = test_db_session.query(User).filter_by(sub_id=existing_snow_user.sub_id).one()
    assert snow_user is not None
    assert len(snow_user.roles) == 0
