#
# Tests for massgov.pfml.fineos.fineos_client.
#

import datetime
import json
import pathlib
import time
import xml.etree.ElementTree
from unittest import mock

import defusedxml.ElementTree
import pytest
import requests

import massgov.pfml.fineos.fineos_client
import massgov.pfml.fineos.models
from massgov.pfml.fineos.exception import FINEOSClientError
from massgov.pfml.fineos.models.group_client_api import EForm, EFormAttribute, ModelEnum

TEST_FOLDER = pathlib.Path(__file__).parent

ws_update_response = """<?xml version='1.0' encoding='utf-8'?>
<p:WSUpdateResponse xmlns:p="http://www.fineos.com/wscomposer/UpdateOrCreateParty"
                    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <oid-list>
    <oid>PE:11528:0000124502</oid>
  </oid-list>
  <additional-data-set>
    <additional-data>
      <name>SERVICE_RESPONSE_CODE</name>
      <value>200</value>
    </additional-data>
    <additional-data>
      <name>CUSTOMER_NUMBER</name>
      <value>5157438</value>
    </additional-data>
  </additional-data-set>
</p:WSUpdateResponse>"""

get_eform_response = json.dumps(
    {
        "eformType": "Other Income - current version",
        "eformId": 6245,
        "eformAttributes": [
            {
                "name": "V2OtherIncomeNonEmployerBenefitWRT1",
                "enumValue": {
                    "domainName": "WageReplacementType2",
                    "instanceValue": "Workers Compensation",
                },
            },
            {"name": "V2Spacer1", "stringValue": ""},
            {
                "name": "V2ReceiveWageReplacement7",
                "enumValue": {"domainName": "PleaseSelectYesNo", "instanceValue": "Yes"},
            },
            {"name": "Spacer11", "stringValue": ""},
            {
                "name": "V2ReceiveWageReplacement8",
                "enumValue": {"domainName": "PleaseSelectYesNo", "instanceValue": "No"},
            },
            {
                "name": "V2SalaryContinuation1",
                "enumValue": {"domainName": "PleaseSelectYesNo", "instanceValue": "No"},
            },
            {"name": "V2Spacer3", "stringValue": ""},
            {"name": "V2Spacer2", "stringValue": ""},
            {
                "name": "V2SalaryContinuation2",
                "enumValue": {"domainName": "PleaseSelectYesNo", "instanceValue": "Yes"},
            },
            {"name": "V2Spacer5", "stringValue": ""},
            {
                "name": "V2ReceiveWageReplacement3",
                "enumValue": {"domainName": "PleaseSelectYesNo", "instanceValue": "Please Select"},
            },
            {"name": "V2Spacer4", "stringValue": ""},
            {"name": "V2Spacer7", "stringValue": ""},
            {"name": "V2Spacer6", "stringValue": ""},
            {"name": "V2Header1", "stringValue": "Employer-Sponsored Benefits"},
            {"name": "V2Spacer9", "stringValue": ""},
            {"name": "V2Header2", "stringValue": "Income from Other Sources"},
            {"name": "V2Spacer8", "stringValue": ""},
            {
                "name": "V2ReceiveWageReplacement1",
                "enumValue": {"domainName": "PleaseSelectYesNo", "instanceValue": "Yes"},
            },
            {
                "name": "V2ReceiveWageReplacement2",
                "enumValue": {"domainName": "PleaseSelectYesNo", "instanceValue": "Yes"},
            },
            {
                "name": "V2Examples7",
                "stringValue": "Workers Compensation, Unemployment Insurance, Social Security Disability Insurance, Disability benefits under a governmental retirement plan such as STRS or PERS, Jones Act benefits, Railroad Retirement benefit, Earnings from another employer or through self-employment",
            },
            {"name": "V2OtherIncomeNonEmployerBenefitStartDate1", "dateValue": "2021-05-04"},
            {
                "name": "V2WRT1",
                "enumValue": {
                    "domainName": "WageReplacementType",
                    "instanceValue": "Permanent disability insurance",
                },
            },
            {
                "name": "V2WRT2",
                "enumValue": {
                    "domainName": "WageReplacementType",
                    "instanceValue": "Temporary disability insurance (Long- or Short-term)",
                },
            },
            {
                "name": "V2Frequency2",
                "enumValue": {
                    "domainName": "FrequencyEforms",
                    "instanceValue": "One time / Lump sum",
                },
            },
            {
                "name": "V2Frequency1",
                "enumValue": {"domainName": "FrequencyEforms", "instanceValue": "Per week"},
            },
            {"name": "V2OtherIncomeNonEmployerBenefitEndDate1", "dateValue": "2021-05-05"},
            {"name": "V2StartDate1", "dateValue": "2021-05-04"},
            {"name": "V2EndDate1", "dateValue": "2021-05-28"},
            {"name": "V2Amount1", "decimalValue": 40},
            {"name": "V2EndDate2", "dateValue": "2021-05-28"},
            {"name": "V2Amount2", "decimalValue": 150},
            {"name": "V2StartDate2", "dateValue": "2021-05-10"},
            {"name": "V2OtherIncomeNonEmployerBenefitAmount1", "decimalValue": 75},
            {"name": "V2Spacer10", "stringValue": ""},
            {
                "name": "V2OtherIncomeNonEmployerBenefitFrequency1",
                "enumValue": {"domainName": "FrequencyEforms", "instanceValue": "Per month"},
            },
        ],
    }
)


