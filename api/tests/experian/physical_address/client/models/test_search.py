from massgov.pfml.experian.physical_address.client.models.search import (
    AddressSearchV1InputComponent,
    AddressSearchV1MatchedResult,
    AddressSearchV1Request,
    AddressSearchV1Response,
    AddressSearchV1Result,
    Confidence,
)


def test_search_request():
    address_search = AddressSearchV1Request(
        country_iso="USA", components=AddressSearchV1InputComponent(unspecified=["foo"])
    )

    assert (
        address_search.json()
        == '{"country_iso": "USA", "components": {"unspecified": ["foo"]}, "location": null, "dataset": null}'
    )


def test_search_result_minimum():
    response_body = "{}"
    result = AddressSearchV1Response.parse_raw(response_body)
    assert result == AddressSearchV1Response()


def test_search_result():
    response_body = '{"error": null, "result": {"more_results_available": false, "confidence": "Verified match", "suggestions": [{"global_address_key": "baz", "text": "bar", "matched": [[0, 1]], "format": "https://api.experianaperture.io/address/format/v1/baz", "dataset": null}]}}'
    result = AddressSearchV1Response.parse_raw(response_body)
    assert result == AddressSearchV1Response(
        result=AddressSearchV1Result(
            more_results_available=False,
            confidence=Confidence.VERIFIED_MATCH,
            suggestions=[
                AddressSearchV1MatchedResult(
                    global_address_key="baz",
                    text="bar",
                    matched=[[0, 1]],
                    format="https://api.experianaperture.io/address/format/v1/baz",
                )
            ],
        )
    )
