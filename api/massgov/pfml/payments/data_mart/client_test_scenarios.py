import enum
import json
import os
from enum import Enum
from typing import Dict, Optional, Union

import massgov.pfml.db as pfml_db
import massgov.pfml.payments.payments_util as payments_util
from massgov.pfml.db.models.employees import Employee, TaxIdentifier
from massgov.pfml.payments.data_mart.client import Client
from massgov.pfml.payments.data_mart.core import EFTStatus, VendorActiveStatus, VendorInfoResult
from massgov.pfml.payments.mock.payments_test_scenario_generator import ScenarioName
from massgov.pfml.util import assert_never


class TestScenarioResult(Enum):
    VENDOR_DOES_NOT_EXIST = enum.auto()
    VENDOR_EXISTS_MISSING_ADDRESS = enum.auto()
    VENDOR_EXISTS_DIFFERENT_ADDRESS = enum.auto()
    VENDOR_EXISTS_DIFFERENT_ROUTING = enum.auto()
    VENDOR_MATCHES_AND_EFT_NOT_ELIGIBILE = enum.auto()
    VENDOR_MATCHES_AND_EFT_ELIGIBLE = enum.auto()
    VENDOR_MATCHES_AND_EFT_PENDING = enum.auto()
    VENDOR_MATCHES_AND_EFT_ELIGIBLE_NO_VENDOR_CODE = enum.auto()


TEST_SCENARIO_DOES_NOT_EXIST_THEN_MATCHES_AND_EFT_NOT_ELIGIBLE = {
    "round1": TestScenarioResult.VENDOR_DOES_NOT_EXIST,
    "round2": TestScenarioResult.VENDOR_MATCHES_AND_EFT_NOT_ELIGIBILE,
}

TEST_SCENARIO_DOES_NOT_EXIST_THEN_MATCHES_AND_EFT_ELIGIBLE = {
    "round1": TestScenarioResult.VENDOR_DOES_NOT_EXIST,
    "round2": TestScenarioResult.VENDOR_MATCHES_AND_EFT_ELIGIBLE,
}

TEST_SCENARIO_DOES_NOT_EXIST_THEN_MATCHES_AND_EFT_PENDING = {
    "round1": TestScenarioResult.VENDOR_DOES_NOT_EXIST,
    "round2": TestScenarioResult.VENDOR_MATCHES_AND_EFT_PENDING,
}

TEST_SCENARIO_EMPLOYEES_TO_CONFIG: Dict[
    str, Union[Dict[str, TestScenarioResult], TestScenarioResult]
] = {
    ScenarioName.SCENARIO_A.value: TEST_SCENARIO_DOES_NOT_EXIST_THEN_MATCHES_AND_EFT_NOT_ELIGIBLE,
    ScenarioName.SCENARIO_B.value: TEST_SCENARIO_DOES_NOT_EXIST_THEN_MATCHES_AND_EFT_NOT_ELIGIBLE,
    ScenarioName.SCENARIO_C.value: TEST_SCENARIO_DOES_NOT_EXIST_THEN_MATCHES_AND_EFT_PENDING,
    ScenarioName.SCENARIO_D.value: TEST_SCENARIO_DOES_NOT_EXIST_THEN_MATCHES_AND_EFT_PENDING,
    ScenarioName.SCENARIO_M.value: TestScenarioResult.VENDOR_DOES_NOT_EXIST,
    ScenarioName.SCENARIO_N.value: TestScenarioResult.VENDOR_MATCHES_AND_EFT_NOT_ELIGIBILE,
    ScenarioName.SCENARIO_O.value: TEST_SCENARIO_DOES_NOT_EXIST_THEN_MATCHES_AND_EFT_NOT_ELIGIBLE,
    ScenarioName.SCENARIO_P.value: TEST_SCENARIO_DOES_NOT_EXIST_THEN_MATCHES_AND_EFT_NOT_ELIGIBLE,
    ScenarioName.SCENARIO_Q.value: TEST_SCENARIO_DOES_NOT_EXIST_THEN_MATCHES_AND_EFT_PENDING,
    ScenarioName.SCENARIO_R.value: TEST_SCENARIO_DOES_NOT_EXIST_THEN_MATCHES_AND_EFT_NOT_ELIGIBLE,
    ScenarioName.SCENARIO_S.value: TEST_SCENARIO_DOES_NOT_EXIST_THEN_MATCHES_AND_EFT_NOT_ELIGIBLE,
    ScenarioName.SCENARIO_U.value: TestScenarioResult.VENDOR_EXISTS_MISSING_ADDRESS,
    ScenarioName.SCENARIO_V.value: TestScenarioResult.VENDOR_EXISTS_DIFFERENT_ADDRESS,
    ScenarioName.SCENARIO_W.value: TestScenarioResult.VENDOR_EXISTS_DIFFERENT_ROUTING,
    ScenarioName.SCENARIO_X.value: TEST_SCENARIO_DOES_NOT_EXIST_THEN_MATCHES_AND_EFT_NOT_ELIGIBLE,
    ScenarioName.SCENARIO_Y.value: TEST_SCENARIO_DOES_NOT_EXIST_THEN_MATCHES_AND_EFT_ELIGIBLE,
    ScenarioName.SCENARIO_Z.value: TEST_SCENARIO_DOES_NOT_EXIST_THEN_MATCHES_AND_EFT_NOT_ELIGIBLE,
}


