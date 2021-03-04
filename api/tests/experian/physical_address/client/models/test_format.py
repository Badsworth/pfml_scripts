from massgov.pfml.experian.physical_address.client.models.format import (
    AddressFormatV1Address,
    AddressFormatV1Components,
    AddressFormatV1DPV,
    AddressFormatV1Metadata,
    AddressFormatV1Response,
    AddressFormatV1Result,
    Confidence,
)


def test_format_result_minimum():
    response_body = "{}"
    result = AddressFormatV1Response.parse_raw(response_body)
    assert result == AddressFormatV1Response()


def test_format_result():
    response_body = '{"error": null, "result": {"global_address_key": "aWQ9MTAwIENhbWJyaWRnZSBTdCBTdGUgMTAxLCBCb3N0b24gTUEgMDIxMTQsIFVuaXRlZCBTdGF0ZXMgT2YgQW1lcmljYX5hbHRfa2V5PXwxMDAgQ2FtYnJpZGdlIFN0IFN0ZSAxMDF8fEJvc3RvbixNQSwwMjExNC0yNTc5fmRhdGFzZXQ9VVNBX1BBRn5mb3JtYXRfa2V5PVVTQSQkMzU2Mzg0YmQtYWY2NC00MWViLTg1NTMtY2M1YjhlOTcwYmJmJDEwMCQxMDEk", "confidence": "Verified match", "address": {"address_line_1": "100 Cambridge St", "address_line_2": "Ste 101", "address_line_3": "", "locality": "Boston", "region": "MA", "postal_code": "02114-2579", "country": "UNITED STATES OF AMERICA"}, "components": {"language": "en-GB", "country_name": "United States Of America", "country_iso_3": "USA", "postal_code": {"full_name": "02114-2579", "primary": "02114", "secondary": "2579"}, "delivery_service": null, "secondary_delivery_service": null, "sub_building": {"name": null, "entrance": null, "floor": null, "door": {"full_name": "Ste 101", "type": "Ste", "value": "101"}}, "building": {"building_name": null, "building_number": "100", "secondary_number": null, "allotment_number": null}, "organization": null, "street": {"full_name": "Cambridge St", "prefix": null, "name": "Cambridge", "type": "St", "suffix": null}, "secondary_street": null, "route_service": null, "locality": {"region": {"name": null, "code": "MA", "description": null}, "sub_region": {"name": "Suffolk", "code": null, "description": null}, "town": {"name": "Boston", "code": null, "description": null}, "district": null, "sub_district": null}}}, "metadata": {"address_info": null, "dpv": {"cmra_indicator": "N", "seed_indicator": " ", "dpv_indicator": "Y", "footnotes": ["AA", "BB"], "vacancy_indicator": "N", "no_stats_indicator": "N", "pbsa_indicator": "N"}}}'
    result = AddressFormatV1Response.parse_raw(response_body)
    assert result == AddressFormatV1Response(
        error=None,
        result=AddressFormatV1Result(
            global_address_key="aWQ9MTAwIENhbWJyaWRnZSBTdCBTdGUgMTAxLCBCb3N0b24gTUEgMDIxMTQsIFVuaXRlZCBTdGF0ZXMgT2YgQW1lcmljYX5hbHRfa2V5PXwxMDAgQ2FtYnJpZGdlIFN0IFN0ZSAxMDF8fEJvc3RvbixNQSwwMjExNC0yNTc5fmRhdGFzZXQ9VVNBX1BBRn5mb3JtYXRfa2V5PVVTQSQkMzU2Mzg0YmQtYWY2NC00MWViLTg1NTMtY2M1YjhlOTcwYmJmJDEwMCQxMDEk",
            confidence=Confidence.VERIFIED_MATCH,
            address=AddressFormatV1Address(
                address_line_1="100 Cambridge St",
                address_line_2="Ste 101",
                address_line_3="",
                locality="Boston",
                region="MA",
                postal_code="02114-2579",
                country="UNITED STATES OF AMERICA",
            ),
            components=AddressFormatV1Components.parse_obj(
                {
                    "language": "en-GB",
                    "country_name": "United States Of America",
                    "country_iso_3": "USA",
                    "postal_code": {
                        "full_name": "02114-2579",
                        "primary": "02114",
                        "secondary": "2579",
                    },
                    "delivery_service": None,
                    "secondary_delivery_service": None,
                    "sub_building": {
                        "name": None,
                        "entrance": None,
                        "floor": None,
                        "door": {"full_name": "Ste 101", "type": "Ste", "value": "101"},
                    },
                    "building": {
                        "building_name": None,
                        "building_number": "100",
                        "secondary_number": None,
                        "allotment_number": None,
                    },
                    "organization": None,
                    "street": {
                        "full_name": "Cambridge St",
                        "prefix": None,
                        "name": "Cambridge",
                        "type": "St",
                        "suffix": None,
                    },
                    "secondary_street": None,
                    "route_service": None,
                    "locality": {
                        "region": {"name": None, "code": "MA", "description": None},
                        "sub_region": {"name": "Suffolk", "code": None, "description": None},
                        "town": {"name": "Boston", "code": None, "description": None},
                        "district": None,
                        "sub_district": None,
                    },
                }
            ),
        ),
        metadata=AddressFormatV1Metadata(
            address_info=None,
            dpv=AddressFormatV1DPV(
                cmra_indicator="N",
                seed_indicator=" ",
                dpv_indicator="Y",
                footnotes=["AA", "BB"],
                vacancy_indicator="N",
                no_stats_indicator="N",
                pbsa_indicator="N",
            ),
        ),
    )
