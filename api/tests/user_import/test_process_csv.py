import logging  # noqa: B1
import re
import uuid
from pathlib import Path

import pytest
from botocore.exceptions import ClientError

import massgov.pfml.cognito_post_confirmation_lambda.lib as lib
from massgov.pfml import fineos
from massgov.pfml.db.models.employees import Employer, Role, User, UserLeaveAdministrator, UserRole
from massgov.pfml.user_import.process_csv import (
    clean_fein,
    log_progress,
    pivot_csv_file,
    process_by_email,
    process_files,
)


class MockCognito:
    def __init__(self):
        self._memo = dict()

    def admin_create_user(self, *args, UserPoolId="", **kwargs):
        sub = str(uuid.uuid4())
        self._memo[kwargs["Username"]] = sub
        return {"User": {"Attributes": [{"Name": "sub", "Value": sub}]}}

    def admin_set_user_password(self, *args, **kwargs):
        pass

    def list_users(self, *args, UserPoolId="", Filter="", **kwargs):
        email = re.match(r'email="(.*?)"', Filter).group(1)
        sub = self._memo.get(email)
        if sub:
            return {"Users": [{"Attributes": [{"Name": "sub", "Value": sub}]}]}
        return {"Users": []}


class MockCognitoPasswordError(MockCognito):
    def admin_set_user_password(self, *args, **kwargs):
        raise ClientError(
            {"Error": {"Code": "UserNotFoundException", "Message": "That thar user don't exist"}},
            {...},
        )


class MockCognitoListRateLimit(MockCognito):
    def __init__(self):
        self._retries = 0
        super().__init__()

    def list_users(self, *args, UserPoolId="", Filter="", **kwargs):
        self._retries += 1
        if (self._retries % 2) == 0:
            raise ClientError(
                {
                    "Error": {
                        "Code": "TooManyRequestsException",
                        "Message": "You are doing it too loud",
                    }
                },
                {...},
            )
        else:
            return super().list_users(*args, UserPoolId=UserPoolId, Filter=Filter, **kwargs)


@pytest.fixture
def mock_bogus_fineos():
    def mock_create_or_update_leave_admin(
        leave_admin_create_or_update: fineos.models.CreateOrUpdateLeaveAdmin,
    ) -> None:
        raise fineos.FINEOSClientError("OHNO")

    mock_fineos = fineos.create_client()
    mock_fineos.create_or_update_leave_admin = mock_create_or_update_leave_admin
    return mock_fineos


@pytest.fixture
def test_file_location():
    return Path(__file__).parent / "test_users1.csv"


@pytest.fixture
def create_employers(test_db_session):
    test_db_session.add(
        Employer(employer_fein="847847847", employer_dba="Wayne Enterprises", fineos_employer_id=1)
    )
    test_db_session.add(
        Employer(employer_fein="111111111", employer_dba="BogoCorp Ltd", fineos_employer_id=2)
    )
    test_db_session.add(
        Employer(
            employer_fein="222222222",
            employer_dba="Charles Entertainment Cheese",
            fineos_employer_id=3,
        )
    )
    test_db_session.add(
        Employer(employer_fein="114444444", employer_dba="Dunkin", fineos_employer_id=4)
    )
    test_db_session.commit()


class TestProcessCSV:
    """ Tests for helper functions within process_csv """

    def test_pivot_csv(self, test_file_location):
        pivoted = pivot_csv_file(test_file_location)
        assert len(pivoted) == 3
        assert sum(len(x) for x in pivoted.values()) == 5
        assert len(pivoted["test_user@gmail.com"]) == 2

    def test_log_progress(self, caplog):
        caplog.set_level(logging.INFO)  # noqa: B1
        last_updated = 0
        for x in range(0, 100):
            last_updated = log_progress(
                processed=x, total=100, last_updated=last_updated, update_every=10
            )
        assert len(caplog.records) == 9
        processed = 10
        for record in caplog.records:
            assert record.getMessage() == f"processed {processed} out of 100 imports"
            processed += 10

    def test_clean_fein_dash(self):
        cleaned = clean_fein("11-1111111")
        assert cleaned == "111111111"

    def test_clean_fein_zerofill(self):
        cleaned = clean_fein("1234567")
        assert cleaned == "001234567"


