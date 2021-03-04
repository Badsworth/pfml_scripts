import abc
from typing import Optional

from .models import AddressFormatV1Response, AddressSearchV1Request, AddressSearchV1Response


class BaseClient(abc.ABC, metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def search(
        self,
        req: AddressSearchV1Request,
        *,
        reference_id: Optional[str] = None,
        timeout_seconds: Optional[int] = None,
    ) -> AddressSearchV1Response:
        """POSTs a partial address to the service to be completed.

        Experian docs: https://api.experianaperture.io/docs/index.html?urls.primaryName=AddressSearch

        Args:
            req: The request body
            reference_id: Optional identifier that will be returned in the
                response to help you track the request.
            timeout_seconds: Maximum time you are prepared to wait for a
                response, expressed in seconds. Acceptable values: 2-15. If a
                timeout occurs, an HTTP status code of 408 - Request Timeout
                will be returned.

        Examples:
            Called like::

                client.search(
                    AddressSearchV1Request(
                        country_iso="USA",
                        components=AddressSearchV1InputComponent(
                            unspecified=["100 Cambridge St, Ste 101, Boston MA 02114"]
                        ),
                    )
                )

            Return value would be::

                AddressSearchV1Response(
                    error=None,
                    result=AddressSearchV1Result(
                        more_results_available=False,
                        confidence=Confidence.VERIFIED_MATCH,
                        suggestions=[
                            AddressSearchV1MatchedResult(
                                global_address_key="aWQ9MTAwIENhbWJyaWRnZSBTdCBTdGUgMTAxLCBCb3N0b24gTUEgMDIxMTQsIFVuaXRlZCBTdGF0ZXMgT2YgQW1lcmljYX5hbHRfa2V5PXwxMDAgQ2FtYnJpZGdlIFN0IFN0ZSAxMDF8fEJvc3RvbixNQSwwMjExNC0yNTc5fmRhdGFzZXQ9VVNBX1BBRn5mb3JtYXRfa2V5PVVTQSQkMzU2Mzg0YmQtYWY2NC00MWViLTg1NTMtY2M1YjhlOTcwYmJmJDEwMCQxMDEk",
                                text="100 Cambridge St Ste 101, Boston MA 02114",
                                matched=[
                                    [36, 41],
                                    [33, 35],
                                    [26, 32],
                                    [21, 24],
                                    [17, 20],
                                    [14, 16],
                                    [4, 13],
                                    [0, 3],
                                ],
                                format="https://api.experianaperture.io/address/format/v1/aWQ9MTAwIENhbWJyaWRnZSBTdCBTdGUgMTAxLCBCb3N0b24gTUEgMDIxMTQsIFVuaXRlZCBTdGF0ZXMgT2YgQW1lcmljYX5hbHRfa2V5PXwxMDAgQ2FtYnJpZGdlIFN0IFN0ZSAxMDF8fEJvc3RvbixNQSwwMjExNC0yNTc5fmRhdGFzZXQ9VVNBX1BBRn5mb3JtYXRfa2V5PVVTQSQkMzU2Mzg0YmQtYWY2NC00MWViLTg1NTMtY2M1YjhlOTcwYmJmJDEwMCQxMDEkflFMPTQyfmdlbz1GYWxzZQ",
                                dataset=None,
                            )
                        ],
                    ),
                )
        """

    @abc.abstractmethod
    def format(
        self,
        global_address_key: str,
        *,
        add_metadata: Optional[bool] = True,
        add_components: Optional[bool] = True,
        reference_id: Optional[str] = None,
        timeout_seconds: Optional[int] = None,
    ) -> AddressFormatV1Response:
        """GETs structured address data.

        Experian docs: https://api.experianaperture.io/docs/index.html?urls.primaryName=AddressFormat

        Args:
            global_address_key: The ID of the address received as part of a
                previous fielded or intuitive search. Can be the global address
                key or the global_format_key.
            add_metadata: Specifies if the response should return additional
                dataset-specific values, such as verbose validation data.
            add_components: Specifies if the response should contain the address
                broken down into its components.
            reference_id: Optional identifier that will be returned in the
                response to help you track the request.
            timeout_seconds: Maximum time you are prepared to wait for a
                response, expressed in seconds. Acceptable values: 2-15. If a
                timeout occurs, an HTTP status code of 408 - Request Timeout
                will be returned.

        Examples:
            Called like::

                client.format("aWQ9MTAwIENhbWJyaWRnZSBTdCBTdGUgMTAxLCBCb3N0b24gTUEgMDIxMTQsIFVuaXRlZCBTdGF0ZXMgT2YgQW1lcmljYX5hbHRfa2V5PXwxMDAgQ2FtYnJpZGdlIFN0IFN0ZSAxMDF8fEJvc3RvbixNQSwwMjExNC0yNTc5fmRhdGFzZXQ9VVNBX1BBRn5mb3JtYXRfa2V5PVVTQSQkMzU2Mzg0YmQtYWY2NC00MWViLTg1NTMtY2M1YjhlOTcwYmJmJDEwMCQxMDEk")

            Return value would be::

                AddressFormatV1Response(
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
                        components=AddressFormatV1Components(
                            language="en-GB",
                            country_name="United States Of America",
                            country_iso_3="USA",
                            postal_code=AddressFormatV1PostalCodeElement(
                                full_name="02114-2579", primary="02114", secondary="2579"
                            ),
                            delivery_service=None,
                            secondary_delivery_service=None,
                            sub_building=AddressFormatV1SubBuildingComponents(
                                name=None,
                                entrance=None,
                                floor=None,
                                door=AddressFormatV1SubBuildingItem(full_name="Ste 101", type="Ste", value="101"),
                            ),
                            building=AddressFormatV1BuildingComponents(
                                building_name=None,
                                building_number="100",
                                secondary_number=None,
                                allotment_number=None,
                            ),
                            organization=None,
                            street=AddressFormatV1StreetComponents(
                                full_name="Cambridge St", prefix=None, name="Cambridge", type="St", suffix=None
                            ),
                            secondary_street=None,
                            route_service=None,
                            locality=AddressFormatV1LocalityComponents(
                                region=AddressFormatV1LocalityItem(name=None, code="MA", description=None),
                                sub_region=AddressFormatV1LocalityItem(name="Suffolk", code=None, description=None),
                                town=AddressFormatV1LocalityItem(name="Boston", code=None, description=None),
                                district=None,
                                sub_district=None,
                            ),
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
        """
