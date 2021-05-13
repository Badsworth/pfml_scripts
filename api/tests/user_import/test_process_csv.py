import logging  # noqa: B1
import uuid
from pathlib import Path

import boto3
import moto
import pytest

import massgov.pfml.fineos.mock_client
from massgov.pfml import fineos
from massgov.pfml.db.models.employees import Employer, Role, User, UserLeaveAdministrator, UserRole
from massgov.pfml.user_import.process_csv import (
    clean_fein,
    log_progress,
    pivot_csv_file,
    process_by_email,
    process_files,
    split_successes_from_failures,
)

# every test in here requires real resources
pytestmark = pytest.mark.integration


class MockCognito:
    def __init__(self):
        self._memo = dict()

        with moto.mock_cognitoidp():
            self.client = boto3.client("cognito-idp", "us-east-1")
            self.exceptions = self.client.exceptions

    def admin_create_user(self, *args, UserPoolId="", **kwargs):
        sub = str(uuid.uuid4())
        self._memo[kwargs["Username"]] = sub
        return {"User": {"Attributes": [{"Name": "sub", "Value": sub}]}}

    def admin_set_user_password(self, *args, **kwargs):
        pass

    def admin_get_user(self, *args, UserPoolId="", Username="", **kwargs):
        sub = self._memo.get(Username)
        if sub:
            return {"UserAttributes": [{"Name": "sub", "Value": sub}]}

        raise self.client.exceptions.UserNotFoundException(
            error_response={
                "Error": {"Code": "UserNotFoundException", "Message": "User not found",}
            },
            operation_name="AdminGetUser",
        )


class MockCognitoPasswordError(MockCognito):
    def admin_set_user_password(self, *args, **kwargs):
        raise self.client.exceptions.UserNotFoundException(
            error_response={
                "Error": {"Code": "UserNotFoundException", "Message": "User not found",}
            },
            operation_name="AdminGetUser",
        )


class MockCognitoListRateLimit(MockCognito):
    def __init__(self):
        self._retries = 0
        super().__init__()

    def admin_get_user(self, *args, UserPoolId="", Username="", **kwargs):
        self._retries += 1
        if (self._retries % 2) == 0:
            raise self.client.exceptions.TooManyRequestsException(
                error_response={
                    "Error": {"Code": "TooManyRequestsException", "Message": "Too many requests",}
                },
                operation_name="AdminGetUser",
            )
        else:
            return super().admin_get_user(*args, UserPoolId=UserPoolId, Username=Username, **kwargs)


@pytest.fixture
def mock_bogus_fineos():
    def mock_create_or_update_leave_admin(
        leave_admin_create_or_update: fineos.models.CreateOrUpdateLeaveAdmin,
    ) -> None:
        raise fineos.FINEOSFatalResponseError(Exception("OHNO"))

    mock_fineos = fineos.create_client()
    mock_fineos.create_or_update_leave_admin = mock_create_or_update_leave_admin
    return mock_fineos


@pytest.fixture
def test_file_location():
    return Path(__file__).parent / "test_users1.csv"


@pytest.fixture
def broken_test_file_location():
    return Path(__file__).parent / "broken_test_users1.csv"


@pytest.fixture
def bom_test_file_location():
    return Path(__file__).parent / "bom_test_users1.csv"


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


@pytest.fixture
def local_create_employers(local_test_db_session):
    local_test_db_session.add(
        Employer(employer_fein="847847847", employer_dba="Wayne Enterprises", fineos_employer_id=1)
    )
    local_test_db_session.add(
        Employer(employer_fein="111111111", employer_dba="BogoCorp Ltd", fineos_employer_id=2)
    )
    local_test_db_session.add(
        Employer(
            employer_fein="222222222",
            employer_dba="Charles Entertainment Cheese",
            fineos_employer_id=3,
        )
    )
    local_test_db_session.add(
        Employer(employer_fein="114444444", employer_dba="Dunkin", fineos_employer_id=4)
    )
    local_test_db_session.commit()


