import pytest

import massgov.pfml.payments.data_mart.client_test_scenarios as data_mart_test_scenarios
import massgov.pfml.payments.data_mart.core as data_mart_core
from massgov.pfml.db.models.factories import CtrAddressPairFactory, EftFactory, EmployeeFactory


@pytest.fixture
def test_scenario_employees_and_map(initialize_factories_session):
    employees = []
    ssn_to_logical_id_map = dict()
    for logical_id in data_mart_test_scenarios.TEST_SCENARIO_EMPLOYEES_TO_CONFIG:
        employee = EmployeeFactory.create(
            ctr_address_pair=CtrAddressPairFactory(), eft=EftFactory()
        )
        employees.append(employee)
        ssn_to_logical_id_map[employee.tax_identifier.tax_identifier] = {
            "scenario_name": logical_id
        }

    return (employees, ssn_to_logical_id_map)


def assert_matches_and_eft_eligible(employee, vendor_info, vendor_customer_code=None):
    matching_info = data_mart_test_scenarios.create_complete_valid_matching_vendor_info_for_employee(
        employee, vendor_customer_code
    )
    assert vendor_info == matching_info


def assert_matches_and_eft_pending(employee, vendor_info, vendor_customer_code=None):
    matching_info = data_mart_test_scenarios.create_complete_valid_matching_vendor_info_for_employee(
        employee, vendor_customer_code
    )
    matching_info.generate_eft_payment = False
    matching_info.eft_status = data_mart_core.EFTStatus.PRENOTE_PENDING
    assert vendor_info == matching_info


def assert_matches_and_not_eft_eligible(employee, vendor_info, vendor_customer_code=None):
    matching_info = data_mart_test_scenarios.create_complete_valid_matching_vendor_info_for_employee(
        employee, vendor_customer_code
    )
    matching_info.generate_eft_payment = False
    matching_info.eft_status = data_mart_core.EFTStatus.NOT_ELIGIBILE_FOR_EFT
    assert vendor_info == matching_info


def assert_missing_address(employee, vendor_info, vendor_customer_code=None):
    matching_info = data_mart_test_scenarios.create_complete_valid_matching_vendor_info_for_employee(
        employee, vendor_customer_code
    )
    matching_info.address_id = None
    matching_info.street_1 = None
    matching_info.street_2 = None
    matching_info.city = None
    matching_info.zip_code = None
    matching_info.state = None
    matching_info.country_code = None
    assert vendor_info == matching_info


def assert_different_address(employee, vendor_info, vendor_customer_code=None):
    matching_info = data_mart_test_scenarios.create_complete_valid_matching_vendor_info_for_employee(
        employee, vendor_customer_code
    )

    # street should be different
    assert vendor_info.street_1 != matching_info.street_1

    # but removing from the equation, they should be equal
    matching_info.street_1 = None
    vendor_info.street_1 = None
    assert vendor_info == matching_info


def assert_different_routing(employee, vendor_info, vendor_customer_code=None):
    matching_info = data_mart_test_scenarios.create_complete_valid_matching_vendor_info_for_employee(
        employee, vendor_customer_code
    )

    # aba_no should be different
    assert vendor_info.aba_no != matching_info.aba_no

    # but removing from the equation, they should be equal
    matching_info.aba_no = None
    vendor_info.aba_no = None
    assert vendor_info == matching_info


@pytest.mark.integration
def test_test_scenarios_client(test_db_session, test_scenario_employees_and_map, monkeypatch):
    (test_scenario_employees, ssn_to_logical_id_map) = test_scenario_employees_and_map
    data_mart_client = data_mart_test_scenarios.TestScenariosClient(
        test_db_session, ssn_to_logical_id_map
    )

    for round_id in ["round1", "round2"]:
        monkeypatch.setenv("CTR_DATA_MART_MOCK_ROUND", round_id)
        for employee in test_scenario_employees:
            logical_id = ssn_to_logical_id_map[employee.tax_identifier.tax_identifier][
                "scenario_name"
            ]
            vendor_info = data_mart_client.get_vendor_info(employee.tax_identifier.tax_identifier)

            if (
                logical_id == "A"
                or logical_id == "B"
                or logical_id == "O"
                or logical_id == "P"
                or logical_id == "R"
                or logical_id == "S"
                or logical_id == "X"
                or logical_id == "Z"
            ):
                if round_id == "round1":
                    assert vendor_info is None
                else:
                    assert_matches_and_not_eft_eligible(employee, vendor_info)
            elif logical_id == "C" or logical_id == "D" or logical_id == "Q":
                if round_id == "round1":
                    assert vendor_info is None
                else:
                    assert_matches_and_eft_pending(employee, vendor_info)
            elif logical_id == "M":
                assert vendor_info is None
            elif logical_id == "N":
                assert_matches_and_not_eft_eligible(employee, vendor_info)
            elif logical_id == "U":
                assert_missing_address(employee, vendor_info)
            elif logical_id == "V":
                assert_different_address(employee, vendor_info)
            elif logical_id == "W":
                assert_different_routing(employee, vendor_info)
            elif logical_id == "Y":
                if round_id == "round1":
                    assert vendor_info is None
                else:
                    assert_matches_and_eft_eligible(employee, vendor_info)
            else:
                raise AssertionError(f"Unknown logical_id: {logical_id}")


def test_test_scenarios_client_with_vendor_customer_code(
    initialize_factories_session, test_db_session, monkeypatch
):
    logical_id = "A"
    vendor_customer_code = "19891213"
    employee = EmployeeFactory.create(ctr_address_pair=CtrAddressPairFactory(), eft=EftFactory())
    vendor_tin = employee.tax_identifier.tax_identifier

    ssn_to_logical_id_map = {
        vendor_tin: {"scenario_name": logical_id, "vendor_customer_code": vendor_customer_code,}
    }

    data_mart_client = data_mart_test_scenarios.TestScenariosClient(
        test_db_session, ssn_to_logical_id_map
    )

    monkeypatch.setenv("CTR_DATA_MART_MOCK_ROUND", "round2")
    vendor_info = data_mart_client.get_vendor_info(vendor_tin)

    assert_matches_and_not_eft_eligible(employee, vendor_info, vendor_customer_code)
    assert vendor_info.vendor_customer_code == vendor_customer_code