class TestProcessByEmail:
    """ Tests for processing pivoted data into users """

    def test_process_by_email(self, test_file_location, test_db_session, create_employers):
        fineos_client = fineos.create_client()
        cognito_client = MockCognito()
        pivoted = pivot_csv_file(test_file_location)
        processed = 0
        for email, employers in pivoted.items():
            processed += process_by_email(
                email=email,
                input_data=employers,
                db_session=test_db_session,
                cognito_pool_id="fake_pool",
                cognito_client=cognito_client,
                fineos_client=fineos_client,
            )
        # 5 records in this file
        assert processed == 5
        # Should have created 3 cognito users
        assert len(cognito_client._memo) == 3
        # Ensure all emails in pivoted file were created in cognito
        assert set(cognito_client._memo.keys()) == set(pivoted.keys())

        # Ensure ALL changes are committed by the process_by_email flow with intentional rollback
        test_db_session.rollback()
        users_created = test_db_session.query(User).all()
        assert len(users_created) == 3
        user_roles_created = test_db_session.query(UserRole).all()
        assert len(user_roles_created) == 3
        for user_role in user_roles_created:
            assert user_role.role_id == Role.EMPLOYER.role_id

        user_leave_admins = test_db_session.query(UserLeaveAdministrator).all()
        assert len(user_leave_admins) == 5
        for user_leave_admin in user_leave_admins:
            assert user_leave_admin.fineos_web_id is not None

    def test_process_by_email_bad_fineos(
        self, test_file_location, test_db_session, create_employers, mock_bogus_fineos, caplog
    ):
        cognito_client = MockCognito()
        pivoted = pivot_csv_file(test_file_location)
        processed = 0
        for email, employers in pivoted.items():
            processed += process_by_email(
                email=email,
                input_data=employers,
                db_session=test_db_session,
                cognito_pool_id="fake_pool",
                filename=test_file_location,
                cognito_client=cognito_client,
                fineos_client=mock_bogus_fineos,
            )
        # 5 records in this file
        assert processed == 0
        count_error_in_fineos = 0
        count_unable_to_complete_reg = 0
        for record in caplog.records:
            if "Unable to complete registration" in record.getMessage():
                count_unable_to_complete_reg += 1
            elif "Received an error processing FINEOS registration" in record.getMessage():
                count_error_in_fineos += 1
        assert count_unable_to_complete_reg == 5
        assert count_error_in_fineos == count_unable_to_complete_reg * 3  # 3 retries

    def test_process_by_email_bad_set_password(
        self, test_file_location, test_db_session, create_employers, mock_bogus_fineos, caplog
    ):
        cognito_client = MockCognitoPasswordError()
        pivoted = pivot_csv_file(test_file_location)
        processed = 0
        for email, employers in pivoted.items():
            processed += process_by_email(
                email=email,
                input_data=employers,
                db_session=test_db_session,
                cognito_pool_id="fake_pool",
                filename=test_file_location,
                cognito_client=cognito_client,
                fineos_client=mock_bogus_fineos,
            )
        # 5 records in this file
        assert processed == 0
        count_error_in_cognito = 0
        for record in caplog.records:
            if "Unable to set Cognito password for user" in record.getMessage():
                count_error_in_cognito += 1

        #  Only 3 emails in the file
        assert count_error_in_cognito == 3

    def test_process_by_email_flaky_list_users(
        self, test_file_location, test_db_session, create_employers, caplog
    ):
        caplog.set_level(logging.INFO)  # noqa: B1
        cognito_client = MockCognitoListRateLimit()
        pivoted = pivot_csv_file(test_file_location)
        processed = 0
        for email, employers in pivoted.items():
            processed += process_by_email(
                email=email,
                input_data=employers,
                db_session=test_db_session,
                cognito_pool_id="fake_pool",
                filename=test_file_location,
                cognito_client=cognito_client,
            )
        # 5 records in this file
        assert processed == 5
        count_error_in_cognito_list_users = 0
        for record in caplog.records:
            if "Too many requests error from Cognito" in record.getMessage():
                count_error_in_cognito_list_users += 1

        assert count_error_in_cognito_list_users == 4

    def test_process_files(self, test_file_location, test_db_session, create_employers, caplog):
        caplog.set_level(logging.INFO)  # noqa: B1
        cognito_client = MockCognito()

        process_files(
            files=[test_file_location],
            db_session=test_db_session,
            cognito_client=cognito_client,
            cognito_pool_id="fake_pool",
        )
        csv_log_records = [record for record in caplog.records if "process_csv" in record.filename]
        startup_log, finished_file, complete_log = csv_log_records
        assert f"found 3 emails to import in {test_file_location}" in startup_log.getMessage()
        assert (
            f"processed file: {test_file_location}; imported 3 emails, 5 records"
            in finished_file.getMessage()
        )
        assert "done processing files" in complete_log.getMessage()

    def test_duplicate_ula(
        self, test_file_location, test_db_session, create_employers, mock_bogus_fineos, caplog
    ):
        cognito_client = MockCognito()
        email = "test_user@gmail.com"
        fein = "111111111"
        employer = (
            test_db_session.query(Employer).filter(Employer.employer_fein == fein).one_or_none()
        )
        resp = cognito_client.admin_create_user(Username=email)
        mock_active_directory_id = resp["User"]["Attributes"][0]["Value"]
        user = lib.leave_admin_create(
            test_db_session,
            mock_active_directory_id,
            email,
            fein,
            {"auth_id": mock_active_directory_id},
        )
        duplicate_ula = UserLeaveAdministrator(user=user, employer=employer)
        test_db_session.add(duplicate_ula)
        test_db_session.commit()

        pivoted = pivot_csv_file(test_file_location)
        processed = 0
        for email, employers in pivoted.items():
            processed += process_by_email(
                email=email,
                input_data=employers,
                db_session=test_db_session,
                cognito_pool_id="fake_pool",
                filename=test_file_location,
                cognito_client=cognito_client,
            )
        #  We won't process the combination of `test_user@gmail.com` and `111111111`
        #  (as we intentionally created dupe ULAs)
        assert processed == 4
        count_error_db_lookup = 0
        count_error_calling_fineos = 0
        count_error_for_bad_email = 0
        for record in caplog.records:
            if "Duplicate records found for UserLeaveAdministrator" in record.getMessage():
                count_error_db_lookup += 1
            elif "Received an error processing FINEOS registration" in record.getMessage():
                count_error_calling_fineos += 1
            elif (
                f"Unable to complete registration for {email} for employer " in record.getMessage()
            ):
                count_error_for_bad_email += 1

        assert count_error_db_lookup == 1
        assert count_error_calling_fineos == 0
        assert count_error_for_bad_email == 0
