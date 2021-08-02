import json
import logging  # noqa: B1
import os

import pytest

from massgov.pfml.types import Fein

# every test in here requires real resources
pytestmark = pytest.mark.integration


@pytest.fixture
def event_json():
    with open(f"{os.path.dirname(__file__)}/../lambdas/cognito_pre_signup/test_event.json") as fp:
        event = fp.read()

    return event


@pytest.fixture
def event_dict(event_json):
    return json.loads(event_json)


def test_main_success_on_existing_fein_with_fineos_employer_id(
    caplog, test_db_session, event_dict, logging_fix
):
    from massgov.pfml.db.models.employees import Employer
    import massgov.pfml.cognito_pre_signup_lambda.main as main

    caplog.set_level(logging.INFO)  # noqa: B1
    employer = Employer(
        employer_fein=Fein("133701337"), employer_dba="Acme Corp", fineos_employer_id=93
    )

    test_db_session.add(employer)
    test_db_session.commit()

    main.db_session_raw = test_db_session

    response = main.handler(event_dict, {})

    expected_response = event_dict

    assert response == expected_response
    assert "Signup is for a leave administrator account" in caplog.text


def test_main_error_on_existing_fein_with_no_fineos(test_db_session, event_dict, logging_fix):
    from massgov.pfml.db.models.employees import Employer
    import massgov.pfml.cognito_pre_signup_lambda.main as main

    employer = Employer(employer_fein=Fein("133701337"), employer_dba="Acme Corp")

    test_db_session.add(employer)
    test_db_session.commit()

    main.db_session_raw = test_db_session

    with pytest.raises(Exception, match="Invalid employer details"):
        assert main.handler(event_dict, {})


def test_main_error_on_no_existing_fein(test_db_session, event_dict, logging_fix):
    import massgov.pfml.cognito_pre_signup_lambda.main as main

    main.db_session_raw = test_db_session

    with pytest.raises(Exception, match="No employer found with specified FEIN"):
        assert main.handler(event_dict, {})


def test_main_success_claimant(caplog, event_dict, logging_fix):
    import massgov.pfml.cognito_pre_signup_lambda.main as main

    caplog.set_level(logging.INFO)  # noqa: B1
    event_dict["request"]["clientMetadata"] = None

    response = main.handler(event_dict, {})
    expected_response = event_dict

    assert response == expected_response
    assert "Signup is for a claimant account" in caplog.text


def test_main_success_on_pfml_api_source(caplog, test_db_session, event_dict, logging_fix):
    import massgov.pfml.cognito_pre_signup_lambda.main as main

    caplog.set_level(logging.INFO)  # noqa: B1
    event_dict["request"]["clientMetadata"] = {"sign_up_source": "pfml_api"}

    response = main.handler(event_dict, {})
    expected_response = event_dict

    assert response == expected_response
    assert "Signup is from API" in caplog.text
    assert "Signup is for " not in caplog.text
