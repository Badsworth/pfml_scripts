import massgov.pfml.experian.physical_address.client.models.common as models_common

ERROR_BODY_WITH_CAPITAL_KEYS = '{"Type": "Please contact Experian Data Quality or visit edq.com.", "Title": "Error converting value \\"foo\\" to type \'Experian.Capture.AddressApi.Service.Models.V3.SearchInput\'. Path \'\', line 1, position 112.", "Detail": "Could not cast or convert from System.String to Experian.Capture.AddressApi.Service.Models.V3.SearchInput.", "Instance": "Newtonsoft.Json"}'
ERROR_BODY_WITH_LOWER_KEYS = '{"type": "Please contact Experian Data Quality or visit edq.com.", "title": "Error converting value \\"foo\\" to type \'Experian.Capture.AddressApi.Service.Models.V3.SearchInput\'. Path \'\', line 1, position 112.", "detail": "Could not cast or convert from System.String to Experian.Capture.AddressApi.Service.Models.V3.SearchInput.", "instance": "Newtonsoft.Json"}'


def test_response_error_handles_capitalized_keys():
    models_common.ResponseError.parse_raw(ERROR_BODY_WITH_CAPITAL_KEYS)


def test_response_error_handles_lower_keys():
    models_common.ResponseError.parse_raw(ERROR_BODY_WITH_LOWER_KEYS)
