#
# Tests for massgov.pfml.util.logging.network.
#

import logging  # noqa: B1
import socket

import massgov.pfml.util.logging.network

TEST_ADDR_INFO = [
    (socket.AF_INET6, socket.SOCK_STREAM, 6, "", ("::1", 8001, 0, 0)),
    (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 8001)),
]

TEST_PEER_CERT = {
    "subject": ((("commonName", "test.host"),),),
    "issuer": (
        (("countryName", "US"),),
        (("organizationName", "PFML"),),
        (("organizationalUnitName", "API"),),
        (("commonName", "PFML API"),),
    ),
    "version": 3,
    "serialNumber": "00001111000022220000333300004444",
    "notBefore": "Jul 22 00:00:00 2020 GMT",
    "notAfter": "Aug 22 12:00:00 2021 GMT",
    "subjectAltName": (("DNS", "other.test.host"),),
}


class FakeSocket:
    def getpeername(self):
        return "127.0.0.1", 443


class FakeSSLSocket(FakeSocket):
    def getpeercert(self):
        return TEST_PEER_CERT


class FakeConnection:
    def __init__(self):
        self.host = "localhost"
        self.port = 8080
        self.sock = FakeSocket()


class FakeSSLConnection:
    def __init__(self):
        self.host = "localhost"
        self.port = 8443
        self.sock = FakeSSLSocket()


def test_patch_connect_ssl(caplog, monkeypatch):
    caplog.set_level(logging.INFO)  # noqa: B1
    monkeypatch.setattr("socket.getaddrinfo", lambda host, port, proto: TEST_ADDR_INFO)

    def connect(self):
        pass

    patched_connect = massgov.pfml.util.logging.network.patch_connect(connect)

    patched_connect(FakeSSLConnection())

    assert [(r.funcName, r.levelname, r.message) for r in caplog.records] == [
        (
            "connect_log",
            "INFO",
            "getaddrinfo localhost:8443 => [('::1', 8001, 0, 0), ('127.0.0.1', 8001)]",
        ),
        ("connect_log", "INFO", "connected localhost:8443 => ('127.0.0.1', 443)"),
    ]
    assert caplog.records[1].cert == TEST_PEER_CERT


def test_patch_connect_not_ssl(caplog, monkeypatch):
    caplog.set_level(logging.INFO)  # noqa: B1
    monkeypatch.setattr("socket.getaddrinfo", lambda host, port, proto: TEST_ADDR_INFO)

    def connect(self):
        pass

    patched_connect = massgov.pfml.util.logging.network.patch_connect(connect)

    patched_connect(FakeConnection())

    assert [(r.funcName, r.levelname, r.message) for r in caplog.records] == [
        (
            "connect_log",
            "INFO",
            "getaddrinfo localhost:8080 => [('::1', 8001, 0, 0), ('127.0.0.1', 8001)]",
        ),
        ("connect_log", "INFO", "connected localhost:8080 => ('127.0.0.1', 443)"),
    ]
    assert not hasattr(caplog.records[1], "cert")
