#
# Tests for massgov.pfml.util.logging.access.
#

import logging  # noqa: B1

import werkzeug.datastructures

from massgov.pfml.util.logging import access


class FakeRequest:
    def __init__(
        self,
        method,
        path,
        user_agent="Mozilla/5.0 (X11; Linux x86_64; rv:77.0) Gecko/20100101 Firefox/77.0",
    ):
        self.method = method
        self.path = path
        self.full_path = path + "?"
        self.remote_addr = "4.5.6.7"
        self.headers = werkzeug.datastructures.Headers(
            [("Content-Type", "text/plain"), ("User-Agent", user_agent)]
        )
        self.content_length = 64
        self.data = b'{"hello": "world"}'
        self.form = werkzeug.datastructures.ImmutableMultiDict()
        self.json = {"hello": "world"}


class FakeResponse:
    def __init__(self, status_code):
        self.status_code = status_code
        self.content_length = 33300
        self.content_type = "text/html"
        self.data = b'{"status": "ok"}'


def simulate_requests(full_error_logs=False):
    access.access_log(FakeRequest("GET", "/one/1"), FakeResponse(200), full_error_logs)
    access.access_log(FakeRequest("POST", "/two/2"), FakeResponse(404), full_error_logs)
    access.access_log(FakeRequest("GET", "/v1/status"), FakeResponse(200), full_error_logs)
    access.access_log(FakeRequest("GET", "/v1/status"), FakeResponse(500), full_error_logs)
    # 5th request should not be logged as it's a successful load balancer health check:
    access.access_log(
        FakeRequest("GET", "/v1/status", "ELB-HealthChecker/2.0"),
        FakeResponse(200),
        full_error_logs,
    )
    access.access_log(
        FakeRequest("GET", "/v1/status", "ELB-HealthChecker/2.0"),
        FakeResponse(500),
        full_error_logs,
    )


def test_access_log(caplog):
    caplog.set_level(logging.INFO)  # noqa: B1

    simulate_requests()

    assert [(r.funcName, r.levelname, r.message, r.status_code) for r in caplog.records] == [
        ("access_log_success", "INFO", "200 GET /one/1?", 200),
        ("access_log_error", "WARNING", "404 POST /two/2?", 404),
        ("access_log_success", "INFO", "200 GET /v1/status?", 200),
        ("access_log_error", "WARNING", "500 GET /v1/status?", 500),
        # Note: 5th request not logged as it's a successful load balancer health check.
        ("access_log_error", "WARNING", "500 GET /v1/status?", 500),
    ]
    assert all([r.name == "massgov.pfml.util.logging.access" for r in caplog.records])


def test_full_request_data_not_logged_by_default(caplog):
    caplog.set_level(logging.INFO)  # noqa: B1

    simulate_requests()

    for record in caplog.records:
        keys = set(vars(record).keys())
        assert {"request_data", "request_form", "request_json", "response_data"}.isdisjoint(keys)


def test_full_request_data_logged_when_enabled(caplog):
    caplog.set_level(logging.INFO)  # noqa: B1

    simulate_requests(full_error_logs=True)

    for record in caplog.records:
        if 400 <= record.status_code:
            keys = set(vars(record).keys())
            assert {"request_data", "request_form", "request_json", "response_data"}.issubset(keys)


def test_is_load_balancer_health_check():
    assert access.is_load_balancer_health_check(
        FakeRequest("GET", "/v1/status", "ELB-HealthChecker/2.0")
    )
    assert not access.is_load_balancer_health_check(FakeRequest("GET", "/v1/status", "Mozilla/5.0"))
    assert not access.is_load_balancer_health_check(
        FakeRequest("GET", "/", "ELB-HealthChecker/2.0")
    )