class TestProcessCSV:
    """ Tests for helper functions within process_csv """

    def test_pivot_csv(self, test_file_location):
        pivoted = pivot_csv_file(test_file_location)
        assert len(pivoted) == 3
        assert sum(len(x) for x in pivoted.values()) == 5
        assert len(pivoted["test_user@gmail.com"]) == 2

    def test_pivot_csv_bom_encoding(self, bom_test_file_location):
        pivoted = pivot_csv_file(bom_test_file_location)
        assert pivoted["bogus@yahoo.com"] == [
            {"fein": "222222222", "email": "bogus@yahoo.com", "verification_code": ""}
        ]

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
        processed = []
        for email, employers in pivoted.items():
            processed += process_by_email(
                email=email,
                input_data=employers,
                db_session=test_db_session,
                force_registration=True,
                cognito_pool_id="fake_pool",
                cognito_client=cognito_client,
                fineos_client=fineos_client,
            )
        # 5 records in this file
        (
            successfully_processed_records,
            unsuccessfully_processed_records,
        ) = split_successes_from_failures(processed)
        assert len(successfully_processed_records) == 5
        assert len(unsuccessfully_processed_records) == 0
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
        processed = []
        for email, employers in pivoted.items():
            processed += process_by_email(
                email=email,
                input_data=employers,
                db_session=test_db_session,
                force_registration=True,
                cognito_pool_id="fake_pool",
                filename=test_file_location,
                cognito_client=cognito_client,
                fineos_client=mock_bogus_fineos,
            )
        # 5 records in this file
        (
            successfully_processed_records,
            unsuccessfully_processed_records,
        ) = split_successes_from_failures(processed)
        assert len(successfully_processed_records) == 0
        assert len(unsuccessfully_processed_records) == 5
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
        processed = []
        for email, employers in pivoted.items():
            processed += process_by_email(
                email=email,
                input_data=employers,
                db_session=test_db_session,
                force_registration=True,
                cognito_pool_id="fake_pool",
                filename=test_file_location,
                cognito_client=cognito_client,
                fineos_client=mock_bogus_fineos,
            )
        # 5 records in this file
        (
            successfully_processed_records,
            unsuccessfully_processed_records,
        ) = split_successes_from_failures(processed)
        assert len(successfully_processed_records) == 0
        assert len(unsuccessfully_processed_records) == 5
        count_error_in_cognito = 0
        for record in caplog.records:
            if "Unable to set Cognito password for user" in record.getMessage():
                count_error_in_cognito += 1

        #  Only 3 emails in the file
        assert count_error_in_cognito == 3

    def test_process_by_email_flaky_get_user(
        self, test_file_location, test_db_session, create_employers, caplog
    ):
        caplog.set_level(logging.INFO)  # noqa: B1
        cognito_client = MockCognitoListRateLimit()
        pivoted = pivot_csv_file(test_file_location)
        processed = []
        for email, employers in pivoted.items():
            processed += process_by_email(
                email=email,
                input_data=employers,
                db_session=test_db_session,
                force_registration=True,
                cognito_pool_id="fake_pool",
                filename=test_file_location,
                cognito_client=cognito_client,
            )
        # 5 records in this file
        (
            successfully_processed_records,
            unsuccessfully_processed_records,
        ) = split_successes_from_failures(processed)
        assert len(successfully_processed_records) == 5
        assert len(unsuccessfully_processed_records) == 0
        count_error_in_cognito_get_user = 0
        for record in caplog.records:
            if "Too many requests error from Cognito" in record.getMessage():
                count_error_in_cognito_get_user += 1

        assert count_error_in_cognito_get_user == 4

    @moto.mock_s3
    def test_process_files(
        self, test_file_location, test_db_session, create_employers, caplog, monkeypatch
    ):
        monkeypatch.setenv(
            "PROCESS_CSV_DATA_BUCKET_NAME", "test-bucket",
        )
        conn = boto3.resource("s3", region_name="us-east-1")
        conn.create_bucket(Bucket="test-bucket")

        caplog.set_level(logging.INFO)  # noqa: B1
        cognito_client = MockCognito()

        process_files(
            files=[test_file_location],
            db_session=test_db_session,
            force_registration=True,
            cognito_client=cognito_client,
            cognito_pool_id="fake_pool",
        )
        csv_log_records = [record for record in caplog.records if "process_csv" in record.filename]
        startup_log, success_file_upload, finished_file, complete_log = csv_log_records
        assert f"found 3 emails to import in {test_file_location}" in startup_log.getMessage()
        assert (
            f"processed file: {test_file_location}; imported 3 emails, 5 records"
            in finished_file.getMessage()
        )
        assert "done processing files" in complete_log.getMessage()
        assert "Uploading results to S3." in success_file_upload.getMessage()

    def test_no_fineos_web_ids_created_when_not_forcing_registration(
        self, test_file_location, local_test_db_session, local_create_employers
    ):
        massgov.pfml.fineos.mock_client.start_capture()
        fineos_client = fineos.create_client()
        cognito_client = MockCognito()
        pivoted = pivot_csv_file(test_file_location)
        processed = []
        for email, employers in pivoted.items():
            processed += process_by_email(
                email=email,
                input_data=employers,
                db_session=local_test_db_session,
                force_registration=False,
                cognito_pool_id="fake_pool",
                cognito_client=cognito_client,
                fineos_client=fineos_client,
            )
        # 5 records in this file
        (
            successfully_processed_records,
            unsuccessfully_processed_records,
        ) = split_successes_from_failures(processed)
        assert len(successfully_processed_records) == 5
        assert len(unsuccessfully_processed_records) == 0
        # Should have created 3 cognito users
        assert len(cognito_client._memo) == 3
        # Ensure all emails in pivoted file were created in cognito
        assert set(cognito_client._memo.keys()) == set(pivoted.keys())

        # Ensure ALL changes are committed by the process_by_email flow with intentional rollback
        local_test_db_session.rollback()
        users_created = local_test_db_session.query(User).all()
        assert len(users_created) == 3
        user_roles_created = local_test_db_session.query(UserRole).all()
        assert len(user_roles_created) == 3
        for user_role in user_roles_created:
            assert user_role.role_id == Role.EMPLOYER.role_id

        # We shouldn't have any fineos_web_ids in the ULA table because none of these users have verified.
        user_leave_admins = local_test_db_session.query(UserLeaveAdministrator).all()
        assert len(user_leave_admins) == 3
        for ula in user_leave_admins:
            assert ula.fineos_web_id is None
        capture = massgov.pfml.fineos.mock_client.get_capture()
        assert len(capture) == 0

    def test_error_if_file_has_invalid_headers(
        self, broken_test_file_location, test_db_session, caplog
    ):
        caplog.set_level(logging.INFO)  # noqa: B1
        cognito_client = MockCognito()

        with pytest.raises(Exception):
            process_files(
                files=[broken_test_file_location],
                db_session=test_db_session,
                force_registration=True,
                cognito_client=cognito_client,
                cognito_pool_id="fake_pool",
            )
        assert "File has invalid headers" in caplog.text
