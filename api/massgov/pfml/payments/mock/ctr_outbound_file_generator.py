import os
import tempfile
import xml.dom.minidom as minidom
from random import randint
from typing import Any, Dict, List

import massgov.pfml.payments.config as payments_config
import massgov.pfml.payments.mock.payments_test_scenario_generator as scenario_generator
import massgov.pfml.payments.outbound_returns as outbound_returns
import massgov.pfml.payments.payments_util as payments_util
import massgov.pfml.util.files as file_util
from massgov.pfml.db.models.employees import (
    EmployeeReferenceFile,
    LkReferenceFileType,
    PaymentReferenceFile,
    ReferenceFileType,
)
from massgov.pfml.db.models.factories import EmployeeReferenceFileFactory, ReferenceFileFactory

### Outbound Vendor Return values

# All of the outbound vendor return sections have these static values
outbound_vendor_shared_attributes = {
    "DOC_CAT": "VCUST",
    "DOC_TYP": "VCC",
    "DOC_CD": "VCC",
    "DOC_DEPT_CD": payments_util.Constants.COMPTROLLER_DEPT_CODE,
    "DOC_UNIT_CD": payments_util.Constants.COMPTROLLER_UNIT_CODE,
}

# Default elements for the VC_DOC_VCUST
vc_doc_vcust_attributes = {
    "ORG_TYP": "1",
    "COMP_NM": None,
    "TIN_TYP": "2",
    "TRCK_NO": None,
}

vc_doc_ad_attributes = {
    "AD_ID": payments_util.Constants.COMPTROLLER_AD_ID,
    "CNTAC_NO": "PC001",
    "PRIN_CNTAC": "NONE PROVIDED",
}

# We expect two of these sections because we supplied two (nearly identical) sections
vc_doc_ad_attributes_pa = {"AD_TYP": "PA", "DOC_AD_LN_NO": "1"}

vc_doc_ad_attributes_pr = {"AD_TYP": "PR", "DOC_AD_LN_NO": "2"}

### Outbound Payment Return Values
pymt_retn_doc_attributes = {
    "PY_CD": "GAX",
    "PY_DEPT": "EOL",
    "PY_VEND_LN": "1",
    "PY_COMM_LN": None,
    "PY_ACTG_LN": "1",
    "DISB_CAT": "C",
    "DISB_TYP": "350",
    "DISB_DEPT": "EOL",
    "VEND_INV_NO": "MULTILINE",
}


### Status Return Values

shared_status_doc_attributes = {
    "DEPT_CD": payments_util.Constants.COMPTROLLER_DEPT_CODE,
    "UNIT_CD": payments_util.Constants.COMPTROLLER_UNIT_CODE,
}

shared_status_doc_elements = {
    "DOC_DEPT_CD": payments_util.Constants.COMPTROLLER_DEPT_CODE,
    "DOC_UNIT_CD": payments_util.Constants.COMPTROLLER_UNIT_CODE,
    # Comptroller will return the following elements but our code does not inspect them.
    "DOC_VERS_NO": 1,
    "DOC_FUNC_CD": "1 - New",
    "DOC_STA_CD": "4 - Submitted",
}

example_status_doc_errors = [
    ("W0048", "Street name not found in directory. (W0048)"),
    ("A2416", "Vendor is required per options on Event Type/Document Control (A2416)"),
    ("", "Invalid Vendor/Customer Code"),
]


