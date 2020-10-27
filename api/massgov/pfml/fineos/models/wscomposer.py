#
# Models for Web Services Composer.
#
from __future__ import annotations

import datetime
from typing import Any, List, Optional

import pydantic


class EmployeeRegistration(pydantic.BaseModel):
    user_id: str
    customer_number: Optional[int]
    employer_id: str
    date_of_birth: datetime.date
    email: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    national_insurance_no: str


class CreateOrUpdateEmployer(pydantic.BaseModel):
    fineos_customer_nbr: str
    employer_fein: str
    employer_legal_name: str
    employer_dba: Optional[str]


# Classes for UpdateOrCreateParty request. Most attributes
# we are defaulting. The classes are used to help construct
# the XML request body. Not all elements of the request have
# been modeled, only those required to create or update a
# basic organisation with no points of contact or addresses.
class InstanceDomainAndFullIdItem(pydantic.BaseModel):
    InstanceName: str
    DomainName: str
    FullId: int


class InstanceDomainAndFullId(pydantic.BaseModel):
    InstanceDomainAndFullId: InstanceDomainAndFullIdItem


class OCPartyAliasItem(pydantic.BaseModel):
    Type: InstanceDomainAndFullId = InstanceDomainAndFullId(
        InstanceDomainAndFullId=InstanceDomainAndFullIdItem(
            InstanceName="Unknown", DomainName="Party Alias Type", FullId=8928000
        )
    )
    Value: Any = None


class OCPartyAlias(pydantic.BaseModel):
    OCPartyAlias: List[OCPartyAliasItem]


class OCOrganisationDefaultItem(pydantic.BaseModel):
    LastUpdateDate: str = "1753-01-01T00:00:00"
    UserUpdatedBy: str = "PFML_API"
    persistent_boeversion: int = pydantic.Field(0, alias="persistent-boeversion")
    C_CORRESP_PRIVHOLDER: int = 0
    C_OSGROUP_OWP: int = 0
    CulturalConsiderations: Any = None
    CustomerNo: str
    Disabled: bool = False
    ExcludePartyFromSearch: bool = False
    FailedLogonAttempts: int = 0
    GroupClient: bool = False
    I_CORRESP_PRIVHOLDER: int = 0
    I_OSGROUP_OWP: int = 0
    IdentificationNumberType: InstanceDomainAndFullId = InstanceDomainAndFullId(
        InstanceDomainAndFullId=InstanceDomainAndFullIdItem(
            InstanceName="Tax Identification Number",
            DomainName="IdentificationNumberType",
            FullId=8736002,
        )
    )
    LastSuccessfulLogon: str = "1753-01-01T00:00:00"
    NotificationIssued: bool = False
    PartyType: InstanceDomainAndFullId = InstanceDomainAndFullId(
        InstanceDomainAndFullId=InstanceDomainAndFullIdItem(
            InstanceName="Employer", DomainName="Party Type", FullId=3290008
        )
    )
    Password: Any = None
    Position1: int = 0
    Position2: int = 0
    PronouncedAs: Any = None
    ReferenceGloballyUnique: bool = False
    ReferenceNo: Any = None
    SecuredClient: bool = False
    SelfServiceEnabled: bool = False
    SourceSystem: InstanceDomainAndFullId = InstanceDomainAndFullId(
        InstanceDomainAndFullId=InstanceDomainAndFullIdItem(
            InstanceName="Internal", DomainName="PartySourceSystem", FullId=8032000
        )
    )
    SuppressMktg: bool = False
    TenureStart: str = "1753-01-01T00:00:00"
    AccountingDate: str = "1753-01-01T00:00:00"
    BusinessType: InstanceDomainAndFullId = InstanceDomainAndFullId(
        InstanceDomainAndFullId=InstanceDomainAndFullIdItem(
            InstanceName="Unknown", DomainName="Organisation Business Type", FullId=3328000
        )
    )
    CompanyNumber: Any = None
    CorporateTaxDistrict: Any = None
    CorporateTaxNumber: str
    DateBusinessCommenced: str = "1753-01-01T00:00:00"
    DateOfIncorporation: str = "1753-01-01T00:00:00"
    DoingBusinessAs: str
    EndOfTrading: str = "1753-01-01T00:00:00"
    EOTReasonCode: InstanceDomainAndFullId = InstanceDomainAndFullId(
        InstanceDomainAndFullId=InstanceDomainAndFullIdItem(
            InstanceName="Unknown", DomainName="EndOfTradingReasonCode", FullId=6592000
        )
    )
    EOTReasonInd: bool = False
    FinancialYearEnd: str = "1753-01-01T00:00:00"
    LegalBusinessName: str
    LegalStatus: InstanceDomainAndFullId = InstanceDomainAndFullId(
        InstanceDomainAndFullId=InstanceDomainAndFullIdItem(
            InstanceName="Unknown", DomainName="Legal Status", FullId=1408000
        )
    )
    Name: str
    PayeTaxDistrict: Any = None
    PayeTaxNumber: Any = None
    RegisteredNumber: Any = None
    ShortName: Any = None
    UpperName: Any = None
    UpperRegisteredNumber: Any = None
    UpperShortName: Any = None
    VatNumber: Any = None


