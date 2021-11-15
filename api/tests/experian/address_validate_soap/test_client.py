import pytest

import massgov.pfml.experian.address_validate_soap.models as sm
from massgov.pfml.experian.address_validate_soap.caller import ApiCaller
from massgov.pfml.experian.address_validate_soap.client import Client

single_standard_response = pytest.param(
    {
        "header": {"information_header": {"StateTransition": "SearchResults", "CreditsUsed": 1}},
        "body": {
            "QAPicklist": None,
            "QAAddress": {
                "AddressLine": [
                    {
                        "Label": None,
                        "Line": None,
                        "DataplusGroup": [],
                        "LineContent": "Address",
                        "Overflow": "false",
                        "Truncated": "false",
                    },
                    {
                        "Label": None,
                        "Line": "333 Foo St",
                        "DataplusGroup": [],
                        "LineContent": "Address",
                        "Overflow": "false",
                        "Truncated": "false",
                    },
                    {
                        "Label": None,
                        "Line": "Washington DC  12345-6789",
                        "DataplusGroup": [],
                        "LineContent": "Address",
                        "Overflow": "false",
                        "Truncated": "false",
                    },
                ],
                "Overflow": "false",
                "Truncated": "false",
                "DPVStatus": "DPVConfirmed",
                "MissingSubPremise": "false",
            },
            "VerificationFlags": {
                "BldgFirmNameChanged": None,
                "PrimaryNumberChanged": None,
                "StreetCorrected": None,
                "RuralRteHighwayContractMatched": None,
                "CityNameChanged": None,
                "CityAliasMatched": None,
                "StateProvinceChanged": None,
                "PostCodeCorrected": True,
                "SecondaryNumRetained": None,
                "IdenPreStInfoRetained": None,
                "GenPreStInfoRetained": None,
                "PostStInfoRetained": None,
            },
            "VerifyLevel": "Verified",
        },
    },
    sm.SearchResponse(
        address=sm.SearchAddress(
            address_lines=[
                sm.SearchAddressLine(
                    label=None,
                    line=None,
                    dataplus_group=[],
                    overflow=False,
                    truncated=False,
                    line_content=sm.SearchAddressLineContentType.ADDRESS,
                ),
                sm.SearchAddressLine(
                    label=None,
                    line="333 Foo St",
                    dataplus_group=[],
                    overflow=False,
                    truncated=False,
                    line_content=sm.SearchAddressLineContentType.ADDRESS,
                ),
                sm.SearchAddressLine(
                    label=None,
                    line="Washington DC  12345-6789",
                    dataplus_group=[],
                    overflow=False,
                    truncated=False,
                    line_content=sm.SearchAddressLineContentType.ADDRESS,
                ),
            ],
            overflow=False,
            truncated=False,
            dpv_status=sm.DPVStatus.CONFIRMED,
            missing_sub_premise=False,
        ),
        picklist=None,
        verification_flags=sm.SearchVerificationFlags(
            bldg_firm_name_changed=None,
            primary_number_changed=None,
            street_corrected=None,
            rural_rte_highway_contract_matched=None,
            city_name_changed=None,
            city_alias_matched=None,
            state_province_changed=None,
            post_code_corrected=True,
            secondary_num_retained=None,
            iden_pre_st_info_retained=None,
            gen_pre_st_info_retained=None,
            post_st_info_retained=None,
        ),
        verify_level=sm.VerifyLevel.VERIFIED,
    ),
    id="single_standard_response",
)