def add_vendor_record(
    xml_document: minidom.Document,
    document_root: minidom.Element,
    scenario_data: scenario_generator.ScenarioData,
    doc_id: str,
):
    # Grab all the values together
    employee = scenario_data.employee
    first_name = employee.first_name
    middle_name = employee.middle_name
    last_name = employee.last_name
    ssn = employee.tax_identifier.tax_identifier
    vendor_customer_code = employee.ctr_vendor_customer_code

    address = employee.ctr_address_pair.fineos_address
    address_line_1 = address.address_line_one
    address_line_2 = address.address_line_two
    city = address.city
    state = address.geo_state.geo_state_description
    zip_code = address.zip_code

    # Add an AMS_DOCUMENT, each represent one record returned (but made up of multiple separate elements)
    ams_document = xml_document.createElement("AMS_DOCUMENT")
    ams_doc_attributes = {"DOC_ID": doc_id}
    ams_doc_attributes.update(outbound_vendor_shared_attributes.copy())
    payments_util.add_attributes(ams_document, ams_doc_attributes)
    document_root.appendChild(ams_document)

    # Add the VC_DOC_VCUST
    vc_doc_vcust = xml_document.createElement("VC_DOC_VCUST")
    payments_util.add_attributes(vc_doc_vcust, {"AMSDataObject": "Y"})
    ams_document.appendChild(vc_doc_vcust)

    # Add the individual VC_DOC_VCUST values
    vc_doc_vcust_elements = {
        "DOC_ID": doc_id,
        "FRST_NM": first_name,
        "MID_NM": middle_name,
        "LAST_NM": last_name,
        "TIN": ssn,
        "VEND_CUST_CD": vendor_customer_code,
        "ORG_VEND_CUST_CD": vendor_customer_code,
    }
    vc_doc_vcust_elements.update(outbound_vendor_shared_attributes.copy())
    vc_doc_vcust_elements.update(vc_doc_vcust_attributes.copy())
    payments_util.add_cdata_elements(
        vc_doc_vcust, xml_document, vc_doc_vcust_elements, add_y_attribute=False
    )

    # There are two VC_DOC_AD sections that differ in a few static values
    # First generate all of their shared values
    vc_doc_ad_elements = {
        "DOC_ID": doc_id,
        "STR_1_NM": address_line_1,
        "STR_2_NM": address_line_2,
        "CITY_NM": city,
        "ST": state,
        "ZIP": zip_code,
    }
    vc_doc_ad_elements.update(outbound_vendor_shared_attributes.copy())
    vc_doc_ad_elements.update(vc_doc_ad_attributes.copy())

    # Add the first VC_DOC_AD for the PA address type.
    vc_doc_ad_pa = xml_document.createElement("VC_DOC_AD")
    payments_util.add_attributes(vc_doc_ad_pa, {"AMSDataObject": "Y"})
    ams_document.appendChild(vc_doc_ad_pa)

    # Add VC_DOC_AD values for PA address type
    vc_doc_ad_pa_elements = vc_doc_ad_elements.copy()
    vc_doc_ad_pa_elements.update(vc_doc_ad_attributes_pa.copy())
    payments_util.add_cdata_elements(
        vc_doc_ad_pa, xml_document, vc_doc_ad_pa_elements, add_y_attribute=False
    )

    # Add the second VC_DOC_AD for the PR address type.
    vc_doc_ad_pr = xml_document.createElement("VC_DOC_AD")
    payments_util.add_attributes(vc_doc_ad_pr, {"AMSDataObject": "Y"})
    ams_document.appendChild(vc_doc_ad_pr)

    # Add the VC_DOC_AD values for PR address type
    vc_doc_ad_pr_elements = vc_doc_ad_elements.copy()
    vc_doc_ad_pr_elements.update(vc_doc_ad_attributes_pr.copy())
    payments_util.add_cdata_elements(
        vc_doc_ad_pr, xml_document, vc_doc_ad_pr_elements, add_y_attribute=False
    )


def add_broken_vendor_record(
    xml_document: minidom.Document, document_root: minidom.Element, doc_id: str
):
    # This broken record is based on a bad one we received which had a few values set
    # at seemingly random. Just reproducing it here as closely as possible

    ams_document = xml_document.createElement("AMS_DOCUMENT")
    ams_doc_attributes = {
        "DOC_ID": doc_id,
        "DOC_CAT": None,  # This is null compared to normal
        "DOC_CD": "VCC",
        "DOC_DEPT_CD": "EOL",
        "DOC_UNIT_CD": "8770",
    }
    payments_util.add_attributes(ams_document, ams_doc_attributes)
    document_root.appendChild(ams_document)

    # Add the VC_DOC_VCUST
    vc_doc_vcust = xml_document.createElement("VC_DOC_VCUST")
    payments_util.add_attributes(vc_doc_vcust, {"AMSDataObject": "Y"})
    ams_document.appendChild(vc_doc_vcust)

    # Most of the elements we are expecting back are missing
    # Only doc_id isn't static
    vc_doc_vcust_elements = {
        "DOC_CAT": None,
        "DOC_TYP": None,
        "DOC_CD": "VCC",
        "DOC_ID": doc_id,
        "DOC_DEPT_CD": "EOL",
        "DOC_UNIT_CD": "8770",
    }
    payments_util.add_cdata_elements(
        vc_doc_vcust, xml_document, vc_doc_vcust_elements, add_y_attribute=False
    )


