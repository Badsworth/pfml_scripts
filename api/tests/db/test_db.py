#
# Tests for massgov.pfml.db.
#

import logging  # noqa: B1

import massgov.pfml.db
from massgov.pfml.db import DbConfig, make_connection_uri


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