database_layout_iso2_response = pytest.param(
    {
        "header": {"information_header": {"StateTransition": "SearchResults", "CreditsUsed": 1}},
        "body": {
            "QAPicklist": None,
            "QAAddress": {
                "AddressLine": [
                    {
                        "Label": None,
                        "Line": "333 Foo St",
                        "DataplusGroup": [],
                        "LineContent": "None",
                        "Overflow": "false",
                        "Truncated": "false",
                    },
                    {
                        "Label": None,
                        "Line": None,
                        "DataplusGroup": [],
                        "LineContent": "None",
                        "Overflow": "false",
                        "Truncated": "false",
                    },
                    {
                        "Label": None,
                        "Line": None,
                        "DataplusGroup": [],
                        "LineContent": "None",
                        "Overflow": "false",
                        "Truncated": "false",
                    },
                    {
                        "Label": "City name",
                        "Line": "Washington",
                        "DataplusGroup": [],
                        "LineContent": "Address",
                        "Overflow": "false",
                        "Truncated": "false",
                    },
                    {
                        "Label": "State code",
                        "Line": "DC",
                        "DataplusGroup": [],
                        "LineContent": "Address",
                        "Overflow": "false",
                        "Truncated": "false",
                    },
                    {
                        "Label": None,
                        "Line": "12345-6789",
                        "DataplusGroup": [],
                        "LineContent": "Address",
                        "Overflow": "false",
                        "Truncated": "false",
                    },
                    {
                        "Label": "Two character ISO country code",
                        "Line": "US",
                        "DataplusGroup": [],
                        "LineContent": "Address",
                        "Overflow": "false",
                        "Truncated": "false",
                    },
                ],
                "Overflow": "false",
                "Truncated": "false",
                "DPVStatus": "DPVConfirmed",
                "MissingSubPremise": "false",
            },
            "VerificationFlags": {
                "BldgFirmNameChanged": None,
                "PrimaryNumberChanged": None,
                "StreetCorrected": None,
                "RuralRteHighwayContractMatched": None,
                "CityNameChanged": None,
                "CityAliasMatched": None,
                "StateProvinceChanged": None,
                "PostCodeCorrected": True,
                "SecondaryNumRetained": None,
                "IdenPreStInfoRetained": None,
                "GenPreStInfoRetained": None,
                "PostStInfoRetained": None,
            },
            "VerifyLevel": "Verified",
        },
    },
    sm.SearchResponse(
        address=sm.SearchAddress(
            address_lines=[
                sm.SearchAddressLine(
                    label=None,
                    line="333 Foo St",
                    dataplus_group=[],
                    overflow=False,
                    truncated=False,
                    line_content=sm.SearchAddressLineContentType.NONE,
                ),
                sm.SearchAddressLine(
                    label=None,
                    line=None,
                    dataplus_group=[],
                    overflow=False,
                    truncated=False,
                    line_content=sm.SearchAddressLineContentType.NONE,
                ),
                sm.SearchAddressLine(
                    label=None,
                    line=None,
                    dataplus_group=[],
                    overflow=False,
                    truncated=False,
                    line_content=sm.SearchAddressLineContentType.NONE,
                ),
                sm.SearchAddressLine(
                    label="City name",
                    line="Washington",
                    dataplus_group=[],
                    overflow=False,
                    truncated=False,
                    line_content=sm.SearchAddressLineContentType.ADDRESS,
                ),
                sm.SearchAddressLine(
                    label="State code",
                    line="DC",
                    dataplus_group=[],
                    overflow=False,
                    truncated=False,
                    line_content=sm.SearchAddressLineContentType.ADDRESS,
                ),
                sm.SearchAddressLine(
                    label=None,
                    line="12345-6789",
                    dataplus_group=[],
                    overflow=False,
                    truncated=False,
                    line_content=sm.SearchAddressLineContentType.ADDRESS,
                ),
                sm.SearchAddressLine(
                    label="Two character ISO country code",
                    line="US",
                    dataplus_group=[],
                    overflow=False,
                    truncated=False,
                    line_content=sm.SearchAddressLineContentType.ADDRESS,
                ),
            ],
            overflow=False,
            truncated=False,
            dpv_status=sm.DPVStatus.CONFIRMED,
            missing_sub_premise=False,
        ),
        picklist=None,
        verification_flags=sm.SearchVerificationFlags(
            bldg_firm_name_changed=None,
            primary_number_changed=None,
            street_corrected=None,
            rural_rte_highway_contract_matched=None,
            city_name_changed=None,
            city_alias_matched=None,
            state_province_changed=None,
            post_code_corrected=True,
            secondary_num_retained=None,
            iden_pre_st_info_retained=None,
            gen_pre_st_info_retained=None,
            post_st_info_retained=None,
        ),
        verify_level=sm.VerifyLevel.VERIFIED,
    ),
    id="database_layout_iso2_response",
)