def xml_equal(actual_data, expected_name):
    actual_xml = xml.etree.ElementTree.canonicalize(xml_data=actual_data)
    expected_xml = xml.etree.ElementTree.canonicalize(
        from_file=TEST_FOLDER / "expected_xml" / expected_name
    )
    assert actual_xml == expected_xml
    return True


class MockOAuth2Session(requests.Session):
    """A session that mocks out OAuth2Session methods but is otherwise a real `requests.Session`.

    This helps tests use as much of the real `requests` library code as possible, which makes it
    possible to test for bugs that only appear in when real HTTP requests are happening.
    """

    @staticmethod
    def fetch_token(token_url, client_id, client_secret, timeout):
        return {
            "access_token": "1234abcd",
            "token_type": "Bearer",
            "expires_in": 3600,
            "expires_at": time.time() + 3600,
        }


@pytest.fixture
def fineos_client(httpserver):
    """FINEOSClient configured to call pytest-httpserver and injected with a mock oauth_session."""
    client = massgov.pfml.fineos.fineos_client.FINEOSClient(
        customer_api_url=httpserver.url_for("/customerapi/"),
        group_client_api_url=httpserver.url_for("/groupclientapi/"),
        integration_services_api_url=httpserver.url_for("/integration-services/"),
        wscomposer_url=httpserver.url_for("/wscomposer/"),
        wscomposer_user_id="USER",
        oauth2_url=httpserver.url_for("/oauth2/token"),
        client_id="1234567890abcdefghij",
        client_secret="abcdefghijklmnopqrstuvwxyz",
        oauth_session=MockOAuth2Session(),
    )
    return client


def test_constructor(httpserver, fineos_client):
    assert fineos_client.customer_api_url == httpserver.url_for("/customerapi/")
    assert fineos_client.group_client_api_url == httpserver.url_for("/groupclientapi/")
    assert fineos_client.integration_services_api_url == httpserver.url_for(
        "/integration-services/"
    )
    assert fineos_client.wscomposer_url == httpserver.url_for("/wscomposer/")
    assert fineos_client.oauth2_url == httpserver.url_for("/oauth2/token")
    assert fineos_client.oauth_session is not None


def test_create_or_update_employer_success(httpserver, fineos_client):
    httpserver.expect_ordered_request(
        "/wscomposer/webservice",
        query_string={"config": "UpdateOrCreateParty", "userid": "USER"},
        method="POST",
        headers={"Content-Type": "application/xml; charset=utf-8"},
    ).respond_with_data(ws_update_response.encode("utf-8"), content_type="application/xml")

    employer_request_body = massgov.pfml.fineos.models.CreateOrUpdateEmployer(
        fineos_customer_nbr="08eedafc-c591-4988-a099-b35b3e2b704f",
        employer_fein="100000050",
        employer_legal_name="Test One Corp",
        employer_dba="Test One",
    )
    fineos_customer_nbr, fineos_employer_id = fineos_client.create_or_update_employer(
        employer_request_body
    )

    assert len(httpserver.log) == 1
    assert xml_equal(httpserver.log[0][0].data, "create_or_update_employer.request.xml")
    assert fineos_customer_nbr == "08eedafc-c591-4988-a099-b35b3e2b704f"
    assert fineos_employer_id == 5157438


