#
# Request access logging.
#

import werkzeug

import massgov.pfml.util.logging

logger = massgov.pfml.util.logging.get_logger(__name__)


def access_log_start(request):
    if is_load_balancer_health_check(request):
        return

    logger.info(
        "Started %s %s",
        request.method,
        request.full_path,
        extra={"remote_addr": request.remote_addr},
    )


def access_log_end(request, response, response_time_ms, full_error_logs=False):
    """Log a request, excluding load balancer requests that fill the logs."""
    if 400 <= response.status_code:
        access_log_error(request, response, response_time_ms, full_error_logs)
    else:
        if is_load_balancer_health_check(request):
            return
        access_log_success(request, response, response_time_ms)


def access_log_success(request, response, response_time_ms):
    """Log basic attributes of a successful request. Request and response data is not logged."""
    logger.info(
        "%s %s %s",
        response.status_code,
        request.method,
        request.full_path,
        extra={
            "remote_addr": request.remote_addr,
            "response_length": response.content_length,
            "response_type": response.content_type,
            "status_code": response.status_code,
            "response_time_ms": response_time_ms,
        },
    )


def access_log_error(request, response, response_time_ms, full_data=False):
    """Log data for a failed request. Full request and response data is logged
    in non-prod environments for debugging and reproducing of errors, which can be
    difficult to do otherwise for integrations like FINEOS."""
    headers = werkzeug.datastructures.Headers(request.headers)
    headers.remove("Authorization")
    extra = {
        "remote_addr": request.remote_addr,
        "request_headers": headers,
        "request_length": request.content_length,
        "response_length": response.content_length,
        "response_type": response.content_type,
        "response_time_ms": response_time_ms,
        "status_code": response.status_code,
    }

    # Don't log requests to our /users endpoint to avoid logging passwords
    if full_data and request.path != "/v1/users":
        extra["request_data"] = request.data
        extra["request_form"] = request.form.to_dict(flat=False)
        extra["request_json"] = request.get_json(silent=True)

    if full_data:
        extra["response_data"] = response.data

    logger.warning("%s %s %s", response.status_code, request.method, request.full_path, extra=extra)


def is_load_balancer_health_check(request):
    """Test if the request comes from a load balancer."""
    return request.path == "/v1/status" and request.headers.get("User-Agent", "").startswith(
        "ELB-HealthChecker/"
    )