def get_test_scenario_ssn_to_logical_id_map() -> Dict[str, Dict[str, str]]:
    ssn_to_logical_id_map = dict()

    if ssn_to_logical_id_map_str := os.getenv("CTR_DATA_MART_MOCK_SSN_TO_LOGICAL_ID_MAP"):
        ssn_to_logical_id_map = json.loads(ssn_to_logical_id_map_str)

    return ssn_to_logical_id_map


def get_test_scenario_for_employee(
    ssn_to_logical_id_map: Dict[str, Dict[str, str]], vendor_tin: str, round_id: str
) -> TestScenarioResult:
    test_scenario_struct = ssn_to_logical_id_map.get(vendor_tin)
    if not test_scenario_struct:
        return TestScenarioResult.VENDOR_DOES_NOT_EXIST

    test_scenario_employee = test_scenario_struct["scenario_name"]
    test_scenario_config = TEST_SCENARIO_EMPLOYEES_TO_CONFIG.get(test_scenario_employee)

    if not test_scenario_config:
        return TestScenarioResult.VENDOR_DOES_NOT_EXIST

    if isinstance(test_scenario_config, TestScenarioResult):
        return test_scenario_config

    test_scenario_result_for_round = test_scenario_config.get(round_id)

    if not test_scenario_result_for_round:
        raise ValueError(
            f"No result was provided for round {round_id}, scenario name: {test_scenario_employee}"
        )

    return test_scenario_result_for_round


def get_vendor_customer_code_from_ssn_map(
    ssn_to_logical_id_map: Dict[str, Dict[str, str]], vendor_tin: str,
) -> Optional[str]:
    if test_scenario_struct := ssn_to_logical_id_map.get(vendor_tin):
        return test_scenario_struct.get("vendor_customer_code")

    return None


def create_complete_valid_matching_vendor_info_for_employee(
    employee: Employee, vendor_customer_code: Optional[str],
) -> VendorInfoResult:
    # Similar function exists in tests/helpers/data_mart, but requires an
    # address be present, if this can be updated with that constraint, could
    # have the test helper just export this function instead of having a
    # separate version.
    if not employee.ctr_address_pair:
        addr = None
    else:
        addr = employee.ctr_address_pair.fineos_address

    return VendorInfoResult(
        vendor_customer_code=vendor_customer_code
        or employee.ctr_vendor_customer_code
        or str(employee.employee_id),
        vendor_active_status=VendorActiveStatus.ACTIVE,
        eft_status=EFTStatus.ELIGIBILE_FOR_EFT,
        generate_eft_payment=True,
        aba_no=employee.eft.routing_nbr if employee.eft else None,
        address_id=payments_util.Constants.COMPTROLLER_AD_ID,
        street_1=addr.address_line_one if addr else None,
        street_2=addr.address_line_two if addr else None,
        city=addr.city if addr else None,
        zip_code=addr.zip_code if addr else None,
        state=addr.geo_state.geo_state_description if addr and addr.geo_state else None,
        country_code=addr.country.country_description if addr and addr.country else None,
    )