def _generate_outbound_vendor_return(scenario_datasets: List[scenario_generator.ScenarioData]):
    xml_document = minidom.Document()

    document_root = xml_document.createElement("AMS_DOC_XML_IMPORT_FILE")
    payments_util.add_attributes(document_root, {"VERSION": "1.0"})
    xml_document.appendChild(document_root)

    for scenario_data in scenario_datasets:
        try:
            # Many scenarios don't get to the point where we would expect
            # a vendor return, so skip them.
            if not scenario_data.scenario_descriptor.has_outbound_vendor_return:
                continue

            employee_reference_files = [
                ref_file
                for ref_file in scenario_data.employee.reference_files
                if ref_file.__class__ == EmployeeReferenceFile
                and ref_file.reference_file.reference_file_type_id
                == ReferenceFileType.VCC.reference_file_type_id
            ]
            if not employee_reference_files:
                # When generating an Outbound Vender Return without running the scenario,
                # there will be no pre-existing VCC EmployeeReferenceFile.
                ref_file = ReferenceFileFactory.create(
                    reference_file_type_id=ReferenceFileType.VCC.reference_file_type_id
                )
                employee_reference_file = EmployeeReferenceFileFactory.create(
                    employee=scenario_data.employee, reference_file=ref_file
                )
            else:
                # We assume that this scenario has an associated EmployeeReferenceFile
                # and take the first one.
                employee_reference_file = employee_reference_files[0]

            doc_id = employee_reference_file.ctr_document_identifier.ctr_document_identifier

            # To test scenarios where they send us a garbage file, individual records
            # can be overriden to be broken which causes most values to be missing/null
            if scenario_data.scenario_descriptor.has_broken_outbound_vendor_return:
                add_broken_vendor_record(xml_document, document_root, doc_id)
            else:
                add_vendor_record(xml_document, document_root, scenario_data, doc_id)
        except Exception:
            print(
                "Error trying to generate outbound vendor return for scenario",
                scenario_data.scenario_descriptor.scenario_name,
            )
            raise

    return xml_document


def _generate_outbound_payment_return(scenario_datasets: List[scenario_generator.ScenarioData]):
    xml_document = minidom.Document()

    document_root = xml_document.createElement("AMS_DOC_XML_IMPORT_FILE")
    payments_util.add_attributes(document_root, {"VERSION": "1.0"})
    xml_document.appendChild(document_root)

    for count, scenario_data in enumerate(scenario_datasets):
        # Many scenarios don't get to the point where we would expect
        # a payment return, so skip them
        if not scenario_data.scenario_descriptor.has_outbound_payment_return:
            continue

        # We assume that this scenario has an associated PaymentReferenceFile
        for payment in scenario_data.payments:
            payment_reference_files = [
                ref_file
                for ref_file in payment.reference_files
                if ref_file.__class__ == PaymentReferenceFile
                and ref_file.reference_file.reference_file_type_id
                == ReferenceFileType.GAX.reference_file_type_id
            ]
            payment_reference_file_count = len(payment_reference_files)
            if not payment_reference_file_count == 1:
                raise Exception(
                    f"Expect a single PaymentReferenceFile for this scenario. Found {payment_reference_file_count} PaymentReferenceFiles."
                )

            payment_reference_file = payment_reference_files[0]
            doc_id = payment_reference_file.ctr_document_identifier.ctr_document_identifier

            # Pull all the values out first that we'll need
            vendor_code = scenario_data.employee.ctr_vendor_customer_code

            # Calculate a few values that just use the incrementing count
            py_id = doc_id
            chk_no = "{:011}".format(count)
            now = payments_util.get_now().strftime("%Y-%m-%d")
            amount = payment.amount

            # Add the PYMT_RETN_DOC
            pymt_retn_doc = xml_document.createElement("PYMT_RETN_DOC")
            document_root.appendChild(pymt_retn_doc)

            # Add the individual PYMT_RETN_DOC values
            pymt_retn_doc_elements = {
                "PY_ID": py_id,
                "VEND_CD": vendor_code,
                "LINE_AMT": amount,  # We don't check this field in processing
                "CHK_NO": chk_no,
                "CHK_AM": amount,
                "CHK_EFT_ISS_DT": now,
            }
            pymt_retn_doc_elements.update(pymt_retn_doc_attributes.copy())
            payments_util.add_cdata_elements(pymt_retn_doc, xml_document, pymt_retn_doc_elements)

    return xml_document


