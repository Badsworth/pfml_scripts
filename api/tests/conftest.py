"""
conftest.py files are automatically loaded by pytest, they are an easy place to
put shared test fixtures as well as define other pytest configuration (define
hooks, load plugins, define new/override assert behavior, etc.).

More info:
https://docs.pytest.org/en/latest/fixture.html#conftest-py-sharing-fixture-functions
"""
import logging.config  # noqa: B1
import os
import uuid
from datetime import date, datetime, timedelta, timezone
from typing import List
from unittest.mock import MagicMock

import _pytest.monkeypatch
import boto3
import moto
import pytest
import sqlalchemy
from jose import jwt
from jose.constants import ALGORITHMS
from pytest import Item

import massgov.pfml.api.app
import massgov.pfml.api.authentication as authentication
import massgov.pfml.api.employees
import massgov.pfml.db.models.employees as employee_models
import massgov.pfml.util.files as file_util
import massgov.pfml.util.logging
from massgov.pfml.api.models.claims.responses import AbsencePeriodResponse
from massgov.pfml.db.models.factories import (
    ClaimFactory,
    EmployeeFactory,
    EmployerFactory,
    TaxIdentifierFactory,
    UserFactory,
)

logger = massgov.pfml.util.logging.get_logger("massgov.pfml.api.tests.conftest")


def get_mock_logger():
    mock_logger = MagicMock()
    mock_logger.info = MagicMock()
    mock_logger.warning = MagicMock()
    mock_logger.error = MagicMock()

    return mock_logger


@pytest.fixture(scope="session")
def has_external_dependencies():
    """
    Use this fixture to automatically mark all tests that are in the downline
    of fixtures or tests that request this fixture.
    """
    pass


@pytest.fixture(autouse=True, scope="session")
def set_no_db_factories_alert():
    """By default, ensure factories do not attempt to access the database.

    The tests that need generated models to actually hit the database can pull
    in the `initialize_factories_session` fixture to their test case to enable
    factory writes to the database.
    """
    os.environ["DB_FACTORIES_DISABLE_DB_ACCESS"] = "1"


@pytest.fixture
def app_cors(monkeypatch, test_db):
    monkeypatch.setenv("CORS_ORIGINS", "http://example.com")
    return massgov.pfml.api.app.create_app(check_migrations_current=False)


@pytest.fixture
def app(test_db_session, initialize_factories_session, set_auth_public_keys):
    return massgov.pfml.api.app.create_app(
        check_migrations_current=False, db_session_factory=test_db_session, do_close_db=False
    )


@pytest.fixture
def client(app):
    return app.app.test_client()


@pytest.fixture
def logging_fix(monkeypatch):
    """Disable the application custom logging setup

    Needed if the code under test calls massgov.pfml.util.logging.init() so that
    tests using the caplog fixture don't break.
    """
    monkeypatch.setattr(logging.config, "dictConfig", lambda config: None)  # noqa: B1


@pytest.fixture
def user(initialize_factories_session):
    user = UserFactory.create()
    return user


@pytest.fixture
def employer():
    return EmployerFactory.create(employer_fein="112222222")


@pytest.fixture
def tax_identifier():
    return TaxIdentifierFactory.create(tax_identifier="123456789")


@pytest.fixture
def employee(tax_identifier):
    return EmployeeFactory.create(tax_identifier_id=tax_identifier.tax_identifier_id)


@pytest.fixture
def claim(employer, employee):
    return ClaimFactory.create(
        employer=employer,
        employee=employee,
        fineos_absence_status_id=1,
        claim_type_id=1,
        fineos_absence_id="foo",
    )


@pytest.fixture
def absence_period():
    return AbsencePeriodResponse(
        fineos_leave_request_id="PL-14449-0000002237",
        absence_period_start_date=date(2021, 1, 29),
        absence_period_end_date=date(2021, 1, 30),
        reason="Child Bonding",
        reason_qualifier_one="Foster Care",
        reason_qualifier_two="",
        period_type="Continuous",
        request_decision="Pending",
        evidence_status=None,
    )


@pytest.fixture
def set_auth_public_keys(monkeypatch, auth_key):
    monkeypatch.setattr(authentication, "public_keys", auth_key)


@pytest.fixture(scope="session")
def auth_claims_unit():
    claims = {
        "exp": datetime.now() + timedelta(days=1),
        "sub": "foo",
    }

    return claims


