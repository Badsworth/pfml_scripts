#
# Tests for massgov.pfml.fineos.fineos_client.
#

import pathlib
import time
import xml.etree.ElementTree

import defusedxml
import pytest
import requests

import massgov.pfml.fineos.fineos_client
import massgov.pfml.fineos.models

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