def _generate_outbound_status_return_xml_document(
    scenario_datasets: List[scenario_generator.ScenarioData], ref_file_type: LkReferenceFileType
) -> minidom.Document:
    xml_document = minidom.Document()

    document_root = xml_document.createElement(
        outbound_returns.OUTBOUND_STATUS_RETURN_XML_DOC_ROOT_ELEMENT
    )
    payments_util.add_attributes(document_root, {"VERSION": "1.0"})
    xml_document.appendChild(document_root)

    for scenario_data in scenario_datasets:
        if (
            scenario_data.scenario_descriptor.has_vcc_status_return
            and ref_file_type.reference_file_type_id == ReferenceFileType.VCC.reference_file_type_id
        ):
            doc = _generate_outbound_status_return_document_for_vcc(xml_document, scenario_data)
            document_root.appendChild(doc)

        if (
            scenario_data.scenario_descriptor.has_gax_status_return
            and ref_file_type.reference_file_type_id == ReferenceFileType.GAX.reference_file_type_id
        ):
            docs = _generate_outbound_status_return_document_for_gax(xml_document, scenario_data)
            for doc in docs:
                document_root.appendChild(doc)

    return xml_document


def _generate_outbound_status_return_document_for_gax(
    xml_document: minidom.Document, scenario_data: scenario_generator.ScenarioData
) -> List[minidom.Element]:
    transaction_type = "GAX"

    phase_code = payments_util.Constants.DOC_PHASE_CD_FINAL_STATUS
    if scenario_data.scenario_descriptor.has_gax_status_pending_ctr_action:
        phase_code = "2 - Pending"

    status_returns = []

    # We assume that this scenario has an associated PaymentReferenceFile
    for payment in scenario_data.payments:
        payment_reference_files = [
            ref_file
            for ref_file in payment.reference_files
            if ref_file.__class__ == PaymentReferenceFile
            and ref_file.reference_file.reference_file_type_id
            == ReferenceFileType.GAX.reference_file_type_id
        ]
        payment_reference_file_count = len(payment_reference_files)
        if not payment_reference_file_count == 1:
            raise Exception(
                f"Expect a single PaymentReferenceFile for this scenario. Found {payment_reference_file_count} PaymentReferenceFiles."
            )

        payment_reference_file = payment_reference_files[0]
        batch_id = payment_reference_file.reference_file.ctr_batch_identifier.ctr_batch_identifier
        document_id = payment_reference_file.ctr_document_identifier.ctr_document_identifier

        attrs = {
            "TRAN_CD": transaction_type,
            # Comptroller will return the following elements but our code does not inspect them.
            "BATCH_ID": batch_id,
            "IMP_DT": payments_util.get_now().strftime("%Y-%m-%d"),
        }

        elems = {"DOC_CD": transaction_type, "DOC_ID": document_id, "DOC_PHASE_CD": phase_code}

        has_errors = scenario_data.scenario_descriptor.has_gax_status_return_errors

        status_returns.append(
            _generate_outbound_status_return_document(xml_document, attrs, elems, has_errors)
        )

    return status_returns


def _generate_outbound_status_return_document_for_vcc(
    xml_document: minidom.Document, scenario_data: scenario_generator.ScenarioData
) -> minidom.Element:
    transaction_type = "VCC"

    # We assume that this scenario has an associated EmployeeReferenceFile
    employee_reference_files = [
        ref_file
        for ref_file in scenario_data.employee.reference_files
        if ref_file.__class__ == EmployeeReferenceFile
        and ref_file.reference_file.reference_file_type_id
        == ReferenceFileType.VCC.reference_file_type_id
    ]
    employee_reference_file_count = len(employee_reference_files)
    if not employee_reference_file_count == 1:
        raise Exception(
            f"Expect a single EmployeeReferenceFile for this scenario. Found {employee_reference_file_count} EmployeeReferenceFiles."
        )

    employee_reference_file = employee_reference_files[0]
    batch_id = employee_reference_file.reference_file.ctr_batch_identifier.ctr_batch_identifier
    document_id = employee_reference_file.ctr_document_identifier.ctr_document_identifier

    attrs = {
        "TRAN_CD": transaction_type,
        # Comptroller will return the following elements but our code does not inspect them.
        "BATCH_ID": batch_id,
        "IMP_DT": payments_util.get_now().strftime("%Y-%m-%d"),
    }

    elems = {
        "DOC_CD": transaction_type,
        "DOC_ID": document_id,
        # We expect VCCs to always be in the "3 - Final" phase.
        "DOC_PHASE_CD": payments_util.Constants.DOC_PHASE_CD_FINAL_STATUS,
    }

    has_errors = scenario_data.scenario_descriptor.has_vcc_status_return_errors

    return _generate_outbound_status_return_document(xml_document, attrs, elems, has_errors)


def _generate_outbound_status_return_document(
    xml_document: minidom.Document,
    attrs: Dict[str, Any],
    elements: Dict[str, Any],
    has_errors: bool,
) -> minidom.Element:
    # Add an AMS_DOCUMENT, each represent one record returned (but made up of multiple separate elements)
    ams_document = xml_document.createElement("AMS_DOCUMENT")
    attrs.update(shared_status_doc_attributes.copy())
    payments_util.add_attributes(ams_document, attrs)

    # Add all elements except for the error element.
    elements.update(shared_status_doc_elements.copy())
    add_cdata_elements(ams_document, xml_document, elements)

    errors_element = _create_errors_element_for_status_return_document(xml_document, has_errors)
    ams_document.appendChild(errors_element)

    return ams_document