@pytest.fixture(scope="session")
def auth_token_unit(auth_claims_unit, auth_private_key):
    encoded = jwt.encode(auth_claims_unit, auth_private_key, algorithm=ALGORITHMS.RS256)
    return encoded


@pytest.fixture
def auth_claims(auth_claims_unit, user):
    auth_claims = auth_claims_unit.copy()
    auth_claims["sub"] = str(user.sub_id)

    return auth_claims


@pytest.fixture
def employer_claims(employer_user):
    claims = {
        "exp": datetime.now(timezone.utc) + timedelta(days=1),
        "sub": str(employer_user.sub_id),
    }

    return claims


@pytest.fixture
def consented_user(initialize_factories_session):
    user = UserFactory.create(consented_to_data_sharing=True)
    return user


@pytest.fixture
def user_with_mfa(initialize_factories_session):
    user = UserFactory.create(mfa_phone_number="+15109283075", mfa_delivery_preference_id=1,)
    return user


@pytest.fixture
def fineos_user(initialize_factories_session):
    user = UserFactory.create(roles=[employee_models.Role.FINEOS])
    return user


@pytest.fixture
def snow_user(initialize_factories_session):
    user = UserFactory.create(roles=[employee_models.Role.PFML_CRM])
    return user


@pytest.fixture
def employer_user(initialize_factories_session):
    user = UserFactory.create(roles=[employee_models.Role.EMPLOYER])
    return user


@pytest.fixture
def disable_employee_endpoint(monkeypatch):
    new_env = monkeypatch.setenv("ENABLE_EMPLOYEE_ENDPOINTS", "0")
    return new_env


@pytest.fixture
def enable_application_fraud_check(monkeypatch):
    new_env = monkeypatch.setenv("ENABLE_APPLICATION_FRAUD_CHECK", "1")
    return new_env


@pytest.fixture
def consented_user_claims(consented_user):
    claims = {
        "a": "b",
        "exp": datetime.now() + timedelta(days=1),
        "sub": str(consented_user.sub_id),
    }

    return claims


@pytest.fixture
def fineos_user_claims(fineos_user):
    claims = {
        "a": "b",
        "exp": datetime.now() + timedelta(days=1),
        "sub": str(fineos_user.sub_id),
    }

    return claims


@pytest.fixture
def snow_user_claims(snow_user):
    claims = {
        "a": "b",
        "exp": datetime.now() + timedelta(days=1),
        "sub": str(snow_user.sub_id),
    }

    return claims


@pytest.fixture(scope="session")
def azure_auth_keys():
    """A fake public key for Azure AD"""
    return {
        "keys": [
            {
                "alg": "RS256",
                "e": "AQAB",
                "kid": "azure_kid",
                "kty": "RSA",
                "n": "iWBm-DQbycUqrPBSD5yk73zxyIr66hBUCyPCShW-btQ-nyBk1E-h4AvtqHpl4Y1aghQDTnn2gLHiRtV_XJtCpK1PEJ3SCqw6wGOEw5bbG7Q88KDvTMUF5k6gzRMHMBTD7lMNPIY-oCuh_Rwvg19hGBD2O6rA2sMHyTB-O2ZwL6M",
                "use": "sig",
            },
        ]
    }


@pytest.fixture(scope="session")
def auth_key():
    hmac_key = {
        "alg": "RS256",
        "e": "AQAB",
        "kid": "c7f7e776-bd29-4d00-b110-d4d4a8652815",
        "kty": "RSA",
        "n": "iWBm-DQbycUqrPBSD5yk73zxyIr66hBUCyPCShW-btQ-nyBk1E-h4AvtqHpl4Y1aghQDTnn2gLHiRtV_XJtCpK1PEJ3SCqw6wGOEw5bbG7Q88KDvTMUF5k6gzRMHMBTD7lMNPIY-oCuh_Rwvg19hGBD2O6rA2sMHyTB-O2ZwL6M",
        "use": "sig",
    }

    return hmac_key