def generate_test_scenario_vendor_info(
    employee: Employee,
    test_scenario_result: TestScenarioResult,
    vendor_customer_code: Optional[str],
) -> Optional[VendorInfoResult]:
    if test_scenario_result is TestScenarioResult.VENDOR_DOES_NOT_EXIST:
        return None

    if test_scenario_result is TestScenarioResult.VENDOR_EXISTS_MISSING_ADDRESS:
        vendor_info = create_complete_valid_matching_vendor_info_for_employee(
            employee, vendor_customer_code
        )
        vendor_info.address_id = None
        vendor_info.street_1 = None
        vendor_info.street_2 = None
        vendor_info.city = None
        vendor_info.zip_code = None
        vendor_info.state = None
        vendor_info.country_code = None
        return vendor_info

    if test_scenario_result is TestScenarioResult.VENDOR_EXISTS_DIFFERENT_ADDRESS:
        vendor_info = create_complete_valid_matching_vendor_info_for_employee(
            employee, vendor_customer_code
        )
        vendor_info.street_1 = (
            vendor_info.street_1 + "_mod" if vendor_info.street_1 else "dummy_value"
        )
        return vendor_info

    if test_scenario_result is TestScenarioResult.VENDOR_EXISTS_DIFFERENT_ROUTING:
        vendor_info = create_complete_valid_matching_vendor_info_for_employee(
            employee, vendor_customer_code
        )
        vendor_info.aba_no = vendor_info.aba_no + "_mod" if vendor_info.aba_no else "dummy_value"
        return vendor_info

    if test_scenario_result is TestScenarioResult.VENDOR_MATCHES_AND_EFT_NOT_ELIGIBILE:
        vendor_info = create_complete_valid_matching_vendor_info_for_employee(
            employee, vendor_customer_code
        )

        vendor_info.eft_status = EFTStatus.NOT_ELIGIBILE_FOR_EFT
        vendor_info.generate_eft_payment = False
        return vendor_info

    if test_scenario_result is TestScenarioResult.VENDOR_MATCHES_AND_EFT_ELIGIBLE:
        vendor_info = create_complete_valid_matching_vendor_info_for_employee(
            employee, vendor_customer_code
        )
        return vendor_info

    if test_scenario_result is TestScenarioResult.VENDOR_MATCHES_AND_EFT_ELIGIBLE_NO_VENDOR_CODE:
        vendor_info = create_complete_valid_matching_vendor_info_for_employee(
            employee, vendor_customer_code
        )
        vendor_info.vendor_customer_code = None
        return vendor_info

    if test_scenario_result is TestScenarioResult.VENDOR_MATCHES_AND_EFT_PENDING:
        vendor_info = create_complete_valid_matching_vendor_info_for_employee(
            employee, vendor_customer_code
        )
        vendor_info.eft_status = EFTStatus.PRENOTE_PENDING
        vendor_info.generate_eft_payment = False
        return vendor_info

    assert_never(test_scenario_result)


class TestScenariosClient(Client):
    def __init__(
        self,
        pfml_db_session: pfml_db.Session,
        ssn_to_logical_id_map: Optional[Dict[str, Dict[str, str]]] = None,
    ):
        self.pfml_db_session = pfml_db_session

        if ssn_to_logical_id_map is None:
            ssn_to_logical_id_map = get_test_scenario_ssn_to_logical_id_map()

        self.ssn_to_logical_id_map = ssn_to_logical_id_map

    def get_vendor_info(self, vendor_tin: str) -> Optional[VendorInfoResult]:
        round_id = os.getenv("CTR_DATA_MART_MOCK_ROUND", "round1")
        test_scenario_result = get_test_scenario_for_employee(
            self.ssn_to_logical_id_map, vendor_tin, round_id
        )
        vendor_customer_code = get_vendor_customer_code_from_ssn_map(
            self.ssn_to_logical_id_map, vendor_tin
        )
        employee = (
            self.pfml_db_session.query(Employee)
            .join(TaxIdentifier)
            .filter(TaxIdentifier.tax_identifier == vendor_tin)
            .one_or_none()
        )

        if not employee:
            return None

        return generate_test_scenario_vendor_info(
            employee, test_scenario_result, vendor_customer_code
        )
