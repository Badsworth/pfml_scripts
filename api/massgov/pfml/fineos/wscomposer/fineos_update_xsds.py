import os

import defusedxml.minidom

import massgov.pfml.fineos
import massgov.pfml.fineos.models
import massgov.pfml.util.logging

logger = massgov.pfml.util.logging.get_logger(__package__)


def handler():
    """
    Fetch the XML Schema Definition (XSD) files for Web Service Composer APIS.

    This is only needed if the API has changed. The output files should be committed to version control.
    """
    update_xsds()


def update_xsds():
    massgov.pfml.util.logging.init("fineos-update-xsds")
    cps = massgov.pfml.fineos.create_client()

    services = [
        "EmployeeRegisterService.Request.xsd",
        "EmployeeRegisterService.Response.xsd",
        "ReadEmployer.Request.xsd",
        "ReadEmployer.Response.xsd",
        "UpdateOrCreateParty.Request.xsd",
        "UpdateOrCreateParty.Response.xsd",
        "ServiceAgreementService.Request.xsd",
        "ServiceAgreementService.Response.xsd",
        "OccupationDetailUpdateService.Request.xsd",
        "OccupationDetailUpdateService.Response.xsd",
    ]

    dir_path = os.path.dirname(os.path.realpath(__file__))

    for service in services:
        [_name, _type, _ext] = service.split(".")
        query = {"config": _name}
        query[f"{_type}-{_ext.upper()}"] = None  # type: ignore
        response = cps._wscomposer_request("GET", "webservice", "", query, "")  # type: ignore

        file_xml = defusedxml.minidom.parseString(response.text)
        pretty_xml = file_xml.toprettyxml(indent="  ")
        if len(pretty_xml):
            f = open(dir_path + "/" + service, "w")
            f.write(pretty_xml)
            f.close()