@pytest.fixture(scope="session")
def auth_private_key():
    hmac_key = {
        "alg": "RS256",
        "d": "WC8GyisA73teUpcNxjHCem0U86urN5b1rBTvQglFLfWWoST1NIhNm_lsPGsdfTT0tW1NVhHaV3BYlSm06AFKphL1UtHI0z_xS-CnRuqYljyca1YQWhuFETP01c1tVmA4g8iFGUW_VkQ6QgyHiC_kaz_v8skOLLgLoR6KPeo_yPE",
        "dp": "i8Sa6tKsKrSGsjE6H98dDiTbc_CDogP2-VgNPN5SMa02rki4972o5WmZhiQvcjxlU7NZbeE3fRiiXHt_E_wZan9MFkk",
        "dq": "QRYM74mdgrYHqutTmTY5tuEOsddFiE2NFa-qPagjKQKzvUPhl9EZbkm1VR06K1omw0SoFpxMLc4O3K8Z",
        "e": "AQAB",
        "kid": "67ad345e-8a77-45bb-8988-22aa2ab8ca62",
        "kty": "RSA",
        "n": "iWBm-DQbycUqrPBSD5yk73zxyIr66hBUCyPCShW-btQ-nyBk1E-h4AvtqHpl4Y1aghQDTnn2gLHiRtV_XJtCpK1PEJ3SCqw6wGOEw5bbG7Q88KDvTMUF5k6gzRMHMBTD7lMNPIY-oCuh_Rwvg19hGBD2O6rA2sMHyTB-O2ZwL6M",
        "p": "o2tSqdoRyCMnzT_CZx1Oq8WCwMo7rWMKFx-wlwaXOoxzqDv0YhjP1t7DqDn5V8yERCVBUP9ZPDIzNmBUQMul7bwIpfs",
        "q": "1zQdXV-7I2VNSUhzRAYvhJAOFvAKiJv8lJc2_66XNGww0g3og_sBPrGwFsO2stVd-rJ1mZWV8D78LHR5",
        "qi": "SebQz5QdxAvqGSDUvchSLpxXf0Ry0NhYdBCCMftTwqqVcNjY3GKQ8-YET5Y_dwMmEYM51DCCDolVxBAjbNDlKU7JIjU",
        "use": "sig",
    }

    return hmac_key


@pytest.fixture(scope="session")
def azure_auth_private_key():
    hmac_key = {
        "alg": "RS256",
        "d": "WC8GyisA73teUpcNxjHCem0U86urN5b1rBTvQglFLfWWoST1NIhNm_lsPGsdfTT0tW1NVhHaV3BYlSm06AFKphL1UtHI0z_xS-CnRuqYljyca1YQWhuFETP01c1tVmA4g8iFGUW_VkQ6QgyHiC_kaz_v8skOLLgLoR6KPeo_yPE",
        "dp": "i8Sa6tKsKrSGsjE6H98dDiTbc_CDogP2-VgNPN5SMa02rki4972o5WmZhiQvcjxlU7NZbeE3fRiiXHt_E_wZan9MFkk",
        "dq": "QRYM74mdgrYHqutTmTY5tuEOsddFiE2NFa-qPagjKQKzvUPhl9EZbkm1VR06K1omw0SoFpxMLc4O3K8Z",
        "e": "AQAB",
        "kid": "azure_kid",
        "kty": "RSA",
        "n": "iWBm-DQbycUqrPBSD5yk73zxyIr66hBUCyPCShW-btQ-nyBk1E-h4AvtqHpl4Y1aghQDTnn2gLHiRtV_XJtCpK1PEJ3SCqw6wGOEw5bbG7Q88KDvTMUF5k6gzRMHMBTD7lMNPIY-oCuh_Rwvg19hGBD2O6rA2sMHyTB-O2ZwL6M",
        "p": "o2tSqdoRyCMnzT_CZx1Oq8WCwMo7rWMKFx-wlwaXOoxzqDv0YhjP1t7DqDn5V8yERCVBUP9ZPDIzNmBUQMul7bwIpfs",
        "q": "1zQdXV-7I2VNSUhzRAYvhJAOFvAKiJv8lJc2_66XNGww0g3og_sBPrGwFsO2stVd-rJ1mZWV8D78LHR5",
        "qi": "SebQz5QdxAvqGSDUvchSLpxXf0Ry0NhYdBCCMftTwqqVcNjY3GKQ8-YET5Y_dwMmEYM51DCCDolVxBAjbNDlKU7JIjU",
        "use": "sig",
    }

    return hmac_key


@pytest.fixture
def consented_user_token(consented_user_claims, auth_private_key):
    encoded = jwt.encode(consented_user_claims, auth_private_key, algorithm=ALGORITHMS.RS256)
    return encoded


