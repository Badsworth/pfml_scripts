#
# Tests for massgov.pfml.fineos.fineos_client.
#

import datetime
import json
import pathlib
import time
import xml.etree.ElementTree

import defusedxml
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
        "eformType": "Other Income",
        "eformId": 11132,
        "eformAttributes": [
            {"name": "StartDate", "dateValue": "2020-12-24"},
            {"name": "Frequency3", "stringValue": "Please Select"},
            {
                "name": "ProgramType",
                "enumValue": {"domainName": "Program Type", "instanceValue": "Employer"},
            },
            {"name": "Spacer4", "stringValue": ""},
            {
                "name": "ProgramType3",
                "enumValue": {"domainName": "Program Type", "instanceValue": "Please Select"},
            },
            {
                "name": "ReceiveWageReplacement",
                "enumValue": {"domainName": "YesNoI'veApplied", "instanceValue": "Yes"},
            },
            {"name": "StartDate3", "dateValue": ""},
            {"name": "Spacer1", "stringValue": ""},
            {"name": "Spacer3", "stringValue": ""},
            {"name": "Spacer2", "stringValue": ""},
            {"name": "Spacer", "stringValue": ""},
            {
                "name": "WRT1",
                "enumValue": {
                    "domainName": "WageReplacementType",
                    "instanceValue": "Short-term disability insurance",
                },
            },
            {
                "name": "WRT2",
                "enumValue": {
                    "domainName": "WageReplacementType2",
                    "instanceValue": "Please Select",
                },
            },
            {
                "name": "WRT5",
                "enumValue": {
                    "domainName": "WageReplacementType",
                    "instanceValue": "Please Select",
                },
            },
            {
                "name": "WRT6",
                "enumValue": {
                    "domainName": "WageReplacementType2",
                    "instanceValue": "Please Select",
                },
            },
            {"name": "EndDate3", "dateValue": ""},
            {"name": "Amount", "decimalValue": 1000},
            {"name": "EndDate", "dateValue": "2021-01-16"},
            {"name": "Amount3", "decimalValue": 0},
            {"name": "Frequency", "stringValue": "Per Week"},
            {
                "name": "ReceiveWageReplacement4",
                "enumValue": {"domainName": "YesNoI'veApplied", "instanceValue": "Please Select"},
            },
            {
                "name": "ReceiveWageReplacement2",
                "enumValue": {"domainName": "YesNoI'veApplied", "instanceValue": "Please Select"},
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
        eformType="Other Income",
        eformId=11132,
        eformAttributes=[
            EFormAttribute(
                name="StartDate",
                booleanValue=None,
                dateValue=datetime.date(2020, 12, 24),
                decimalValue=None,
                integerValue=None,
                stringValue=None,
                enumValue=None,
            ),
            EFormAttribute(
                name="Frequency3",
                booleanValue=None,
                dateValue=None,
                decimalValue=None,
                integerValue=None,
                stringValue="Please Select",
                enumValue=None,
            ),
            EFormAttribute(
                name="ProgramType",
                booleanValue=None,
                dateValue=None,
                decimalValue=None,
                integerValue=None,
                stringValue=None,
                enumValue=ModelEnum(domainName="Program Type", instanceValue="Employer"),
            ),
            EFormAttribute(
                name="Spacer4",
                booleanValue=None,
                dateValue=None,
                decimalValue=None,
                integerValue=None,
                stringValue="",
                enumValue=None,
            ),
            EFormAttribute(
                name="ProgramType3",
                booleanValue=None,
                dateValue=None,
                decimalValue=None,
                integerValue=None,
                stringValue=None,
                enumValue=ModelEnum(domainName="Program Type", instanceValue="Please Select"),
            ),
            EFormAttribute(
                name="ReceiveWageReplacement",
                booleanValue=None,
                dateValue=None,
                decimalValue=None,
                integerValue=None,
                stringValue=None,
                enumValue=ModelEnum(domainName="YesNoI'veApplied", instanceValue="Yes"),
            ),
            EFormAttribute(
                name="StartDate3",
                booleanValue=None,
                dateValue=None,
                decimalValue=None,
                integerValue=None,
                stringValue=None,
                enumValue=None,
            ),
            EFormAttribute(
                name="Spacer1",
                booleanValue=None,
                dateValue=None,
                decimalValue=None,
                integerValue=None,
                stringValue="",
                enumValue=None,
            ),
            EFormAttribute(
                name="Spacer3",
                booleanValue=None,
                dateValue=None,
                decimalValue=None,
                integerValue=None,
                stringValue="",
                enumValue=None,
            ),
            EFormAttribute(
                name="Spacer2",
                booleanValue=None,
                dateValue=None,
                decimalValue=None,
                integerValue=None,
                stringValue="",
                enumValue=None,
            ),
            EFormAttribute(
                name="Spacer",
                booleanValue=None,
                dateValue=None,
                decimalValue=None,
                integerValue=None,
                stringValue="",
                enumValue=None,
            ),
            EFormAttribute(
                name="WRT1",
                booleanValue=None,
                dateValue=None,
                decimalValue=None,
                integerValue=None,
                stringValue=None,
                enumValue=ModelEnum(
                    domainName="WageReplacementType",
                    instanceValue="Short-term disability insurance",
                ),
            ),
            EFormAttribute(
                name="WRT2",
                booleanValue=None,
                dateValue=None,
                decimalValue=None,
                integerValue=None,
                stringValue=None,
                enumValue=ModelEnum(
                    domainName="WageReplacementType2", instanceValue="Please Select"
                ),
            ),
            EFormAttribute(
                name="WRT5",
                booleanValue=None,
                dateValue=None,
                decimalValue=None,
                integerValue=None,
                stringValue=None,
                enumValue=ModelEnum(
                    domainName="WageReplacementType", instanceValue="Please Select"
                ),
            ),
            EFormAttribute(
                name="WRT6",
                booleanValue=None,
                dateValue=None,
                decimalValue=None,
                integerValue=None,
                stringValue=None,
                enumValue=ModelEnum(
                    domainName="WageReplacementType2", instanceValue="Please Select"
                ),
            ),
            EFormAttribute(
                name="EndDate3",
                booleanValue=None,
                dateValue=None,
                decimalValue=None,
                integerValue=None,
                stringValue=None,
                enumValue=None,
            ),
            EFormAttribute(
                name="Amount",
                booleanValue=None,
                dateValue=None,
                decimalValue=1000.0,
                integerValue=None,
                stringValue=None,
                enumValue=None,
            ),
            EFormAttribute(
                name="EndDate",
                booleanValue=None,
                dateValue=datetime.date(2021, 1, 16),
                decimalValue=None,
                integerValue=None,
                stringValue=None,
                enumValue=None,
            ),
            EFormAttribute(
                name="Amount3",
                booleanValue=None,
                dateValue=None,
                decimalValue=0.0,
                integerValue=None,
                stringValue=None,
                enumValue=None,
            ),
            EFormAttribute(
                name="Frequency",
                booleanValue=None,
                dateValue=None,
                decimalValue=None,
                integerValue=None,
                stringValue="Per Week",
                enumValue=None,
            ),
            EFormAttribute(
                name="ReceiveWageReplacement4",
                booleanValue=None,
                dateValue=None,
                decimalValue=None,
                integerValue=None,
                stringValue=None,
                enumValue=ModelEnum(domainName="YesNoI'veApplied", instanceValue="Please Select"),
            ),
            EFormAttribute(
                name="ReceiveWageReplacement2",
                booleanValue=None,
                dateValue=None,
                decimalValue=None,
                integerValue=None,
                stringValue=None,
                enumValue=ModelEnum(domainName="YesNoI'veApplied", instanceValue="Please Select"),
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
