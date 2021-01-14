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
        ssn_to_logical_id_map[employee.tax_identifier.tax_identifier] = logical_id

    return (employees, ssn_to_logical_id_map)


def assert_matches_and_eft_eligible(employee, vendor_info):
    matching_info = data_mart_test_scenarios.create_complete_valid_matching_vendor_info_for_employee(
        employee
    )
    assert vendor_info == matching_info


def assert_matches_and_not_eft_eligible(employee, vendor_info):
    matching_info = data_mart_test_scenarios.create_complete_valid_matching_vendor_info_for_employee(
        employee
    )
    matching_info.generate_eft_payment = False
    matching_info.eft_status = data_mart_core.EFTStatus.NOT_ELIGIBILE_FOR_EFT
    assert vendor_info == matching_info


def assert_missing_address(employee, vendor_info):
    matching_info = data_mart_test_scenarios.create_complete_valid_matching_vendor_info_for_employee(
        employee
    )
    matching_info.address_id = None
    matching_info.street_1 = None
    matching_info.street_2 = None
    matching_info.city = None
    matching_info.zip_code = None
    matching_info.state = None
    matching_info.country_code = None
    assert vendor_info == matching_info


def assert_different_address(employee, vendor_info):
    matching_info = data_mart_test_scenarios.create_complete_valid_matching_vendor_info_for_employee(
        employee
    )

    # street should be different
    assert vendor_info.street_1 != matching_info.street_1

    # but removing from the equation, they should be equal
    matching_info.street_1 = None
    vendor_info.street_1 = None
    assert vendor_info == matching_info


def assert_different_routing(employee, vendor_info):
    matching_info = data_mart_test_scenarios.create_complete_valid_matching_vendor_info_for_employee(
        employee
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
            logical_id = ssn_to_logical_id_map[employee.tax_identifier.tax_identifier]
            vendor_info = data_mart_client.get_vendor_info(employee.tax_identifier.tax_identifier)

            if (
                logical_id == "EmployeeA"
                or logical_id == "EmployeeB"
                or logical_id == "EmployeeC"
                or logical_id == "EmployeeD"
                or logical_id == "EmployeeR"
                or logical_id == "EmployeeS"
            ):
                if round_id == "round1":
                    assert vendor_info is None
                else:
                    assert_matches_and_eft_eligible(employee, vendor_info)
            elif (
                logical_id == "EmployeeM"
                or logical_id == "EmployeeO"
                or logical_id == "EmployeeP"
                or logical_id == "EmployeeQ"
            ):
                assert vendor_info is None
            elif logical_id == "EmployeeN":
                assert_matches_and_eft_eligible(employee, vendor_info)
            elif logical_id == "EmployeeU":
                assert_missing_address(employee, vendor_info)
            elif logical_id == "EmployeeV":
                assert_different_address(employee, vendor_info)
            elif logical_id == "EmployeeW":
                assert_different_routing(employee, vendor_info)
            elif logical_id == "EmployeeX":
                if round_id == "round1":
                    assert vendor_info is None
                else:
                    assert_matches_and_not_eft_eligible(employee, vendor_info)
            elif logical_id == "EmployeeY":
                if round_id == "round1":
                    assert vendor_info is None
                else:
                    assert_matches_and_eft_eligible(employee, vendor_info)
            else:
                raise AssertionError(f"Unknown logical_id: {logical_id}")