class OCOrganisationWithDefault(pydantic.BaseModel):
    OCOrganisation: List[OCOrganisationDefaultItem]


class OCOrganisationNameItem(pydantic.BaseModel):
    LastUpdateDate: str = "1753-01-01T00:00:00"
    UserUpdatedBy: str = "PFML_API"
    persistent_boeversion: int = pydantic.Field(0, alias="persistent-boeversion")
    Description: Any = None
    DoingBusinessAs: str
    LegalBusinessName: str
    Name: str
    NameType: InstanceDomainAndFullId = InstanceDomainAndFullId(
        InstanceDomainAndFullId=InstanceDomainAndFullIdItem(
            InstanceName="Unknown", DomainName="OrganisationNameType", FullId=6240000
        )
    )
    PronouncedAs: Any = None
    ShortName: Any = None
    UpperName: Any = None
    UpperShortName: Any = None
    ValidFrom: str = "1753-01-01T00:00:00"
    ValidTo: str = "1753-01-01T00:00:00"
    DefaultName: bool = True
    RunBOValidations: bool = True
    organisationWithDefault: OCOrganisationWithDefault


class OCOrganisationName(pydantic.BaseModel):
    OCOrganisationName: List[OCOrganisationNameItem]


class OCOrganisationItem(pydantic.BaseModel):
    C_CORRESP_PRIVHOLDER: int = 0
    C_OSGROUP_OWP: int = 0
    CulturalConsiderations: Any = None
    CustomerNo: str
    Disabled: bool = False
    ExcludePartyFromSearch: bool = False
    FailedLogonAttempts: int = 0
    GroupClient: bool = False
    I_CORRESP_PRIVHOLDER: int = 0
    I_OSGROUP_OWP: int = 0
    IdentificationNumberType: InstanceDomainAndFullId = InstanceDomainAndFullId(
        InstanceDomainAndFullId=InstanceDomainAndFullIdItem(
            InstanceName="Tax Identification Number",
            DomainName="IdentificationNumberType",
            FullId=8736002,
        )
    )
    LastSuccessfulLogon: str = "1753-01-01T00:00:00"
    NotificationIssued: bool = False
    PartyType: InstanceDomainAndFullId = InstanceDomainAndFullId(
        InstanceDomainAndFullId=InstanceDomainAndFullIdItem(
            InstanceName="Employer", DomainName="Party Type", FullId=3290008
        )
    )
    Password: Any = None
    Position1: int = 0
    Position2: int = 0
    PronouncedAs: Any = None
    ReferenceGloballyUnique: bool = False
    ReferenceNo: Any = None
    SecuredClient: bool = False
    SelfServiceEnabled: bool = False
    SourceSystem: InstanceDomainAndFullId = InstanceDomainAndFullId(
        InstanceDomainAndFullId=InstanceDomainAndFullIdItem(
            InstanceName="Internal", DomainName="PartySourceSystem", FullId=8032000
        )
    )
    SuppressMktg: bool = False
    TenureStart: str = "1753-01-01T00:00:00"
    personalContactMediums: Any = None
    partyContactPreferences: Any = None
    partyAliases: OCPartyAlias = OCPartyAlias(OCPartyAlias=[OCPartyAliasItem()])
    pointsOfContact: Any = None
    AccountingDate: str = "1753-01-01T00:00:00"
    BusinessType: InstanceDomainAndFullId = InstanceDomainAndFullId(
        InstanceDomainAndFullId=InstanceDomainAndFullIdItem(
            InstanceName="Unknown", DomainName="Organisation Business Type", FullId=3328000
        )
    )
    CompanyNumber: Any = None
    CorporateTaxDistrict: Any = None
    CorporateTaxNumber: str
    DateBusinessCommenced: str = "1753-01-01T00:00:00"
    DateOfIncorporation: str = "1753-01-01T00:00:00"
    DoingBusinessAs: str
    EndOfTrading: str = "1753-01-01T00:00:00"
    EOTReasonCode: InstanceDomainAndFullId = InstanceDomainAndFullId(
        InstanceDomainAndFullId=InstanceDomainAndFullIdItem(
            InstanceName="Unknown", DomainName="EndOfTradingReasonCode", FullId=6592000
        )
    )
    EOTReasonInd: bool = False
    FinancialYearEnd: str = "1753-01-01T00:00:00"
    LegalBusinessName: str
    LegalStatus: InstanceDomainAndFullId = InstanceDomainAndFullId(
        InstanceDomainAndFullId=InstanceDomainAndFullIdItem(
            InstanceName="Unknown", DomainName="Legal Status", FullId=1408000
        )
    )
    Name: str
    PayeTaxDistrict: Any = None
    PayeTaxNumber: Any = None
    RegisteredNumber: Any = None
    ShortName: Any = None
    UpperName: Any = None
    UpperRegisteredNumber: Any = None
    UpperShortName: Any = None
    VatNumber: Any = None
    names: OCOrganisationName