def _create_errors_element_for_status_return_document(
    xml_document: minidom.Document, has_errors: bool
) -> minidom.Element:
    # Our code only cares if there are any errors. We do not care how many errors there are (as long
    # as there is more than 0), nor what those errors are.
    # Comptroller will return a maximum of 3 errors, even if there are more than 3 errors.

    errors_element = xml_document.createElement("ERRORS")
    error_count = 0

    if has_errors:
        error_count = randint(1, 3)
        # errors = example_status_doc_errors[0:error_count]
        # for error in errors:
        #     code = error[0]
        #     descr = error[1]

    # Adding this sub element for now because our parser doesn't like it when the ERRORS element
    # has no children.
    error_node = xml_document.createElement("ERROR")
    error_node.setAttribute("ERROR_CD", "code")
    cdata = xml_document.createCDATASection("descr")
    error_node.appendChild(cdata)
    errors_element.appendChild(error_node)

    errors_element.setAttribute("NO_OF_ERRORS", str(error_count))

    return errors_element


# payments_util.add_cdata_elements() adds an attribute "Attribute=Y" and uppercases elements.
# For status returns we don't want that behaviour.
def add_cdata_elements(
    parent: minidom.Element, document: minidom.Document, elements: Dict[str, Any]
) -> None:
    for key, val in elements.items():
        elem = document.createElement(key)
        parent.appendChild(elem)
        cdata = document.createCDATASection(str(val))
        elem.appendChild(cdata)


def write_file(
    file_name: str, folder_path: str, date_group_str: str, xml_document: minidom.Document
):
    timed_file_name = "-".join([date_group_str, file_name])
    full_path = os.path.join(folder_path, timed_file_name)

    file_content = xml_document.toprettyxml(indent="   ", encoding="ISO-8859-1")
    _handle, tempfile_path = tempfile.mkstemp()
    temp_file = file_util.write_file(tempfile_path, mode="wb")
    temp_file.write(file_content)
    temp_file.close()

    if file_util.is_sftp_path(full_path):
        config = payments_config.get_moveit_config()
        sftp_client = file_util.get_sftp_client(
            uri=config.ctr_moveit_sftp_uri,
            ssh_key_password=config.ctr_moveit_ssh_key_password,
            ssh_key=config.ctr_moveit_ssh_key,
        )
        sftp_client.put(tempfile_path, full_path, confirm=False)
    else:
        with file_util.write_file(full_path, mode="wb") as xml_file:
            xml_file.write(file_content)
        # Create EmployeeReferenceFiles since we are bypassing MOVEit.
        ReferenceFileFactory.create(
            file_location=full_path,
            reference_file_type_id=ReferenceFileType.OUTBOUND_VENDOR_CUSTOMER_RETURN.reference_file_type_id,
        )


# === Main Generator Functions ===
OUTBOUND_VENDOR_RETURN_FILE_NAME = "outbound-vendor-return.xml"
OUTBOUND_STATUS_RETURN_FILE_NAME = "outbound-status-return.xml"
OUTBOUND_PAYMENT_RETURN_FILE_NAME = "outbound-payment-return.xml"


# VCC
def generate_outbound_vendor_return(
    scenario_datasets: List[scenario_generator.ScenarioData], folder_path: str, date_group_str: str
):
    xml_document = _generate_outbound_vendor_return(scenario_datasets)
    write_file(OUTBOUND_VENDOR_RETURN_FILE_NAME, folder_path, date_group_str, xml_document)


# GAX
def generate_outbound_payment_return(
    scenario_datasets: List[scenario_generator.ScenarioData], folder_path: str, date_group_str: str
):
    xml_document = _generate_outbound_payment_return(scenario_datasets)
    write_file(OUTBOUND_PAYMENT_RETURN_FILE_NAME, folder_path, date_group_str, xml_document)


# VCC or GAX
def generate_outbound_status_return(
    scenario_datasets: List[scenario_generator.ScenarioData],
    folder_path: str,
    date_group_str: str,
    ref_file_type: LkReferenceFileType,
):
    xml_document = _generate_outbound_status_return_xml_document(scenario_datasets, ref_file_type)
    write_file(OUTBOUND_STATUS_RETURN_FILE_NAME, folder_path, date_group_str, xml_document)