@pytest.fixture
def fineos_user_token(fineos_user_claims, auth_private_key):
    encoded = jwt.encode(fineos_user_claims, auth_private_key, algorithm=ALGORITHMS.RS256)
    return encoded


@pytest.fixture
def snow_user_token(snow_user_claims, auth_private_key):
    encoded = jwt.encode(snow_user_claims, auth_private_key, algorithm=ALGORITHMS.RS256)
    return encoded


@pytest.fixture
def snow_user_headers(snow_user_token):
    return {"Authorization": "Bearer {}".format(snow_user_token), "Mass-PFML-Agent-ID": "123"}


@pytest.fixture
def auth_token(auth_claims, auth_private_key):
    encoded = jwt.encode(auth_claims, auth_private_key, algorithm=ALGORITHMS.RS256)
    return encoded


@pytest.fixture(scope="session")
def azure_auth_token_unit(auth_claims_unit, azure_auth_private_key):
    encoded = jwt.encode(
        auth_claims_unit,
        azure_auth_private_key,
        algorithm=ALGORITHMS.RS256,
        headers={"kid": azure_auth_private_key.get("kid")},
    )
    return encoded


@pytest.fixture
def employer_auth_token(employer_claims, auth_private_key):
    encoded = jwt.encode(employer_claims, auth_private_key, algorithm=ALGORITHMS.RS256)
    return encoded


@pytest.fixture
def test_fs_path(tmp_path):
    file_name = "test.txt"
    content = "line 1 text\nline 2 text\nline 3 text"

    test_folder = tmp_path / "test_folder"
    test_folder.mkdir()
    test_file = test_folder / file_name
    test_file.write_text(content)
    return test_folder


@pytest.fixture
def mock_cognito(monkeypatch, reset_aws_env_vars):
    import boto3

    with moto.mock_cognitoidp():
        cognito = boto3.client("cognito-idp", "us-east-1")

        def mock_create_cognito_client():
            return cognito

        monkeypatch.setattr(
            massgov.pfml.util.aws.cognito, "create_cognito_client", mock_create_cognito_client
        )

        yield cognito


@pytest.fixture
def mock_cognito_user_pool(monkeypatch, mock_cognito):
    with moto.mock_cognitoidp():
        user_pool_id = mock_cognito.create_user_pool(PoolName=str(uuid.uuid4()))["UserPool"]["Id"]
        user_pool_client_id = mock_cognito.create_user_pool_client(
            UserPoolId=user_pool_id, ClientName="test"
        )["UserPoolClient"]["ClientId"]

        monkeypatch.setenv("COGNITO_USER_POOL_ID", user_pool_id)
        monkeypatch.setenv("COGNITO_USER_POOL_CLIENT_ID", user_pool_client_id)

        yield {"id": user_pool_id, "client_id": user_pool_client_id}


@pytest.fixture(autouse=True)
def mock_azure(monkeypatch, azure_auth_keys):
    def mock_get_public_keys(_, url):
        return azure_auth_keys.get("keys")

    monkeypatch.setattr(
        massgov.pfml.api.authentication.azure.AzureClientConfig,
        "_get_public_keys",
        mock_get_public_keys,
    )
    monkeypatch.setenv("AZURE_AD_CLIENT_ID", "client_id")
    monkeypatch.setenv("AZURE_AD_TENANT_ID", "tenant_id")
    monkeypatch.setenv("AZURE_AD_AUTHORITY_DOMAIN", "example.com")
    monkeypatch.setenv("AZURE_AD_CLIENT_SECRET", "secret_value")
    monkeypatch.setenv("ADMIN_PORTAL_BASE_URL", "http://localhost:3001")
    monkeypatch.setenv("AZURE_AD_PARENT_GROUP", "TSS-SG-PFML_ADMIN_PORTAL_NON_PROD")

    return authentication.configure_azure_ad()


@pytest.fixture
def mock_ses(monkeypatch, reset_aws_env_vars):
    import boto3

    monkeypatch.setenv("DFML_PROJECT_MANAGER_EMAIL_ADDRESS", "test@test.gov")
    monkeypatch.setenv("PFML_EMAIL_ADDRESS", "noreplypfml@mass.gov")
    monkeypatch.setenv("BOUNCE_FORWARDING_EMAIL", "noreplypfml@mass.gov")
    monkeypatch.setenv(
        "BOUNCE_FORWARDING_EMAIL_ADDRESS_ARN",
        "arn:aws:ses:us-east-1:498823821309:identity/noreplypfml@mass.gov",
    )
    monkeypatch.setenv("DFML_BUSINESS_OPERATIONS_EMAIL_ADDRESS", "test3@example.com")

    with moto.mock_ses():
        ses = boto3.client("ses")
        ses.verify_email_identity(EmailAddress=os.getenv("PFML_EMAIL_ADDRESS"))
        yield ses


