"""
Concrete types to use for Experian Address Validate SOAP API client.

zeep itself does the heavy lifting of XML <-> Python dictionaries, these data
structures largely just provide a slightly more ergonomic (and statically typed)
interface than raw dictionaries.

Experian WSDL (XML request/response types these map to/from):
https://ws2.ondemand.qas.com/ProOnDemand/V3/ProOnDemandService.asmx?WSDL
"""
from enum import Enum
from typing import Any, List, Optional, Union

from pydantic import Field

from massgov.pfml.util.pydantic import PydanticBaseModel
from massgov.pfml.util.strings import snake_to_camel

from .layouts import Layout


class SnakeToCamelBaseModel(PydanticBaseModel):
    class Config:
        alias_generator = snake_to_camel
        allow_population_by_field_name = True


class EngineEnum(Enum):
    SINGLELINE = "Singleline"
    TYPEDOWN = "Typedown"
    VERIFICATION = "Verification"
    INTUITIVE = "Intuitive"
    KEYFINDER = "Keyfinder"


class EngineIntensity(Enum):
    """
    The standard setting is Close. This defines how hard the search engine will
    work to obtain a match. Higher intensity values may yield more results than
    lower intensity values, but will also result in longer search times. The
    available values are:

    Exact. This does not allow many mistakes in the search term, but is the fastest.
    Close. This allows some mistakes in the search term, and is the default setting.
    Extensive. This allows many mistakes in the search term, and will take the longest.
    """

    EXACT = "Exact"
    CLOSE = "Close"
    EXTENSIVE = "Extensive"


class PromptSet(Enum):
    """
    The prompt set depends on the search engine used.

    A prompt set must be used if you are using a Partner Sourced dataset with
    the SingleLine engine.
    """

    ONELINE = "OneLine"
    DEFAULT = "Default"
    GENERIC = "Generic"
    OPTIMAL = "Optimal"
    ALTERNATE = "Alternate"
    ALTERNATE2 = "Alternate2"
    ALTERNATE3 = "Alternate3"


class Engine(SnakeToCamelBaseModel):
    engine_type: EngineEnum
    flatten: bool
    threshold: int = Field(25, ge=5, le=750)
    intensity: EngineIntensity = EngineIntensity.CLOSE
    timeout: int = Field(10000, ge=0, le=600000)
    prompt_set: PromptSet = PromptSet.DEFAULT

    def dict(self, *args, **kwargs):
        # For XML serialization of this in zeep, the data needs take the shape:
        # {
        #   "_value_1": value of engine_type
        #   "Flatten": value of flatten
        #   ...etc
        # }
        #
        # Basically for all the other settings to be attributes, they should be
        # specified by name and the actual value in the magic `_value_1` field
        base_dict = super().dict(*args, **kwargs)

        base_dict["_value_1"] = self.engine_type

        # whether by_alias is True or False, drop the value we've moved to
        # `_value_1`
        base_dict.pop("engine_type", None)
        base_dict.pop("EngineType", None)

        return base_dict


class SearchRequest(SnakeToCamelBaseModel):
    """Corresponds to QASearch type
    """

    engine: Union[EngineEnum, Engine]
    search: str
    country: str = "USA"
    formatted_address_in_picklist: Optional[bool] = False
    # layout is required when using the "Verification" engine
    layout: Optional[Layout] = None


class VerifyLevel(Enum):
    NONE = "None"
    VERIFIED = "Verified"
    INTERACTION_REQUIRED = "InteractionRequired"
    PREMISES_PARTIAL = "PremisesPartial"
    STREET_PARTIAL = "StreetPartial"
    MULTIPLE = "Multiple"
    VERIFIED_PLACE = "VerifiedPlace"
    VERIFIED_STREET = "VerifiedStreet"


class SearchAddressLineContentType(Enum):
    NONE = "None"
    ADDRESS = "Address"
    NAME = "Name"
    ANCILLARY = "Ancillary"
    DATA_PLUS = "DataPlus"


class SearchAddressLine(SnakeToCamelBaseModel):
    label: Optional[str] = None
    line: Optional[str] = None
    dataplus_group: Optional[List[Any]] = None
    overflow: bool = False
    truncated: bool = False
    line_content: SearchAddressLineContentType


class DPVStatus(Enum):
    NOT_CONFIGURED = "DPVNotConfigured"
    CONFIGURED = "DPVConfigured"
    CONFIRMED = "DPVConfirmed"
    CONFIRMED_MISSING_SEC = "DPVConfirmedMissingSec"
    NOT_CONFIRMED = "DPVNotConfirmed"
    LOCKED = "DPVLocked"
    SEED_HIT = "DPVSeedHit"


class SearchAddress(SnakeToCamelBaseModel):
    address_lines: List[SearchAddressLine] = Field(..., alias="AddressLine")
    overflow: bool = False
    truncated: bool = False
    dpv_status: DPVStatus = Field(..., alias="DPVStatus")
    missing_sub_premise: bool = False


class SearchVerificationFlags(SnakeToCamelBaseModel):
    bldg_firm_name_changed: Optional[bool] = False
    primary_number_changed: Optional[bool] = False
    street_corrected: Optional[bool] = False
    rural_rte_highway_contract_matched: Optional[bool] = False
    city_name_changed: Optional[bool] = False
    city_alias_matched: Optional[bool] = False
    state_province_changed: Optional[bool] = False
    post_code_corrected: Optional[bool] = False
    secondary_num_retained: Optional[bool] = False
    iden_pre_st_info_retained: Optional[bool] = False
    gen_pre_st_info_retained: Optional[bool] = False
    post_st_info_retained: Optional[bool] = False


class PicklistEntry(SnakeToCamelBaseModel):
    moniker: Optional[str]
    partial_address: Optional[str]
    picklist: str
    postcode: Optional[str]
    score: int
    formatted_address: Optional[SearchAddress] = Field(None, alias="QAAddress")
    full_address: bool = False
    multiples: bool = False
    can_step: bool = False
    alias_match: bool = False
    postcode_recoded: bool = False
    cross_border_match: bool = False
    dummy_po_box: bool = Field(False, alias="DummyPOBox")
    name: bool = False
    information: bool = False
    warn_information: bool = False
    incomplete_addr: bool = False
    unresolvable_range: bool = False
    phantom_primary_point: bool = False
    subsidiary_data: bool = False
    extended_data: bool = False
    enhanced_data: bool = False


class Picklist(SnakeToCamelBaseModel):
    full_picklist_moniker: Optional[str]
    picklist_entries: Optional[List[PicklistEntry]] = Field(None, alias="PicklistEntry")
    prompt: Optional[str]
    total: int
    auto_format_safe: bool = False
    auto_format_past_close: bool = False
    auto_stepin_safe: bool = False
    auto_stepin_past_close: bool = False
    large_potential: bool = False
    max_matches: bool = False
    more_other_matches: bool = False
    over_threshold: bool = False
    timeout: bool = False


class SearchResponse(SnakeToCamelBaseModel):
    """Corresponds to the QASearchResult type"""

    # Only the verification engine will ever produce a formatted address. Other
    # engines will only ever produce a picklist.
    address: Optional[SearchAddress] = Field(None, alias="QAAddress")
    picklist: Optional[Picklist] = Field(None, alias="QAPicklist")
    verification_flags: Optional[SearchVerificationFlags] = None
    verify_level: VerifyLevel = VerifyLevel.NONE