picklist_response = pytest.param(
    {
        "header": {"information_header": {"StateTransition": "PickList", "CreditsUsed": 0}},
        "body": {
            "QAPicklist": {
                "FullPicklistMoniker": "USA|8a5bb6bb-ab7c-4e90-a91e-b5247111f8ca|7.730...baz$33",
                "PicklistEntry": [
                    {
                        "Moniker": "USA|8a5bb6bb-ab7c-4e90-a91e-b5247111f8ca|7.730...bar$33",
                        "PartialAddress": "Superstore, 333 Foo St, Washington DC 12345-6789",
                        "Picklist": "Superstore, 333 Foo St, Washington DC",
                        "Postcode": "12345-6789",
                        "Score": 100,
                        "QAAddress": None,
                        "FullAddress": True,
                        "Multiples": "false",
                        "CanStep": "false",
                        "AliasMatch": "false",
                        "PostcodeRecoded": "false",
                        "CrossBorderMatch": "false",
                        "DummyPOBox": "false",
                        "Name": "false",
                        "Information": "false",
                        "WarnInformation": "false",
                        "IncompleteAddr": "false",
                        "UnresolvableRange": "false",
                        "PhantomPrimaryPoint": "false",
                        "SubsidiaryData": "false",
                        "ExtendedData": "false",
                        "EnhancedData": "false",
                    },
                    {
                        "Moniker": "USA|8a5bb6bb-ab7c-4e90-a91e-b5247111f8ca|7.7....foo$33",
                        "PartialAddress": "333 Foo St Apt 101 ... 208, Washington DC 12345-6789",
                        "Picklist": "333 Foo St Apt 101 ... 208, Washington DC",
                        "Postcode": "12345-6789",
                        "Score": 100,
                        "QAAddress": None,
                        "FullAddress": "false",
                        "Multiples": True,
                        "CanStep": "false",
                        "AliasMatch": "false",
                        "PostcodeRecoded": "false",
                        "CrossBorderMatch": "false",
                        "DummyPOBox": "false",
                        "Name": "false",
                        "Information": "false",
                        "WarnInformation": "false",
                        "IncompleteAddr": "false",
                        "UnresolvableRange": True,
                        "PhantomPrimaryPoint": "false",
                        "SubsidiaryData": "false",
                        "ExtendedData": "false",
                        "EnhancedData": "false",
                    },
                ],
                "Prompt": "Please confirm your Apt/Ste/Unit Number",
                "Total": 2,
                "AutoFormatSafe": "false",
                "AutoFormatPastClose": "false",
                "AutoStepinSafe": "false",
                "AutoStepinPastClose": "false",
                "LargePotential": "false",
                "MaxMatches": "false",
                "MoreOtherMatches": "false",
                "OverThreshold": "false",
                "Timeout": "false",
            },
            "QAAddress": None,
            "VerificationFlags": {
                "BldgFirmNameChanged": None,
                "PrimaryNumberChanged": None,
                "StreetCorrected": None,
                "RuralRteHighwayContractMatched": None,
                "CityNameChanged": None,
                "CityAliasMatched": None,
                "StateProvinceChanged": None,
                "PostCodeCorrected": True,
                "SecondaryNumRetained": None,
                "IdenPreStInfoRetained": None,
                "GenPreStInfoRetained": None,
                "PostStInfoRetained": None,
            },
            "VerifyLevel": "PremisesPartial",
        },
    },
    sm.SearchResponse(
        address=None,
        picklist=sm.Picklist(
            full_picklist_moniker="USA|8a5bb6bb-ab7c-4e90-a91e-b5247111f8ca|7.730...baz$33",
            picklist_entries=[
                sm.PicklistEntry(
                    moniker="USA|8a5bb6bb-ab7c-4e90-a91e-b5247111f8ca|7.730...bar$33",
                    partial_address="Superstore, 333 Foo St, Washington DC 12345-6789",
                    picklist="Superstore, 333 Foo St, Washington DC",
                    postcode="12345-6789",
                    score=100,
                    formatted_address=None,
                    full_address=True,
                    multiples=False,
                    can_step=False,
                    alias_match=False,
                    postcode_recoded=False,
                    cross_border_match=False,
                    dummy_po_box=False,
                    name=False,
                    information=False,
                    warn_information=False,
                    incomplete_addr=False,
                    unresolvable_range=False,
                    phantom_primary_point=False,
                    subsidiary_data=False,
                    extended_data=False,
                    enhanced_data=False,
                ),
                sm.PicklistEntry(
                    moniker="USA|8a5bb6bb-ab7c-4e90-a91e-b5247111f8ca|7.7....foo$33",
                    partial_address="333 Foo St Apt 101 ... 208, Washington DC 12345-6789",
                    picklist="333 Foo St Apt 101 ... 208, Washington DC",
                    postcode="12345-6789",
                    score=100,
                    formatted_address=None,
                    full_address=False,
                    multiples=True,
                    can_step=False,
                    alias_match=False,
                    postcode_recoded=False,
                    cross_border_match=False,
                    dummy_po_box=False,
                    name=False,
                    information=False,
                    warn_information=False,
                    incomplete_addr=False,
                    unresolvable_range=True,
                    phantom_primary_point=False,
                    subsidiary_data=False,
                    extended_data=False,
                    enhanced_data=False,
                ),
            ],
            prompt="Please confirm your Apt/Ste/Unit Number",
            total=2,
            auto_format_safe=False,
            auto_format_past_close=False,
            auto_stepin_safe=False,
            auto_stepin_past_close=False,
            large_potential=False,
            max_matches=False,
            more_other_matches=False,
            over_threshold=False,
            timeout=False,
        ),
        verification_flags=sm.SearchVerificationFlags(
            bldg_firm_name_changed=None,
            primary_number_changed=None,
            street_corrected=None,
            rural_rte_highway_contract_matched=None,
            city_name_changed=None,
            city_alias_matched=None,
            state_province_changed=None,
            post_code_corrected=True,
            secondary_num_retained=None,
            iden_pre_st_info_retained=None,
            gen_pre_st_info_retained=None,
            post_st_info_retained=None,
        ),
        verify_level=sm.VerifyLevel.PREMISES_PARTIAL,
    ),
    id="picklist_response",
)