@pytest.fixture
def mock_s3(reset_aws_env_vars):
    with moto.mock_s3():
        yield boto3.resource("s3")


@pytest.fixture
def mock_s3_bucket_resource(mock_s3):
    bucket = mock_s3.Bucket("test_bucket")
    bucket.create()
    yield bucket


@pytest.fixture
def mock_s3_bucket(mock_s3_bucket_resource):
    yield mock_s3_bucket_resource.name


@pytest.fixture
def mock_sftp_paths(monkeypatch):
    source_directory_path = "dua/pending"
    archive_directory_path = "dua/archive"
    moveit_pickup_path = "upload/DFML/DUA/Inbound"

    monkeypatch.setenv("DUA_TRANSFER_BASE_PATH", "local_s3/agency_transfer")
    monkeypatch.setenv("OUTBOUND_DIRECTORY_PATH", source_directory_path)
    monkeypatch.setenv("ARCHIVE_DIRECTORY_PATH", archive_directory_path)
    monkeypatch.setenv("MOVEIT_SFTP_URI", "sftp://foo@bar.com")
    monkeypatch.setenv("MOVEIT_SSH_KEY", "foo")

    pending_directory = f"local_s3/agency_transfer/{source_directory_path}"
    archive_directory = f"local_s3/agency_transfer/{archive_directory_path}"

    paths = {
        "pending_directory": pending_directory,
        "archive_directory": archive_directory,
        "moveit_pickup_path": moveit_pickup_path,
    }

    return paths


@pytest.fixture
def mock_sftp_client():
    class MockSftpClient:
        calls = []
        files = {}
        _dirs = {}

        def _append_dir(self, new_dir):
            dirs = set(self._dirs)
            dirs.add(new_dir)
            self._dirs = list(dirs)
            return self._dirs

        def _remove_dir(self, dir):
            dirs = set(self._dirs)
            dirs.discard(dir)
            self._dirs = list(dirs)
            return self._dirs

        def _rename_dir(self, olddir, newdir):
            self._remove_dir(olddir)
            self._append_dir(newdir)

        def get(self, src: str, dest: str):
            self.calls.append(("get", src, dest))
            if src in self._dirs:
                try:
                    os.mkdir(dest)
                except FileExistsError:
                    pass
                target_dir = dest
                dir_files = self.listdir(src)
                for file in dir_files:
                    self.get(f"{src}/{file}", f"{target_dir}/{file}")
            else:
                body = self.files.get(src)
                if body is not None:
                    with open(dest, "w") as f:
                        f.write(body)

        def put(self, src: str, dest: str, confirm: bool):
            """
            This isn't recursive, i.e. you can put /dir and it will contain
            - /dir/f1
            - /dir/f2
            - ...
            But it will NOT contain
            - /dir/subdir/file

            For testing, if you put a single file to /dir/target.txt, it will not register
            the directory.  You should put /dir
            """
            self.calls.append(("put", src, dest))
            if os.path.isfile(src):
                with open(src) as f:
                    self.files[dest] = f.read()
            else:
                self._append_dir(dest)
                files = os.listdir(src)
                for file in files:
                    file_path = f"{src}/{file}"
                    with open(file_path) as f:
                        self.files[f"{dest}/{file}"] = f.read()

        def remove(self, filename: str):
            self.calls.append(("remove", filename))
            if filename in self._dirs:
                dir_files = self.listdir(filename)
                for file in dir_files:
                    self.remove(f"{filename}/{file}")
                self._remove_dir(filename)
            else:
                body = self.files.get(filename)
                if body is not None:
                    del self.files[filename]

        def rename(self, oldpath: str, newpath: str):
            self.calls.append(("rename", oldpath, newpath))
            if oldpath in self._dirs:
                dir_files = self.listdir(oldpath)
                for file in dir_files:
                    self.rename(f"{oldpath}/{file}", f"{newpath}/{file}")
                self._rename_dir(oldpath, newpath)
            else:
                body = self.files.get(oldpath)
                if body is not None:
                    self.files[newpath] = body
                    del self.files[oldpath]

        def listdir(self, dir: str):
            self.calls.append(("listdir", dir))
            # Remove the directory from the front of the file name to match the behaviour of the
            # non-mocked SFTP client we use which returns the filenames relative to the directory
            # passed in instead of the entire path to the file.
            first_char_index = len(dir) + 1 if len(dir) else 0
            return sorted(
                [fn[first_char_index:] for fn in list(self.files.keys()) if fn.startswith(dir)]
            )

        # Non-standard method to add/modify the SFTP client with files of our choosing.
        def _add_file(self, path: str, body: str):
            self.files[path] = body

        # Tests that inspect the contents of the calls attribute can call this function to
        # conveniently reset the calls attribute back to an empty list between tests.
        def reset_calls(self):
            self.calls = []

    return MockSftpClient()


