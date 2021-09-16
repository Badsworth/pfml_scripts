#
# Tests for massgov.pfml.db.
#
import logging  # noqa: B1
import urllib.parse

import moto
import pytest
from sqlalchemy.exc import InvalidRequestError

import massgov.pfml.db
from massgov.pfml.db import DbConfig, get_config, make_connection_uri
from massgov.pfml.db.models.employees import TaxIdentifier


class DummyConnectionInfo:
    def __init__(self, ssl_in_use, attributes):
        self.ssl_in_use = ssl_in_use
        self.attributes = attributes
        self.ssl_attribute_names = tuple(attributes.keys())

    def ssl_attribute(self, name):
        return self.attributes[name]


def test_verify_ssl(caplog):
    caplog.set_level(logging.INFO)  # noqa: B1

    conn_info = DummyConnectionInfo(True, {"protocol": "ABCv3", "key_bits": "64", "cipher": "XYZ"})
    massgov.pfml.db.verify_ssl(conn_info)

    assert caplog.messages == [
        "database connection is using SSL: protocol ABCv3, key_bits 64, cipher XYZ"
    ]
    assert caplog.records[0].levelname == "INFO"


def test_verify_ssl_not_in_use(caplog):
    caplog.set_level(logging.INFO)  # noqa: B1

    conn_info = DummyConnectionInfo(False, {})
    massgov.pfml.db.verify_ssl(conn_info)

    assert caplog.messages == ["database connection is not using SSL"]
    assert caplog.records[0].levelname == "WARNING"


def test_make_connection_uri():
    assert (
        make_connection_uri(
            DbConfig(
                host="localhost",
                name="dbname",
                username="foo",
                password="bar",
                schema="public",
                port="5432",
            )
        )
        == "postgresql://foo:bar@localhost:5432/dbname?options=-csearch_path=public"
    )

    assert (
        make_connection_uri(
            DbConfig(
                host="localhost",
                name="dbname",
                username="foo",
                password=None,
                schema="public",
                port="5432",
            )
        )
        == "postgresql://foo@localhost:5432/dbname?options=-csearch_path=public"
    )


def test_get_iam_auth_token(reset_aws_env_vars):
    with moto.mock_rds():
        db_config = get_config()

        iam_token = massgov.pfml.db.get_iam_auth_token(db_config)

        assert iam_token is not None

        # IAM auth tokens are formatted like a url, but don't have a schema
        # part, so add a dummy `aws://` for the url parse
        password_parts = urllib.parse.urlparse(f"aws://{iam_token}")
        assert password_parts.netloc == f"{db_config.host}:{db_config.port}"

        password_query_parts = urllib.parse.parse_qs(password_parts.query)
        assert password_query_parts["Action"][0] == "connect"
        assert password_query_parts["DBUser"][0] == db_config.username
        assert len(password_query_parts["X-Amz-Algorithm"]) != 0
        assert len(password_query_parts["X-Amz-Credential"]) != 0
        assert len(password_query_parts["X-Amz-Date"]) != 0
        assert len(password_query_parts["X-Amz-Expires"]) != 0
        assert len(password_query_parts["X-Amz-SignedHeaders"]) != 0
        assert len(password_query_parts["X-Amz-Security-Token"]) != 0
        assert len(password_query_parts["X-Amz-Signature"]) != 0


def test_get_connection_parameters(reset_aws_env_vars, delete_db_env_vars, monkeypatch):
    db_config = get_config()
    conn_params = massgov.pfml.db.get_connection_parameters(db_config)

    assert conn_params == dict(
        host=db_config.host,
        dbname=db_config.name,
        user=db_config.username,
        password=db_config.password,
        port=db_config.port,
        options=f"-c search_path={db_config.schema}",
        connect_timeout=3,
    )


def test_get_connection_parameters_not_local_no_set_password(
    reset_aws_env_vars, delete_db_env_vars, monkeypatch
):
    monkeypatch.setenv("ENVIRONMENT", "not-local")

    with moto.mock_rds():
        db_config = get_config()

        assert db_config.use_iam_auth is True

        conn_params = massgov.pfml.db.get_connection_parameters(db_config)

        assert conn_params["sslmode"] == "require"
        assert conn_params["password"]


def simulate_insert_duplicate_row(db_session):
    TEST_SSN = "1234567890"
    tax_id_1 = TaxIdentifier(
        tax_identifier_id="638309eb-1981-4a13-aa35-8f1eb6f52e75", tax_identifier=TEST_SSN
    )
    tax_id_2 = TaxIdentifier(
        tax_identifier_id="c28b9a52-cd53-445f-b3eb-a15a05ed287f", tax_identifier=TEST_SSN
    )
    db_session.add(tax_id_1)
    db_session.add(tax_id_2)
    db_session.flush()


def simulate_rollback(db_session):
    try:
        simulate_insert_duplicate_row(db_session)
    except Exception:
        db_session.commit()


def test_db_doesnt_log_sql_params(test_db_session, verbose_test_db_session):
    ERROR_PARAMETERS = "[parameters: ({'tax_identifier_id': '638309eb-1981-4a13-aa35-8f1eb6f52e75', 'tax_identifier': '1234567890'}, {'tax_identifier_id': 'c28b9a52-cd53-445f-b3eb-a15a05ed287f', 'tax_identifier': '1234567890'})]"

    with pytest.raises(InvalidRequestError) as verbose_e:
        simulate_rollback(verbose_test_db_session)

    verbose_error_str = verbose_e.exconly()

    assert ERROR_PARAMETERS in verbose_error_str

    with pytest.raises(InvalidRequestError) as silent_e:
        simulate_rollback(test_db_session)

    silent_error_str: str = silent_e.exconly()

    assert ERROR_PARAMETERS not in silent_error_str
