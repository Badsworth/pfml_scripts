NOT_NONE = "NOT NONE"


def validate_field(value, expected_value):
    if expected_value is NOT_NONE:
        assert expected_value is not None
    else:
        assert expected_value == value


def validate_error_response(
    response,
    status_code,
    message=NOT_NONE,
    errors=NOT_NONE,
    meta_method=NOT_NONE,
    meta_resource=NOT_NONE,
):
    """Validate that an error object is properly constructed with fields filled out (ie. created by response_util.error_response)"""
    assert response.status_code == status_code

    response_json = response.get_json()
    validate_field(response_json["message"], message)
    validate_field(response_json["errors"], errors)
    validate_field(response_json["meta"]["method"], meta_method)
    validate_field(response_json["meta"]["resource"], meta_resource)