class OCOrganisation(pydantic.BaseModel):
    OCOrganisation: List[OCOrganisationItem]


class PartyIntegrationDTOItem(pydantic.BaseModel):
    EffectiveDate: str = "1753-01-01T00:00:00"
    EndDate: str = "1753-01-01T00:00:00"
    PartyTypeFlag: str = "Employer"
    SourceSystemName: str = "Unknown"
    person: Any = None
    organisation: OCOrganisation


class UpdateData(pydantic.BaseModel):
    PartyIntegrationDTO: List[PartyIntegrationDTOItem]


class UpdateOrCreatePartyRequest(pydantic.BaseModel):
    xmlns_p: str = pydantic.Field(
        "http://www.fineos.com/wscomposer/UpdateOrCreateParty", alias="@xmlns:p"
    )
    xmlns_xsi: str = pydantic.Field("http://www.w3.org/2001/XMLSchema-instance", alias="@xmlns:xsi")
    xsi_schemaLocation: str = pydantic.Field(
        "http://www.fineos.com/wscomposer/UpdateOrCreateParty updateOrcreateparty.xsd",
        alias="@xsi:schemaLocation",
    )
    config_name: str = pydantic.Field("UpdateOrCreateParty", alias="config-name")
    update_data: UpdateData = pydantic.Field(None, alias="update-data")


# Classes to model ServiceAgreementService request XML
class AdditionalData(pydantic.BaseModel):
    name: str
    value: str


class AdditionalDataSet(pydantic.BaseModel):
    additional_data: List[AdditionalData] = pydantic.Field([], alias="additional-data")


class ServiceAgreementData(pydantic.BaseModel):
    additional_data_set: AdditionalDataSet = pydantic.Field(None, alias="additional-data-set")


class ServiceAgreementServiceRequest(pydantic.BaseModel):
    xmlns_p: str = pydantic.Field(
        "http://www.fineos.com/wscomposer/ServiceAgreementService", alias="@xmlns:p"
    )
    xmlns_xsi: str = pydantic.Field("http://www.w3.org/2001/XMLSchema-instance", alias="@xmlns:xsi")
    xsi_schemaLocation: str = pydantic.Field(
        "http://www.fineos.com/wscomposer/ServiceAgreementService serviceagreement.xsd",
        alias="@xsi:schemaLocation",
    )
    config_name: str = pydantic.Field("ServiceAgreementService", alias="config-name")
    update_data: ServiceAgreementData = pydantic.Field(None, alias="update-data")