@pytest.fixture
def setup_mock_sftp_client(monkeypatch, mock_sftp_client):
    # Mock SFTP client so we can inspect the method calls we make later in the test.
    monkeypatch.setattr(
        file_util, "get_sftp_client", lambda uri, ssh_key_password, ssh_key: mock_sftp_client,
    )


@pytest.fixture(scope="session")
def test_db_schema(has_external_dependencies, monkeypatch_session):
    """
    Create a test schema, if it doesn't already exist, and drop it after the
    test completes.
    """
    schema_name = f"api_test_{uuid.uuid4().int}"

    monkeypatch_session.setenv("DB_SCHEMA", schema_name)

    db_schema_create(schema_name)
    try:
        yield schema_name
    finally:
        db_schema_drop(schema_name)


def db_schema_create(schema_name):
    """Create a database schema."""
    db_config = massgov.pfml.db.config.get_config()
    db_test_user = db_config.username

    exec_sql_admin(f"CREATE SCHEMA IF NOT EXISTS {schema_name} AUTHORIZATION {db_test_user};")
    logger.info("create schema %s", schema_name)


def db_schema_drop(schema_name):
    """Drop a database schema."""
    exec_sql_admin(f"DROP SCHEMA {schema_name} CASCADE;")
    logger.info("drop schema %s", schema_name)


def exec_sql_admin(sql):
    db_admin_config = massgov.pfml.db.config.get_config(prefer_admin=True)
    engine = massgov.pfml.db.create_engine(db_admin_config)
    with engine.connect() as connection:
        connection.execute(sql)


@pytest.fixture(scope="session")
def test_db(test_db_schema):
    """
    Creates a test schema, directly creating all tables with SQLAlchemy. Schema
    is dropped after the test completes.
    """
    import massgov.pfml.db as db
    import massgov.pfml.db.models.applications as applications  # noqa: F401

    # not used directly, but loads models into Base
    import massgov.pfml.db.models.employees as employees  # noqa: F401
    from massgov.pfml.db.models.base import Base

    engine = db.create_engine()
    Base.metadata.create_all(bind=engine)

    db_session = db.init(sync_lookups=True)
    db_session.close()
    db_session.remove()

    return engine


Session = sqlalchemy.orm.sessionmaker()


@pytest.fixture
def test_db_session(test_db):
    # Based on https://docs.sqlalchemy.org/en/13/orm/session_transaction.html#joining-a-session-into-an-external-transaction-such-as-for-test-suites
    connection = test_db.connect()
    trans = connection.begin()
    session = Session(bind=connection)

    session.begin_nested()

    @sqlalchemy.event.listens_for(session, "after_transaction_end")
    def restart_savepoint(session, transaction):
        if transaction.nested and not transaction._parent.nested:
            session.begin_nested()

    yield session

    session.close()
    trans.rollback()
    connection.close()


@pytest.fixture
def test_db_other_session(test_db):
    # Based on https://docs.sqlalchemy.org/en/13/orm/session_transaction.html#joining-a-session-into-an-external-transaction-such-as-for-test-suites
    connection = test_db.connect()
    trans = connection.begin()
    session = Session(bind=connection)

    yield session

    session.close()
    trans.rollback()
    connection.close()


@pytest.fixture
def initialize_factories_session(monkeypatch, test_db_session):
    monkeypatch.delenv("DB_FACTORIES_DISABLE_DB_ACCESS")

    import massgov.pfml.db.models.factories as factories

    logger.info("set factories db_session to %s", test_db_session)
    factories.db_session = test_db_session


