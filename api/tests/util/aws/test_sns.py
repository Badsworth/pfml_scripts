from unittest import mock
from unittest.mock import MagicMock

import boto3
import pytest

import massgov.pfml.util.aws.sns as sns_util


@pytest.fixture
def mock_sns():
    mock_sns = MagicMock()
    mock_sns.check_if_phone_number_is_opted_out = MagicMock()
    mock_sns.opt_in_phone_number = MagicMock()
    return mock_sns


class TestPhoneNumberOptOut:
    @mock.patch("massgov.pfml.util.aws.sns.create_sns_client")
    def test_success(self, mock_create_sns, mock_sns):
        mock_create_sns.return_value = mock_sns

        sns_util.check_phone_number_opt_out("+15109283075")

        mock_sns.check_if_phone_number_is_opted_out.assert_called_with(phoneNumber="+15109283075")

    @mock.patch("massgov.pfml.util.aws.sns.create_sns_client")
    def test_invalid_parameter_raises_exception(self, mock_create_sns, mock_sns, caplog):
        mock_create_sns.return_value = mock_sns

        invalid_param = boto3.client("sns", "us-east-1").exceptions.InvalidParameterException(
            error_response={"Error": {"Code": "InvalidParameter"}}, operation_name=""
        )

        mock_check_phone = mock_sns.check_if_phone_number_is_opted_out
        mock_check_phone.side_effect = invalid_param

        with pytest.raises(Exception):
            sns_util.check_phone_number_opt_out("")

        assert "Invalid parameter in request" in caplog.text


class TestOptInPhoneNumber:
    @mock.patch("massgov.pfml.util.aws.sns.create_sns_client")
    def test_success(self, mock_create_sns, mock_sns):
        mock_create_sns.return_value = mock_sns

        sns_util.opt_in_phone_number("+15109283075")

        mock_sns.opt_in_phone_number.assert_called_with(phoneNumber="+15109283075")

    @mock.patch("massgov.pfml.util.aws.sns.create_sns_client")
    def test_invalid_parameter_raises_exception(self, mock_create_sns, mock_sns, caplog):
        mock_create_sns.return_value = mock_sns

        invalid_param = boto3.client("sns", "us-east-1").exceptions.InvalidParameterException(
            error_response={"Error": {"Code": "InvalidParameter"}}, operation_name=""
        )

        mock_opt_in = mock_sns.opt_in_phone_number
        mock_opt_in.side_effect = invalid_param

        with pytest.raises(Exception):
            sns_util.opt_in_phone_number("")

        assert "Invalid parameter in request" in caplog.text

    @mock.patch("massgov.pfml.util.aws.sns.create_sns_client")
    def test_throttled_exception_raises_exception(self, mock_create_sns, mock_sns, caplog):
        mock_create_sns.return_value = mock_sns

        throttled = boto3.client("sns", "us-east-1").exceptions.ThrottledException(
            error_response={"Error": {"Code": "Throttled"}}, operation_name=""
        )

        mock_opt_in = mock_sns.opt_in_phone_number
        mock_opt_in.side_effect = throttled

        with pytest.raises(Exception):
            sns_util.opt_in_phone_number("")

        assert "Too many requests" in caplog.text