def test_create_or_update_employer_unicode_name(httpserver, fineos_client):
    httpserver.expect_ordered_request(
        "/wscomposer/webservice",
        query_string={"config": "UpdateOrCreateParty", "userid": "USER"},
        method="POST",
        headers={"Content-Type": "application/xml; charset=utf-8"},
    ).respond_with_data(ws_update_response.encode("utf-8"), content_type="application/xml")

    employer_request_body = massgov.pfml.fineos.models.CreateOrUpdateEmployer(
        fineos_customer_nbr="08eedafc-c591-4988-a099-b35b3e2b704f",
        employer_fein="100000050",
        employer_legal_name="Test “Two” Č Corp",
        employer_dba="“Two” Č",
    )
    fineos_customer_nbr, fineos_employer_id = fineos_client.create_or_update_employer(
        employer_request_body
    )

    assert len(httpserver.log) == 1
    tree = defusedxml.ElementTree.fromstring(httpserver.log[0][0].data)
    assert (
        tree.find(
            "./update-data/PartyIntegrationDTO/organisation/OCOrganisation/DoingBusinessAs"
        ).text
        == "“Two” Č"
    )
    assert (
        tree.find(
            "./update-data/PartyIntegrationDTO/organisation/OCOrganisation/LegalBusinessName"
        ).text
        == "Test “Two” Č Corp"
    )
    assert (
        tree.find("./update-data/PartyIntegrationDTO/organisation/OCOrganisation/Name").text
        == "Test “Two” Č Corp"
    )
    assert fineos_customer_nbr == "08eedafc-c591-4988-a099-b35b3e2b704f"
    assert fineos_employer_id == 5157438