@pytest.fixture
def local_test_db_schema(has_external_dependencies, monkeypatch):
    """
    Create a test schema, if it doesn't already exist, and drop it after the
    test completes.
    """
    schema_name = f"api_test_{uuid.uuid4().int}"

    monkeypatch.setenv("DB_SCHEMA", schema_name)

    db_schema_create(schema_name)
    try:
        yield schema_name
    finally:
        db_schema_drop(schema_name)


@pytest.fixture
def local_test_db(local_test_db_schema):
    """
    Creates a test schema, directly creating all tables with SQLAlchemy. Schema
    is dropped after the test completes.
    """
    import massgov.pfml.db as db
    import massgov.pfml.db.models.applications as applications  # noqa: F401

    # not used directly, but loads models into Base
    import massgov.pfml.db.models.employees as employees  # noqa: F401
    import massgov.pfml.db.models.payments as payments  # noqa: F401
    from massgov.pfml.db.models.base import Base

    engine = db.create_engine()
    Base.metadata.create_all(bind=engine)

    db_session = db.init(sync_lookups=True, check_migrations_current=False)
    db_session.close()
    db_session.remove()

    return engine


@pytest.fixture
def local_test_db_session(local_test_db):
    import massgov.pfml.db as db

    db_session = db.init(sync_lookups=False, check_migrations_current=False)

    yield db_session

    db_session.close()
    db_session.remove()


@pytest.fixture
def local_test_db_other_session(local_test_db):
    import massgov.pfml.db as db

    db_session = db.init(sync_lookups=False, check_migrations_current=False)

    yield db_session

    db_session.close()
    db_session.remove()


@pytest.fixture
def local_initialize_factories_session(monkeypatch, local_test_db_session):
    monkeypatch.delenv("DB_FACTORIES_DISABLE_DB_ACCESS")
    import massgov.pfml.db.models.factories as factories

    logger.info("set factories db_session to %s", local_test_db_session)
    factories.db_session = local_test_db_session


@pytest.fixture
def migrations_test_db_schema(has_external_dependencies, monkeypatch):
    """
    Create a test schema, if it doesn't already exist, and drop it after the
    test completes.
    """
    schema_name = f"api_test_{uuid.uuid4().int}"

    monkeypatch.setenv("DB_SCHEMA", schema_name)

    db_schema_create(schema_name)
    try:
        yield schema_name
    finally:
        db_schema_drop(schema_name)


@pytest.fixture
def test_db_via_migrations(has_external_dependencies, migrations_test_db_schema, logging_fix):
    """
    Creates a test schema, runs migrations through Alembic. Schema is dropped
    after the test completes.
    """
    from pathlib import Path

    from alembic import command
    from alembic.config import Config

    alembic_cfg = Config(
        os.path.join(os.path.dirname(__file__), "../massgov/pfml/db/migrations/alembic.ini")
    )
    # Change directory location so the relative script_location in alembic config works.
    os.chdir(Path(__file__).parent.parent)
    command.upgrade(alembic_cfg, "head")

    return migrations_test_db_schema


@pytest.fixture
def test_db_session_via_migrations(test_db_via_migrations):
    import massgov.pfml.db as db

    db_session = db.init()

    yield db_session

    db_session.close()
    db_session.remove()


@pytest.fixture
def initialize_factories_session_via_migrations(test_db_session_via_migrations):
    import massgov.pfml.db.models.factories as factories

    factories.db_session = test_db_session_via_migrations


@pytest.fixture(scope="module")
def module_persistent_db(has_external_dependencies, monkeypatch_module, request):
    import massgov.pfml.db as db
    import massgov.pfml.db.models.applications as applications  # noqa: F401

    # not used directly, but loads models into Base
    import massgov.pfml.db.models.employees as employees  # noqa: F401
    from massgov.pfml.db.models.base import Base

    schema_name = f"api_test_persistent_{uuid.uuid4().int}"
    logger.info("use persistent test db for module %s", request.module.__name__)

    monkeypatch_module.setenv("DB_SCHEMA", schema_name)
    db_schema_create(schema_name)

    engine = db.create_engine()
    Base.metadata.create_all(bind=engine)

    db_session = db.init(sync_lookups=True)

    try:
        yield schema_name
    finally:
        db_session.close()
        db_session.remove()
        db_schema_drop(schema_name)