no_matches_response = pytest.param(
    {
        "header": {"information_header": {"StateTransition": "NoMatches", "CreditsUsed": 0}},
        "body": {
            "QAPicklist": {
                "FullPicklistMoniker": "USA|91979cff-e6cd-41ec-b641-dc2a2d4bbe94|7.730...foo$3",
                "PicklistEntry": [
                    {
                        "Moniker": None,
                        "PartialAddress": None,
                        "Picklist": "No matches",
                        "Postcode": None,
                        "Score": 0,
                        "QAAddress": None,
                        "FullAddress": "false",
                        "Multiples": "false",
                        "CanStep": "false",
                        "AliasMatch": "false",
                        "PostcodeRecoded": "false",
                        "CrossBorderMatch": "false",
                        "DummyPOBox": "false",
                        "Name": "false",
                        "Information": True,
                        "WarnInformation": True,
                        "IncompleteAddr": "false",
                        "UnresolvableRange": "false",
                        "PhantomPrimaryPoint": "false",
                        "SubsidiaryData": "false",
                        "ExtendedData": "false",
                        "EnhancedData": "false",
                    }
                ],
                "Prompt": "Enter selection",
                "Total": 1,
                "AutoFormatSafe": "false",
                "AutoFormatPastClose": "false",
                "AutoStepinSafe": "false",
                "AutoStepinPastClose": "false",
                "LargePotential": "false",
                "MaxMatches": "false",
                "MoreOtherMatches": "false",
                "OverThreshold": "false",
                "Timeout": "false",
            },
            "QAAddress": None,
            "VerificationFlags": None,
            "VerifyLevel": "None",
        },
    },
    sm.SearchResponse(
        address=None,
        picklist=sm.Picklist(
            full_picklist_moniker="USA|91979cff-e6cd-41ec-b641-dc2a2d4bbe94|7.730...foo$3",
            picklist_entries=[
                sm.PicklistEntry(
                    moniker=None,
                    partial_address=None,
                    picklist="No matches",
                    postcode=None,
                    score=0,
                    formatted_address=None,
                    full_address=False,
                    multiples=False,
                    can_step=False,
                    alias_match=False,
                    postcode_recoded=False,
                    cross_border_match=False,
                    dummy_po_box=False,
                    name=False,
                    information=True,
                    warn_information=True,
                    incomplete_addr=False,
                    unresolvable_range=False,
                    phantom_primary_point=False,
                    subsidiary_data=False,
                    extended_data=False,
                    enhanced_data=False,
                )
            ],
            prompt="Enter selection",
            total=1,
            auto_format_safe=False,
            auto_format_past_close=False,
            auto_stepin_safe=False,
            auto_stepin_past_close=False,
            large_potential=False,
            max_matches=False,
            more_other_matches=False,
            over_threshold=False,
            timeout=False,
        ),
        verification_flags=None,
        verify_level=sm.VerifyLevel.NONE,
    ),
    id="no_matches_response",
)


@pytest.mark.parametrize(
    "caller_response, client_response",
    [
        single_standard_response,
        database_layout_iso2_response,
        picklist_response,
        no_matches_response,
    ],
)
def test_client_search(mocker, caller_response, client_response):
    caller = mocker.Mock(spec=ApiCaller)
    caller.DoSearch.return_value = caller_response

    client = Client(caller)

    request = sm.SearchRequest(engine=sm.EngineEnum.VERIFICATION, search="foo")

    response = client.search(request)

    caller.DoSearch.assert_called_once_with(
        Engine="Verification",
        Search="foo",
        Country="USA",
        FormattedAddressInPicklist=False,
        Layout=None,
    )

    assert response.dict() == client_response.dict()


def test_client_search_empty_body_response(mocker):
    caller = mocker.Mock(spec=ApiCaller)
    caller.DoSearch.return_value = {"header": {}, "body": {}}

    client = Client(caller)

    request = sm.SearchRequest(engine=sm.EngineEnum.VERIFICATION, search="foo")

    response = client.search(request)

    assert response.dict() == sm.SearchResponse().dict()


def test_client_search_no_body_response(mocker):
    caller = mocker.Mock(spec=ApiCaller)
    caller.DoSearch.return_value = {"header": {}}

    client = Client(caller)

    request = sm.SearchRequest(engine=sm.EngineEnum.VERIFICATION, search="foo")

    with pytest.raises(KeyError, match="body"):
        client.search(request)