def test_get_eform(httpserver, fineos_client):

    httpserver.expect_ordered_request(
        "/groupclientapi/groupClient/cases/NTN-100-ABS-01/eforms/3333/readEform",
        method="GET",
        headers={"userid": "FINEOS_WEB_ID", "Content-Type": "application/json"},
    ).respond_with_data(get_eform_response, content_type="application/json")

    eform = fineos_client.get_eform("FINEOS_WEB_ID", "NTN-100-ABS-01", "3333")
    assert eform == EForm(
        eformType="Other Income - current version",
        eformId=6245,
        eformAttributes=[
            EFormAttribute(
                name="V2OtherIncomeNonEmployerBenefitWRT1",
                booleanValue=None,
                dateValue=None,
                decimalValue=None,
                integerValue=None,
                stringValue=None,
                enumValue=ModelEnum(
                    domainName="WageReplacementType2", instanceValue="Workers Compensation"
                ),
            ),
            EFormAttribute(
                name="V2Spacer1",
                booleanValue=None,
                dateValue=None,
                decimalValue=None,
                integerValue=None,
                stringValue="",
                enumValue=None,
            ),
            EFormAttribute(
                name="V2ReceiveWageReplacement7",
                booleanValue=None,
                dateValue=None,
                decimalValue=None,
                integerValue=None,
                stringValue=None,
                enumValue=ModelEnum(domainName="PleaseSelectYesNo", instanceValue="Yes"),
            ),
            EFormAttribute(
                name="Spacer11",
                booleanValue=None,
                dateValue=None,
                decimalValue=None,
                integerValue=None,
                stringValue="",
                enumValue=None,
            ),
            EFormAttribute(
                name="V2ReceiveWageReplacement8",
                booleanValue=None,
                dateValue=None,
                decimalValue=None,
                integerValue=None,
                stringValue=None,
                enumValue=ModelEnum(domainName="PleaseSelectYesNo", instanceValue="No"),
            ),
            EFormAttribute(
                name="V2SalaryContinuation1",
                booleanValue=None,
                dateValue=None,
                decimalValue=None,
                integerValue=None,
                stringValue=None,
                enumValue=ModelEnum(domainName="PleaseSelectYesNo", instanceValue="No"),
            ),
            EFormAttribute(
                name="V2Spacer3",
                booleanValue=None,
                dateValue=None,
                decimalValue=None,
                integerValue=None,
                stringValue="",
                enumValue=None,
            ),
            EFormAttribute(
                name="V2Spacer2",
                booleanValue=None,
                dateValue=None,
                decimalValue=None,
                integerValue=None,
                stringValue="",
                enumValue=None,
            ),
            EFormAttribute(
                name="V2SalaryContinuation2",
                booleanValue=None,
                dateValue=None,
                decimalValue=None,
                integerValue=None,
                stringValue=None,
                enumValue=ModelEnum(domainName="PleaseSelectYesNo", instanceValue="Yes"),
            ),
            EFormAttribute(
                name="V2Spacer5",
                booleanValue=None,
                dateValue=None,
                decimalValue=None,
                integerValue=None,
                stringValue="",
                enumValue=None,
            ),
            EFormAttribute(
                name="V2ReceiveWageReplacement3",
                booleanValue=None,
                dateValue=None,
                decimalValue=None,
                integerValue=None,
                stringValue=None,
                enumValue=ModelEnum(domainName="PleaseSelectYesNo", instanceValue="Please Select"),
            ),
            EFormAttribute(
                name="V2Spacer4",
                booleanValue=None,
                dateValue=None,
                decimalValue=None,
                integerValue=None,
                stringValue="",
                enumValue=None,
            ),
            EFormAttribute(
                name="V2Spacer7",
                booleanValue=None,
                dateValue=None,
                decimalValue=None,
                integerValue=None,
                stringValue="",
                enumValue=None,
            ),
            EFormAttribute(
                name="V2Spacer6",
                booleanValue=None,
                dateValue=None,
                decimalValue=None,
                integerValue=None,
                stringValue="",
                enumValue=None,
            ),
            EFormAttribute(
                name="V2Header1",
                booleanValue=None,
                dateValue=None,
                decimalValue=None,
                integerValue=None,
                stringValue="Employer-Sponsored Benefits",
                enumValue=None,
            ),
            EFormAttribute(
                name="V2Spacer9",
                booleanValue=None,
                dateValue=None,
                decimalValue=None,
                integerValue=None,
                stringValue="",
                enumValue=None,
            ),
            EFormAttribute(
                name="V2Header2",
                booleanValue=None,
                dateValue=None,
                decimalValue=None,
                integerValue=None,
                stringValue="Income from Other Sources",
                enumValue=None,
            ),
            EFormAttribute(
                name="V2Spacer8",
                booleanValue=None,
                dateValue=None,
                decimalValue=None,
                integerValue=None,
                stringValue="",
                enumValue=None,
            ),
            EFormAttribute(
                name="V2ReceiveWageReplacement1",
                booleanValue=None,
                dateValue=None,
                decimalValue=None,
                integerValue=None,
                stringValue=None,
                enumValue=ModelEnum(domainName="PleaseSelectYesNo", instanceValue="Yes"),
            ),
            EFormAttribute(
                name="V2ReceiveWageReplacement2",
                booleanValue=None,
                dateValue=None,
                decimalValue=None,
                integerValue=None,
                stringValue=None,
                enumValue=ModelEnum(domainName="PleaseSelectYesNo", instanceValue="Yes"),
            ),
            EFormAttribute(
                name="V2Examples7",
                booleanValue=None,
                dateValue=None,
                decimalValue=None,
                integerValue=None,
                stringValue="Workers Compensation, Unemployment Insurance, Social Security Disability Insurance, Disability benefits under a governmental retirement plan such as STRS or PERS, Jones Act benefits, Railroad Retirement benefit, Earnings from another employer or through self-employment",
                enumValue=None,
            ),
            EFormAttribute(
                name="V2OtherIncomeNonEmployerBenefitStartDate1",
                booleanValue=None,
                dateValue=datetime.date(2021, 5, 4),
                decimalValue=None,
                integerValue=None,
                stringValue=None,
                enumValue=None,
            ),
            EFormAttribute(
                name="V2WRT1",
                booleanValue=None,
                dateValue=None,
                decimalValue=None,
                integerValue=None,
                stringValue=None,
                enumValue=ModelEnum(
                    domainName="WageReplacementType", instanceValue="Permanent disability insurance"
                ),
            ),
            EFormAttribute(
                name="V2WRT2",
                booleanValue=None,
                dateValue=None,
                decimalValue=None,
                integerValue=None,
                stringValue=None,
                enumValue=ModelEnum(
                    domainName="WageReplacementType",
                    instanceValue="Temporary disability insurance (Long- or Short-term)",
                ),
            ),
            EFormAttribute(
                name="V2Frequency2",
                booleanValue=None,
                dateValue=None,
                decimalValue=None,
                integerValue=None,
                stringValue=None,
                enumValue=ModelEnum(
                    domainName="FrequencyEforms", instanceValue="One time / Lump sum"
                ),
            ),
            EFormAttribute(
                name="V2Frequency1",
                booleanValue=None,
                dateValue=None,
                decimalValue=None,
                integerValue=None,
                stringValue=None,
                enumValue=ModelEnum(domainName="FrequencyEforms", instanceValue="Per week"),
            ),
            EFormAttribute(
                name="V2OtherIncomeNonEmployerBenefitEndDate1",
                booleanValue=None,
                dateValue=datetime.date(2021, 5, 5),
                decimalValue=None,
                integerValue=None,
                stringValue=None,
                enumValue=None,
            ),
            EFormAttribute(
                name="V2StartDate1",
                booleanValue=None,
                dateValue=datetime.date(2021, 5, 4),
                decimalValue=None,
                integerValue=None,
                stringValue=None,
                enumValue=None,
            ),
            EFormAttribute(
                name="V2EndDate1",
                booleanValue=None,
                dateValue=datetime.date(2021, 5, 28),
                decimalValue=None,
                integerValue=None,
                stringValue=None,
                enumValue=None,
            ),
            EFormAttribute(
                name="V2Amount1",
                booleanValue=None,
                dateValue=None,
                decimalValue=40.0,
                integerValue=None,
                stringValue=None,
                enumValue=None,
            ),
            EFormAttribute(
                name="V2EndDate2",
                booleanValue=None,
                dateValue=datetime.date(2021, 5, 28),
                decimalValue=None,
                integerValue=None,
                stringValue=None,
                enumValue=None,
            ),
            EFormAttribute(
                name="V2Amount2",
                booleanValue=None,
                dateValue=None,
                decimalValue=150.0,
                integerValue=None,
                stringValue=None,
                enumValue=None,
            ),
            EFormAttribute(
                name="V2StartDate2",
                booleanValue=None,
                dateValue=datetime.date(2021, 5, 10),
                decimalValue=None,
                integerValue=None,
                stringValue=None,
                enumValue=None,
            ),
            EFormAttribute(
                name="V2OtherIncomeNonEmployerBenefitAmount1",
                booleanValue=None,
                dateValue=None,
                decimalValue=75.0,
                integerValue=None,
                stringValue=None,
                enumValue=None,
            ),
            EFormAttribute(
                name="V2Spacer10",
                booleanValue=None,
                dateValue=None,
                decimalValue=None,
                integerValue=None,
                stringValue="",
                enumValue=None,
            ),
            EFormAttribute(
                name="V2OtherIncomeNonEmployerBenefitFrequency1",
                booleanValue=None,
                dateValue=None,
                decimalValue=None,
                integerValue=None,
                stringValue=None,
                enumValue=ModelEnum(domainName="FrequencyEforms", instanceValue="Per month"),
            ),
        ],
    )