@pytest.fixture
def module_persistent_db_session(module_persistent_db, monkeypatch):
    import massgov.pfml.db as db
    import massgov.pfml.db.models.factories as factories

    db_session = db.init(sync_lookups=False)

    monkeypatch.delenv("DB_FACTORIES_DISABLE_DB_ACCESS")

    logger.info("set factories db_session to %s", db_session)
    factories.db_session = db_session

    yield db_session

    db_session.close()
    db_session.remove()


@pytest.fixture
def mock_db_session(mocker):
    return mocker.patch("sqlalchemy.orm.Session", autospec=True)


# From https://github.com/pytest-dev/pytest/issues/363
@pytest.fixture(scope="session")
def monkeypatch_session(request):
    mpatch = _pytest.monkeypatch.MonkeyPatch()
    yield mpatch
    mpatch.undo()


# From https://github.com/pytest-dev/pytest/issues/363
@pytest.fixture(scope="module")
def monkeypatch_module(request):
    mpatch = _pytest.monkeypatch.MonkeyPatch()
    yield mpatch
    mpatch.undo()


@pytest.fixture
def set_env_to_local(monkeypatch):
    # this should always be the case for the tests, but the when testing
    # behavior that depends on the ENVIRONMENT value, best set it explicitly, to
    # be sure we test the correct behavior
    monkeypatch.setenv("ENVIRONMENT", "local")


@pytest.fixture
def reset_aws_env_vars(monkeypatch):
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_SECURITY_TOKEN", "testing")
    monkeypatch.setenv("AWS_SESSION_TOKEN", "testing")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """Format output for GitHub Actions.

    See https://docs.github.com/en/free-pro-team@latest/actions/reference/workflow-commands-for-github-actions
    """
    yield

    if "CI" not in os.environ:
        return

    for report in terminalreporter.stats.get("failed", []):
        print(
            "::error file=api/%s,line=%s::%s %s\n"
            % (
                report.location[0],
                report.location[1],
                report.location[2],
                report.longrepr.reprcrash.message,
            )
        )


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_collection_modifyitems(items: List[Item]):
    """Automatically mark integration tests.

    Automatically marks any test with the has_external_dependencies fixture in its
    fixture request graph as an integration test.

    Other markers could be established here as well.
    """

    for item in items:
        if "has_external_dependencies" in item.fixturenames:
            item.add_marker(pytest.mark.integration)

    yield


# This fixture was necessary at the time of this PR as
# the test_db_via_migration was not working. Will refactor
# once that fixture is fixed. The code here is functionally
# equal to index created in migration file:
# 2021_04_27_17_07_38_a654bf03da3f_switch_dua_payment_data_to_use_fineos_.py
@pytest.fixture
def dua_reduction_payment_unique_index(initialize_factories_session):
    import massgov.pfml.db as db

    engine = db.create_engine()
    with engine.connect() as connection:
        connection.execute(
            """
            create unique index on dua_reduction_payment (
                fineos_customer_number,
                coalesce(employer_fein, ''),
                coalesce(payment_date, '1788-02-06'),
                coalesce(request_week_begin_date, '1788-02-06'),
                coalesce(gross_payment_amount_cents, 99999999),
                coalesce(payment_amount_cents, 99999999),
                coalesce(fraud_indicator, ''),
                coalesce(benefit_year_end_date, '1788-02-06'),
                coalesce(benefit_year_begin_date, '1788-02-06')
            )
        """
        )


@pytest.fixture
def sqlalchemy_query_counter():
    class SQLAlchemyQueryCounter:
        """
        Check SQLAlchemy query count.
        Usage:
            with SQLAlchemyQueryCounter(session, expected_query_count=2):
                conn.execute("SELECT 1")
                conn.execute("SELECT 1")
        """

        def __init__(self, session, expected_query_count):
            self.engine = session.get_bind()
            self._query_count = expected_query_count
            self.count = 0

        def __enter__(self):
            sqlalchemy.event.listen(self.engine, "after_execute", self._callback)
            return self

        def __exit__(self, *_):
            sqlalchemy.event.remove(self.engine, "after_execute", self._callback)
            assert self.count == self._query_count, (
                "Executed: " + str(self.count) + " != Required: " + str(self._query_count)
            )

        def _callback(self, *_):
            self.count += 1

    return SQLAlchemyQueryCounter


pytest.register_assert_rewrite("tests.helpers")