def test_get_absence_period_decisions_with_error(caplog, httpserver, fineos_client):

    httpserver.expect_ordered_request(
        "/groupclientapi/groupClient/absences/absence-period-decisions?absenceId=NTN-251-ABS-01",
        method="GET",
        headers={"userid": "FINEOS_WEB_ID", "Content-Type": "application/json"},
    ).respond_with_data('{"message": "Not found"', status=404, content_type="application/json")

    with pytest.raises(FINEOSClientError):
        fineos_client.get_absence_period_decisions("FINEOS_WEB_ID", "NTN-251-ABS-01")
    assert "FINEOS Client Exception: get_absence_period_decisions" in caplog.text


def test_get_fineos_correlation_id_with_non_json():
    response = requests.Response()
    type(response).text = mock.PropertyMock(return_value="not_json")

    cid = massgov.pfml.fineos.fineos_client.get_fineos_correlation_id(response)
    assert cid is None


def test_get_fineos_correlation_id_with_json_list():
    response = requests.Response()
    type(response).text = mock.PropertyMock(return_value='[{"ha":"ha"}]')

    cid = massgov.pfml.fineos.fineos_client.get_fineos_correlation_id(response)
    assert cid is None


def test_get_fineos_correlation_id_with_string():
    response = requests.Response()
    type(response).text = mock.PropertyMock(return_value='{"correlationId":"1234"}')

    cid = massgov.pfml.fineos.fineos_client.get_fineos_correlation_id(response)
    assert cid == "1234"


def test_get_fineos_correlation_id_with_int():
    response = requests.Response()
    type(response).text = mock.PropertyMock(return_value='{"correlationId":1234}')

    cid = massgov.pfml.fineos.fineos_client.get_fineos_correlation_id(response)
    assert cid == 1234
