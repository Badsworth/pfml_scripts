"""
Test suite to simulate 4 Day E2E Payments Processing.

Test Scenarios: https://docs.google.com/spreadsheets/d/1iKLc5FA18twZhef3L0piDjpTmtwQ4NZPcqEpEAqwyss/edit?ts=5ff514a5#gid=1222845626
Steps: https://docs.google.com/spreadsheets/d/1iKLc5FA18twZhef3L0piDjpTmtwQ4NZPcqEpEAqwyss/edit?ts=5ff514a5#gid=0
Flow Chart: https://app.lucidchart.com/lucidchart/cc28b7fa-f0eb-4039-bb04-63fc7e6e25a3/edit?beaconFlowId=E87E2DB65199B23E&page=0_0#
"""
import csv
import json
import logging  # noqa: B1
import os
import uuid
from collections import Counter
from typing import Dict, List

from freezegun import freeze_time
from smart_open import open as smart_open

import massgov.pfml.payments.config as payments_config
import massgov.pfml.payments.mock.ctr_outbound_file_generator as ctr_outbound_returns_generator
import massgov.pfml.payments.mock.fineos_extract_generator as fineos_extract_generator
import massgov.pfml.payments.mock.payments_test_scenario_generator as test_scenario_data_generator
import massgov.pfml.payments.payments_util as payments_util
import massgov.pfml.util.datetime as datetime_util
import massgov.pfml.util.files as file_util
from massgov.pfml import db
from massgov.pfml.api.util.state_log_util import AssociatedClass
from massgov.pfml.db.models.employees import (
    Claim,
    CtrDocumentIdentifier,
    Employee,
    EmployeeLog,
    EmployeeReferenceFile,
    Employer,
    EmployerLog,
    LatestStateLog,
    LkReferenceFileType,
    LkState,
    Payment,
    ReferenceFile,
    ReferenceFileType,
    StateLog,
)
from massgov.pfml.payments.fineos_payment_export import CiIndex
from massgov.pfml.payments.mock.ctr_outbound_file_generator import OUTBOUND_VENDOR_RETURN_FILE_NAME
from massgov.pfml.payments.mock.fineos_extract_generator import (
    FINEOS_PAYMENT_EXPORT_FILES,
    FINEOS_VENDOR_EXPORT_FILES,
)
from massgov.pfml.payments.mock.payments_test_scenario_expected_states import (
    TestStage,
    get_scenario_expected_states,
)
from massgov.pfml.payments.mock.payments_test_scenario_generator import (
    SCENARIO_DESCRIPTORS,
    ScenarioData,
    ScenarioDataConfig,
    ScenarioName,
    ScenarioNameWithCount,
)
from massgov.pfml.payments.process_ctr_payments import Configuration as CTRTaskConfiguration
from massgov.pfml.payments.process_ctr_payments import _ctr_process as run_ctr_ecs_task
from massgov.pfml.payments.process_payments import Configuration as FineosTaskConfiguration
from massgov.pfml.payments.process_payments import _fineos_process as run_fineos_ecs_task


# == Helper data structures
class TestScenarioDataSet:
    def __init__(self, scenario_dataset: List[ScenarioData]):
        self.scenario_dataset = scenario_dataset

        # create map
        self.scenario_dataset_map: Dict[ScenarioName, List[ScenarioData]] = {}
        self.employee_id_scenario_name: Dict[uuid.UUID, ScenarioName] = {}

        for scenario_data in scenario_dataset:
            scenario_name: ScenarioName = scenario_data.scenario_descriptor.scenario_name

            if self.scenario_dataset_map.get(scenario_name) is None:
                self.scenario_dataset_map[scenario_name] = []

            self.scenario_dataset_map[scenario_name].append(scenario_data)

            self.employee_id_scenario_name[scenario_data.employee.employee_id] = scenario_name

    def get_scenario_name_by_employee_id(self, employee_id: uuid.UUID) -> ScenarioName:
        return self.employee_id_scenario_name[employee_id]

    def get_employee_ids_by_scenario(self, scenario_name: ScenarioName) -> List[uuid.UUID]:
        if not self.scenario_dataset_map.get(scenario_name):
            return []

        return [
            scenario_data.employee.employee_id
            for scenario_data in self.scenario_dataset_map.get(scenario_name)
        ]

    def get_fineos_customer_numbers_by_scenario(self, scenario_name: ScenarioName) -> List[str]:
        if not self.scenario_dataset_map.get(scenario_name):
            return []
        return [
            scenario_data.employee_customer_number
            for scenario_data in self.scenario_dataset_map.get(scenario_name)
        ]

    def get_payment_ci_index_by_scenario(self, scenario_name: ScenarioName) -> List[str]:
        if not self.scenario_dataset_map.get(scenario_name):
            return []
        return [
            scenario_data.ci_index for scenario_data in self.scenario_dataset_map.get(scenario_name)
        ]

    def get_all_employee_ids(self) -> List[uuid.UUID]:
        return [scenario_data.employee.employee_id for scenario_data in self.scenario_dataset]

    def get_total_count(self):
        return len(self.scenario_dataset)


# == E2E Test ==
def test_e2e_process(
    test_db_session,
    mock_fineos_s3_bucket,
    setup_mock_sftp_client,
    mock_sftp_client,
    mock_ses,
    set_exporter_env_vars,
    initialize_factories_session,
    monkeypatch,
    logging_fix,
    caplog,
    create_triggers,
):
    caplog.set_level(logging.INFO)  # noqa: B1
    monkeypatch.setenv("FINEOS_VENDOR_MAX_HISTORY_DATE", "2019-12-31")
    monkeypatch.setenv("FINEOS_PAYMENT_MAX_HISTORY_DATE", "2019-12-31")
    # Common
    s3_config = payments_config.get_s3_config()
    move_it_config = payments_config.get_moveit_config()

    email_sent_count = 0

    # ========================================================================
    # Data Setup - Mirror DOR Import + Claim Application
    # ========================================================================

    # Setup the testing scenario data (generate one of each)
    test_scenarios_with_count: List[ScenarioNameWithCount] = [
        ScenarioNameWithCount(scenario_name, 1) for scenario_name in SCENARIO_DESCRIPTORS.keys()
    ]
    test_scenario_config: ScenarioDataConfig = ScenarioDataConfig(
        scenario_config=test_scenarios_with_count
    )
    scenario_dataset: List[ScenarioData] = test_scenario_data_generator.generate_scenario_dataset(
        test_scenario_config
    )

    test_scenario_dataset = TestScenarioDataSet(scenario_dataset=scenario_dataset)
    total_scenario_count = test_scenario_dataset.get_total_count()

    # Confirm generated data expectations in db
    employees = test_db_session.query(Employee).all()
    employers = test_db_session.query(Employer).all()
    claims = test_db_session.query(Claim).all()
    payments = test_db_session.query(Payment).all()

    assert len(employees) == total_scenario_count
    assert len(employers) == total_scenario_count
    assert len(claims) == total_scenario_count
    assert len(payments) == 0

    employer_logs_start = test_db_session.query(EmployerLog).all()

    with freeze_time("2020-11-30 12:00:00"):

        # Set file date prefix to current day
        date_group_str = payments_util.get_now().strftime("%Y-%m-%d-%H-%M-%S")
        date_prefix = f"{date_group_str}-"

        # ========================================================================
        # [Night before Day 1] Generate FINEOS vendor extract files
        # ========================================================================

        # Generate mock extract files
        fineos_extract_generator.generate_vendor_extract_files(
            scenario_dataset, folder_path=s3_config.fineos_data_export_path, date_prefix=date_prefix
        )

        # Confirm expected vendor files were generated
        assert_files(
            folder_path=s3_config.fineos_data_export_path,
            expected_files=FINEOS_VENDOR_EXPORT_FILES,
            file_prefix=date_prefix,
        )

    with freeze_time("2020-12-01 12:00:00"):

        day_1_datetime_str = payments_util.get_now().strftime("%Y-%m-%d-%H-%M-%S")

        # Note: Use file date prefix from previous day's generated files

        # ========================================================================
        # [Day 1] Run the FINEOS ECS task - Process Vendor Exract
        # ========================================================================

        # Run the task
        run_fineos_ecs_task(test_db_session, FineosTaskConfiguration(["--steps", "ALL"]))
        log_counts = get_log_message_counts(caplog)

        # Confirm employee state logs
        assert_employee_state_log_by_scenario(
            test_db_session, test_scenario_dataset, TestStage.FINEOS_PROCESS_VENDOR_FILES
        )

        # Confirm that files were moved to s3 pfml processed folder
        processed_vendor_folder_path = os.path.join(
            s3_config.pfml_fineos_inbound_path,
            payments_util.Constants.S3_INBOUND_PROCESSED_DIR,
            payments_util.get_date_group_folder_name(
                date_group_str, ReferenceFileType.VENDOR_CLAIM_EXTRACT
            ),
        )
        assert_files(
            folder_path=processed_vendor_folder_path,
            expected_files=FINEOS_VENDOR_EXPORT_FILES,
            file_prefix=date_prefix,
        )

        # Confirm reference files were created
        date_group_folder = payments_util.get_date_group_folder_name(
            date_group_str, ReferenceFileType.VENDOR_CLAIM_EXTRACT
        )
        file_location = os.path.join(
            s3_config.pfml_fineos_inbound_path,
            payments_util.Constants.S3_INBOUND_PROCESSED_DIR,
            date_group_folder,
        )
        assert_reference_file(
            test_db_session, ReferenceFileType.VENDOR_CLAIM_EXTRACT, file_location
        )

        # Confirm employee reference files were created
        employee_reference_files = test_db_session.query(EmployeeReferenceFile).all()
        assert (
            len(employee_reference_files) == total_scenario_count - 5
        )  # for skipped E, F, K, L, T

        exclude_scenarios: List[ScenarioName] = [
            ScenarioName.SCENARIO_E,
            ScenarioName.SCENARIO_F,
            ScenarioName.SCENARIO_K,
            ScenarioName.SCENARIO_L,
            ScenarioName.SCENARIO_T,
        ]

        assert_employee_reference_file(
            test_db_session,
            test_scenario_dataset,
            ReferenceFileType.VENDOR_CLAIM_EXTRACT,
            file_location,
            exclude_scenarios,
        )

        # Confirm that 2 error reports were generated
        assert_error_reports(
            {
                "CPS-payment-export-error-report.csv": [],
                "CPS-vendor-export-error-report.csv": [
                    ScenarioName.SCENARIO_G,
                    ScenarioName.SCENARIO_H,
                    ScenarioName.SCENARIO_I,
                    ScenarioName.SCENARIO_J,
                ],
            },
            test_scenario_dataset,
        )

        # Confirm log error captures: E, F
        assert_vendor_errors(
            log_counts, [ScenarioName.SCENARIO_E, ScenarioName.SCENARIO_F], test_scenario_dataset
        )

        # Confirm skipped: E, F, K, L, T
        assert_no_employee_state_logs_by_scenario(
            test_db_session, test_scenario_dataset, ScenarioName.SCENARIO_E
        )
        assert_no_employee_state_logs_by_scenario(
            test_db_session, test_scenario_dataset, ScenarioName.SCENARIO_F
        )
        assert_no_employee_state_logs_by_scenario(
            test_db_session, test_scenario_dataset, ScenarioName.SCENARIO_K
        )
        assert_no_employee_state_logs_by_scenario(
            test_db_session, test_scenario_dataset, ScenarioName.SCENARIO_L
        )
        assert_no_employee_state_logs_by_scenario(
            test_db_session, test_scenario_dataset, ScenarioName.SCENARIO_T
        )

        # Confirm that error emails were sent
        expected_count = 1  # Vendor error reports
        assert_email_sent_count(
            log_counts=log_counts, previous_count=email_sent_count, expected_count=expected_count
        )
        email_sent_count += expected_count

        # ========================================================================
        # [Day 1] Run CTR ECS Task - Send VCC Export
        # ========================================================================

        # Setup Data Mart mock for round 1
        ssn_to_logical_id_map = {}
        for scenario_data in scenario_dataset:
            ssn = scenario_data.employee.tax_identifier.tax_identifier
            scenario_name = scenario_data.scenario_descriptor.scenario_name.value
            ssn_to_logical_id_map[ssn] = {"scenario_name": scenario_name}

        monkeypatch.setenv("CTR_DATA_MART_MOCK", "true")
        monkeypatch.setenv("CTR_DATA_MART_MOCK_ROUND", "round1")
        monkeypatch.setenv(
            "CTR_DATA_MART_MOCK_SSN_TO_LOGICAL_ID_MAP", json.dumps(ssn_to_logical_id_map)
        )

        # Run the task
        run_ctr_ecs_task(test_db_session, CTRTaskConfiguration(["--steps", "ALL"]))
        log_counts = get_log_message_counts(caplog)

        # Confirm some CTR document ids were created
        ctr_doc_ids = test_db_session.query(CtrDocumentIdentifier).all()
        assert len(ctr_doc_ids) > 0

        # Confirm emplpyee state logs
        assert_employee_state_log_by_scenario(
            test_db_session, test_scenario_dataset, TestStage.CTR_EXPORT_VCC
        )

        # Confirm VCC file in pfml S3
        date_str = datetime_util.utcnow().strftime("%Y%m%d")
        batch_number = "10"
        vcc_base_name = "{}{}{}{}".format(
            payments_util.Constants.COMPTROLLER_DEPT_CODE,
            date_str,
            ReferenceFileType.VCC.reference_file_type_description,
            batch_number,
        )

        vcc_path_in_s3 = os.path.join(
            s3_config.pfml_ctr_outbound_path,
            payments_util.Constants.S3_OUTBOUND_SENT_DIR,
            vcc_base_name,
        )
        vcc_filenames = ["{}.DAT".format(vcc_base_name), "{}.INF".format(vcc_base_name)]
        sent_vcc_files_in_s3_after_day_1 = file_util.list_files(vcc_path_in_s3)
        assert len(sent_vcc_files_in_s3_after_day_1) == len(vcc_filenames)
        assert_expected_files_ends_in_list(sent_vcc_files_in_s3_after_day_1, vcc_filenames)
        assert_reference_file(test_db_session, ReferenceFileType.VCC, vcc_path_in_s3)

        # Confirm VCC file in CTR moveit
        files_in_moveit_after_day_1 = mock_sftp_client.listdir(
            move_it_config.ctr_moveit_outgoing_path
        )
        assert len(files_in_moveit_after_day_1) == len(vcc_filenames)
        assert_expected_files_ends_in_list(files_in_moveit_after_day_1, vcc_filenames)

        # Confirm all error reports found in S3 (2 from fineos task, 7 from ctr task)
        assert len(file_util.list_files(s3_config.pfml_error_reports_path, recursive=True)) == 9
        assert_error_reports(
            {
                "EFT-audit-error-report.csv": [],
                "EFT-error-report.csv": [],
                "GAX-error-report.csv": [],
                "VCC-error-report.csv": [],
                "VCM-report.csv": [
                    ScenarioName.SCENARIO_U,
                    ScenarioName.SCENARIO_V,
                    ScenarioName.SCENARIO_W,
                ],
                "payment-audit-error-report.csv": [],
                "vendor-audit-error-report.csv": [],
            },
            test_scenario_dataset,
        )

        # Confirm emails were sent
        expected_count = 2  # VCC + CTR Error Reports (No GAX file generated yet)
        assert_email_sent_count(
            log_counts=log_counts, previous_count=email_sent_count, expected_count=expected_count
        )
        email_sent_count += expected_count

        # ========================================================================
        # [Night of Day 1] Generate FINEOS Payment Extract files
        # ========================================================================

        # Switch file date prefix to current day
        date_group_str = payments_util.get_now().strftime("%Y-%m-%d-%H-%M-%S")
        date_prefix = f"{date_group_str}-"

        # Generate mock extract files
        fineos_extract_generator.generate_payment_extract_files(
            scenario_dataset, folder_path=s3_config.fineos_data_export_path, date_prefix=date_prefix
        )

        # Confirm expected vendor files were generated
        assert_files(
            folder_path=s3_config.fineos_data_export_path,
            expected_files=FINEOS_PAYMENT_EXPORT_FILES,
            file_prefix=date_prefix,
        )

        # ========================================================================
        # [Night of Day 1] Generate CTR VCC Outbound Return files
        # ========================================================================

        # Generate mock CTR files
        ctr_moveit_sftp_outbound_returns_path = move_it_config.ctr_moveit_incoming_path
        ctr_outbound_returns_generator.generate_outbound_vendor_return(
            scenario_dataset, ctr_moveit_sftp_outbound_returns_path, date_group_str
        )
        ctr_outbound_returns_generator.generate_outbound_status_return(
            scenario_dataset,
            ctr_moveit_sftp_outbound_returns_path,
            date_group_str,
            ReferenceFileType.VCC,
        )

        # Confirm files in sftp
        sftp_files = mock_sftp_client.listdir(ctr_moveit_sftp_outbound_returns_path)
        assert_expected_files_ends_in_list(sftp_files, [OUTBOUND_VENDOR_RETURN_FILE_NAME])

    with freeze_time("2020-12-02 12:00:00"):

        # Note: Use file date prefix from previous day's generated files

        # ========================================================================
        # [Day 2] Run the FINEOS ECS task - process payments
        # ========================================================================

        # Run the task
        run_fineos_ecs_task(test_db_session, FineosTaskConfiguration(["--steps", "ALL"]))
        log_counts = get_log_message_counts(caplog)

        # Confirm expected number of payments (Success: A-D, Z, Error: O-S)
        payments = test_db_session.query(Payment).all()
        assert len(payments) == 5

        # Confirm employee state logs have not been altered
        assert_employee_state_log_by_scenario(
            test_db_session, test_scenario_dataset, TestStage.CTR_EXPORT_VCC
        )

        # Confirm payment state logs
        assert_payment_state_log_by_scenario(
            test_db_session, test_scenario_dataset, TestStage.FINEOS_PROCESS_PAYMENT_FILES
        )

        # Confirm that files were moved to s3 pfml processed folder
        processed_vendor_folder_path = os.path.join(
            s3_config.pfml_fineos_inbound_path,
            payments_util.Constants.S3_INBOUND_PROCESSED_DIR,
            payments_util.get_date_group_folder_name(
                date_group_str, ReferenceFileType.PAYMENT_EXTRACT
            ),
        )
        assert_files(
            folder_path=processed_vendor_folder_path,
            expected_files=FINEOS_PAYMENT_EXPORT_FILES,
            file_prefix=date_prefix,
        )

        # Confirm file references were created
        date_group_folder = payments_util.get_date_group_folder_name(
            date_group_str, ReferenceFileType.PAYMENT_EXTRACT
        )
        file_location = os.path.join(
            s3_config.pfml_fineos_inbound_path,
            payments_util.Constants.S3_INBOUND_PROCESSED_DIR,
            date_group_folder,
        )
        assert_reference_file(test_db_session, ReferenceFileType.PAYMENT_EXTRACT, file_location)

        # Confirm error report files in pfml S3
        assert_error_reports(
            {
                "CPS-payment-export-error-report.csv": [
                    ScenarioName.SCENARIO_O,
                    ScenarioName.SCENARIO_P,
                    ScenarioName.SCENARIO_Q,
                    ScenarioName.SCENARIO_R,
                    ScenarioName.SCENARIO_S,
                ],
                "CPS-vendor-export-error-report.csv": [],
            },
            test_scenario_dataset,
        )

        # Confirm PEI Writeback file in pfml archive s3 + fineos s3
        assert_pei_writeback(
            False,
            [
                ScenarioName.SCENARIO_A,
                ScenarioName.SCENARIO_B,
                ScenarioName.SCENARIO_C,
                ScenarioName.SCENARIO_D,
                ScenarioName.SCENARIO_Z,
            ],
            test_scenario_dataset,
        )

        # Confirm emails were sent
        expected_count = 1  # Vendor error reports
        assert_email_sent_count(
            log_counts=log_counts, previous_count=email_sent_count, expected_count=expected_count
        )
        email_sent_count += expected_count

        # ========================================================================
        # [Day 2] Run CTR ECS task - Process Vendor Outbound Files, Send GAX Export
        # ========================================================================

        # Setup Data Mart mock for round 2
        monkeypatch.setenv("CTR_DATA_MART_MOCK_ROUND", "round2")

        # Run the task
        run_ctr_ecs_task(
            test_db_session, CTRTaskConfiguration(["--steps", "ALL"]),
        )
        log_counts = get_log_message_counts(caplog)

        # Confirm files were copied over from ctr moveit sftp to pfml s3
        pfml_ctr_outbound_vendor_inbound_path = os.path.join(
            s3_config.pfml_ctr_inbound_path, payments_util.Constants.S3_INBOUND_PROCESSED_DIR
        )
        assert_expected_files_ends_in_list(
            file_util.list_files(pfml_ctr_outbound_vendor_inbound_path),
            [OUTBOUND_VENDOR_RETURN_FILE_NAME],
        )

        # Confirm emplpyee state logs
        assert_employee_state_log_by_scenario(
            test_db_session, test_scenario_dataset, TestStage.CTR_EXPORT_GAX
        )

        # Confirm payment state logs
        assert_payment_state_log_by_scenario(
            test_db_session, test_scenario_dataset, TestStage.CTR_EXPORT_GAX
        )

        # Confirm GAX files in s3 folder
        date_str = datetime_util.utcnow().strftime("%Y%m%d")
        batch_number = "10"
        gax_base_name = "{}{}{}{}".format(
            payments_util.Constants.COMPTROLLER_DEPT_CODE,
            date_str,
            ReferenceFileType.GAX.reference_file_type_description,
            batch_number,
        )

        gax_path_in_s3 = os.path.join(
            s3_config.pfml_ctr_outbound_path,
            payments_util.Constants.S3_OUTBOUND_SENT_DIR,
            gax_base_name,
        )
        gax_filenames = ["{}.DAT".format(gax_base_name), "{}.INF".format(gax_base_name)]
        sent_gax_files_in_s3_after_day_2 = file_util.list_files(gax_path_in_s3)
        assert len(sent_gax_files_in_s3_after_day_2) == len(gax_filenames)
        assert_expected_files_ends_in_list(sent_gax_files_in_s3_after_day_2, gax_filenames)
        assert_reference_file(test_db_session, ReferenceFileType.GAX, gax_path_in_s3)

        # Confirm error report files in pfml S3
        assert_error_reports(
            {
                "EFT-audit-error-report.csv": [],
                "EFT-error-report.csv": [ScenarioName.SCENARIO_X],
                "GAX-error-report.csv": [],
                "VCC-error-report.csv": [],  # Add Scenario_M here once we fix it
                "VCM-report.csv": [],
                "payment-audit-error-report.csv": [],
                "vendor-audit-error-report.csv": [],
            },
            test_scenario_dataset,
        )

        # Confirm emails were sent
        expected_count = 2  # GAX + CTR Error Reports (No VCC file generated)
        assert_email_sent_count(
            log_counts=log_counts, previous_count=email_sent_count, expected_count=expected_count
        )
        email_sent_count += expected_count

        # ========================================================================
        # [Night of Day 2] Generate CTR outbound status and payment files files
        # ========================================================================

        # Switch file date prefix to current day
        date_group_str = payments_util.get_now().strftime("%Y-%m-%d-%H-%M-%S")
        day_2_datetime_str = date_group_str
        date_prefix = f"{date_group_str}-"

        # Refresh scneario data with payment objects
        refersh_scenario_dataset(test_db_session, test_scenario_dataset, include_payment=True)

        # Generate mock CTR files
        ctr_moveit_sftp_outbound_returns_path = move_it_config.ctr_moveit_incoming_path
        ctr_outbound_returns_generator.generate_outbound_payment_return(
            scenario_dataset, ctr_moveit_sftp_outbound_returns_path, date_group_str
        )
        ctr_outbound_returns_generator.generate_outbound_status_return(
            scenario_dataset,
            ctr_moveit_sftp_outbound_returns_path,
            date_group_str,
            ReferenceFileType.GAX,
        )

        # Confirm files in sftp
        gax_and_vcc_files = gax_filenames + vcc_filenames
        files_in_moveit_after_day_2 = mock_sftp_client.listdir(
            move_it_config.ctr_moveit_outgoing_path
        )
        assert len(files_in_moveit_after_day_2) == len(gax_and_vcc_files)
        assert_expected_files_ends_in_list(files_in_moveit_after_day_2, gax_and_vcc_files)

    with freeze_time("2020-12-03 12:00:00"):

        # Note: Use file date prefix from previous day's generated files

        # ========================================================================
        # [Day 3] Run the FINEOS ECS task - No-Op
        # ========================================================================

        # Run the task
        run_fineos_ecs_task(test_db_session, FineosTaskConfiguration(["--steps", "ALL"]))
        log_counts = get_log_message_counts(caplog)

        # Confirm emplpyee state logs were not altered
        assert_employee_state_log_by_scenario(
            test_db_session, test_scenario_dataset, TestStage.CTR_EXPORT_GAX
        )

        # Confirm payment state logs were not altered
        assert_payment_state_log_by_scenario(
            test_db_session, test_scenario_dataset, TestStage.CTR_EXPORT_GAX
        )

        # Confirm error report files in pfml S3 (but empty as it is a no-op)
        assert_error_reports(
            {"CPS-payment-export-error-report.csv": [], "CPS-vendor-export-error-report.csv": []},
            test_scenario_dataset,
        )

        # Confirm emails were sent regardless of it being a no-op
        expected_count = 1  # Vendor Error Report
        assert_email_sent_count(
            log_counts=log_counts, previous_count=email_sent_count, expected_count=expected_count
        )
        email_sent_count += expected_count

        # ========================================================================
        # [Day 3] Run the CTR ECS task - Process Outbound Returns
        # ========================================================================

        # Run the task
        run_ctr_ecs_task(
            test_db_session, CTRTaskConfiguration(["--steps", "ALL"]),
        )
        log_counts = get_log_message_counts(caplog)

        # VCC-related comptroller return files were generated on day 1.
        vendor_return_filename = "{}-{}".format(
            day_1_datetime_str, ctr_outbound_returns_generator.OUTBOUND_VENDOR_RETURN_FILE_NAME
        )
        day1_status_return_filename = "{}-{}".format(
            day_1_datetime_str, ctr_outbound_returns_generator.OUTBOUND_STATUS_RETURN_FILE_NAME
        )
        # GAX-related comptroller return files were generated on day 2.
        payment_return_filename = "{}-{}".format(
            day_2_datetime_str, ctr_outbound_returns_generator.OUTBOUND_PAYMENT_RETURN_FILE_NAME
        )
        day2_status_return_filename = "{}-{}".format(
            day_2_datetime_str, ctr_outbound_returns_generator.OUTBOUND_STATUS_RETURN_FILE_NAME
        )

        # Confirm files were copied over from ctr moveit sftp to pfml s3
        comptroller_return_filenames = [
            vendor_return_filename,
            day1_status_return_filename,
            payment_return_filename,
            day2_status_return_filename,
        ]
        processed_dir = os.path.join(
            s3_config.pfml_ctr_inbound_path, payments_util.Constants.S3_INBOUND_PROCESSED_DIR,
        )
        ctr_return_files_in_s3_after_day_3 = file_util.list_files(processed_dir)
        assert len(ctr_return_files_in_s3_after_day_3) == len(comptroller_return_filenames)
        assert_expected_files_ends_in_list(
            ctr_return_files_in_s3_after_day_3, comptroller_return_filenames
        )

        # Confirm ReferenceFiles were created for the outbound return files we saved in S3.
        assert_reference_file(
            test_db_session,
            ReferenceFileType.OUTBOUND_VENDOR_CUSTOMER_RETURN,
            os.path.join(processed_dir, vendor_return_filename),
        )
        assert_reference_file(
            test_db_session,
            ReferenceFileType.OUTBOUND_STATUS_RETURN,
            os.path.join(processed_dir, day1_status_return_filename),
        )
        assert_reference_file(
            test_db_session,
            ReferenceFileType.OUTBOUND_PAYMENT_RETURN,
            os.path.join(processed_dir, payment_return_filename),
        )
        assert_reference_file(
            test_db_session,
            ReferenceFileType.OUTBOUND_STATUS_RETURN,
            os.path.join(processed_dir, day2_status_return_filename),
        )

        # Confirm emplpyee state logs were not altered
        assert_employee_state_log_by_scenario(
            test_db_session, test_scenario_dataset, TestStage.CTR_EXPORT_GAX
        )

        # Confirm payment state logs
        assert_payment_state_log_by_scenario(
            test_db_session,
            test_scenario_dataset,
            TestStage.CTR_PROCESS_OUTBOUND_STATUS_PAYMENT_RETURNS,
        )

        # Confirm error report files in pfml S3
        assert_error_reports(
            {
                "EFT-audit-error-report.csv": [],
                "EFT-error-report.csv": [],
                "GAX-error-report.csv": [ScenarioName.SCENARIO_Z],
                "VCC-error-report.csv": [],
                "VCM-report.csv": [],
                "payment-audit-error-report.csv": [],
                "vendor-audit-error-report.csv": [],
            },
            test_scenario_dataset,
        )

        # Confirm emails were sent
        expected_count = 1  # CTR Error Reports (No GAX/VCC file generated)
        assert_email_sent_count(
            log_counts=log_counts, previous_count=email_sent_count, expected_count=expected_count
        )
        email_sent_count += expected_count

    with freeze_time("2020-12-04 12:00:00"):

        # Switch file date prefix to current day
        date_group_str = payments_util.get_now().strftime("%Y-%m-%d-%H-%M-%S")
        date_prefix = f"{date_group_str}-"

        # ========================================================================
        # [Day 4] Run the FINEOS ECS task - PEI Writeback
        # ========================================================================

        # Run the task
        run_fineos_ecs_task(test_db_session, FineosTaskConfiguration(["--steps", "ALL"]))
        log_counts = get_log_message_counts(caplog)

        # Confirm previous employee states not altered
        assert_employee_state_log_by_scenario(
            test_db_session, test_scenario_dataset, TestStage.CTR_EXPORT_GAX
        )

        # Confirm payment states
        assert_payment_state_log_by_scenario(
            test_db_session, test_scenario_dataset, TestStage.FINEOS_PEI_WRITEBACK,
        )

        # Confirm PEI Writeback file in pfml archive s3 + fineos s3
        assert_pei_writeback(
            True,
            [
                ScenarioName.SCENARIO_A,
                ScenarioName.SCENARIO_B,
                ScenarioName.SCENARIO_C,
                ScenarioName.SCENARIO_D,
            ],
            test_scenario_dataset,
        )

        # Confirm error report files in pfml S3
        assert_error_reports(
            {"CPS-payment-export-error-report.csv": [], "CPS-vendor-export-error-report.csv": []},
            test_scenario_dataset,
        )

        # Confirm emails were sent
        expected_count = 1  # Vendor Reports
        assert_email_sent_count(
            log_counts=log_counts, previous_count=email_sent_count, expected_count=expected_count
        )
        email_sent_count += expected_count

        # ========================================================================
        # [Day 4] Run the CTR ECS task - No-Op
        # ========================================================================

        # Run the task
        run_ctr_ecs_task(
            test_db_session, CTRTaskConfiguration(["--steps", "ALL"]),
        )
        log_counts = get_log_message_counts(caplog)

        # Confirm emplpyee state logs were not altered
        assert_employee_state_log_by_scenario(
            test_db_session, test_scenario_dataset, TestStage.CTR_EXPORT_GAX
        )

        # Confirm payment state logs were not altered
        assert_payment_state_log_by_scenario(
            test_db_session, test_scenario_dataset, TestStage.FINEOS_PEI_WRITEBACK,
        )

        # Confirm error report files in pfml S3 (but empty as it is a no-op)
        assert_error_reports(
            {
                "EFT-audit-error-report.csv": [],
                "EFT-error-report.csv": [],
                "GAX-error-report.csv": [],
                "VCC-error-report.csv": [],
                "VCM-report.csv": [],
                "payment-audit-error-report.csv": [],
                "vendor-audit-error-report.csv": [],
            },
            test_scenario_dataset,
        )

        # Confirm emails were sent regardless of it being a no-op
        expected_count = 1  # Vendor Error Report
        assert_email_sent_count(
            log_counts=log_counts, previous_count=email_sent_count, expected_count=expected_count
        )
        email_sent_count += expected_count

    # Confirm we have not created any employer logs during process
    employer_logs_end = test_db_session.query(EmployerLog).all()
    employee_logs_end = test_db_session.query(EmployeeLog).all()

    assert len(employer_logs_start) == len(employer_logs_end)
    assert len(employee_logs_end) == len(employees)


def get_log_message_counts(caplog):
    # Create a dictionary of log messages to their counts
    return Counter(record.msg for record in caplog.records)


def assert_vendor_errors(log_counter, expected_scenarios, test_scenario_dataset):
    for scenario in expected_scenarios:
        fineos_customer_numbers = test_scenario_dataset.get_fineos_customer_numbers_by_scenario(
            scenario
        )
        for fineos_customer_number in fineos_customer_numbers:
            message = f"Employee in employee file with customer nbr {fineos_customer_number} not found in PFML DB."
            assert log_counter[message] == 1  # The log messages are unique


# Assertion helpers
def assert_files(folder_path, expected_files, file_prefix):
    files_in_folder = file_util.list_files(folder_path)
    for expected_file in expected_files:
        assert f"{file_prefix}{expected_file}" in files_in_folder


def _get_reference_file(
    db_session: db.Session, reference_file_type: LkReferenceFileType, file_location: str
):
    return (
        db_session.query(ReferenceFile)
        .filter(
            ReferenceFile.file_location == file_location,
            ReferenceFile.reference_file_type_id == reference_file_type.reference_file_type_id,
        )
        .one_or_none()
    )


def assert_reference_file(
    db_session: db.Session, reference_file_type: LkReferenceFileType, file_location: str
):
    reference_file = _get_reference_file(db_session, reference_file_type, file_location)
    assert reference_file is not None


def assert_employee_reference_file(
    db_session: db.Session,
    test_scenario_dataset: TestScenarioDataSet,
    reference_file_type: LkReferenceFileType,
    file_location: str,
    exclude_scenarios: List[ScenarioName],
):
    reference_file = _get_reference_file(db_session, reference_file_type, file_location)

    for scenario_data in test_scenario_dataset.scenario_dataset:
        scenario_name = scenario_data.scenario_descriptor.scenario_name
        if scenario_name in exclude_scenarios:
            continue

        employee_reference_file = (
            db_session.query(EmployeeReferenceFile)
            .filter(
                EmployeeReferenceFile.employee_id == scenario_data.employee.employee_id,
                EmployeeReferenceFile.reference_file_id == reference_file.reference_file_id,
            )
            .one_or_none()
        )

        assert (
            employee_reference_file is not None
        ), f"Expected employee reference file for scenario: {scenario_name}, {reference_file_type.reference_file_type_description}"


def assert_payment_state_log_by_scenario(
    db_session: db.Session, test_scenario_dataset: TestScenarioDataSet, test_stage: TestStage
):
    # Get the expected states
    (expected_states, expected_state_by_scenario_name,) = get_scenario_expected_states(
        test_stage, AssociatedClass.PAYMENT
    )

    # Get all payments and map
    payments = db_session.query(Payment).all()
    payment_ids = [payment.payment_id for payment in payments]

    filter_params = [
        StateLog.associated_type == AssociatedClass.PAYMENT.value,
        StateLog.payment_id.in_(payment_ids),
    ]
    state_logs: List[StateLog] = db_session.query(StateLog).join(LatestStateLog).filter(
        *filter_params
    ).all()

    state_logs_by_payment_id: Dict[uuid.UUID, List[LkState]] = {}
    for state_log in state_logs:
        if not state_logs_by_payment_id.get(state_log.payment_id):
            state_logs_by_payment_id[state_log.payment_id] = []

        state_logs_by_payment_id.get(state_log.payment_id).append(
            state_log.end_state.state_description
        )

    for payment in payments:
        scenario_name = test_scenario_dataset.get_scenario_name_by_employee_id(
            payment.claim.employee_id
        )
        expected_states = expected_state_by_scenario_name[scenario_name]
        expected_state_names = [
            expected_state.expected_state.state_description for expected_state in expected_states
        ]

        assert (
            state_logs_by_payment_id[payment.payment_id] == expected_state_names
        ), f"Error asserting payment state - {test_stage}, {scenario_name}, expected: {expected_state_names}, found: {state_logs_by_payment_id[payment.payment_id]}"

    # TODO validate error payment state logs without a payment - needs associated employee_id to be created


def assert_employee_state_log_by_scenario(
    db_session: db.Session, test_scenario_dataset: TestScenarioDataSet, test_stage: TestStage,
):
    # Get employees and create map
    filter_params = [
        StateLog.associated_type == AssociatedClass.EMPLOYEE.value,
        StateLog.employee_id.in_(test_scenario_dataset.get_all_employee_ids()),
    ]
    state_logs: List[StateLog] = db_session.query(StateLog).join(LatestStateLog).filter(
        *filter_params
    ).all()

    state_logs_by_employee_id: Dict[uuid.UUID, List[LkState]] = {}
    for state_log in state_logs:
        if not state_logs_by_employee_id.get(state_log.employee_id):
            state_logs_by_employee_id[state_log.employee_id] = []

        state_logs_by_employee_id.get(state_log.employee_id).append(
            state_log.end_state.state_description
        )

    # Check all expected states
    (expected_states, expected_state_by_scenario_name,) = get_scenario_expected_states(
        test_stage, AssociatedClass.EMPLOYEE
    )
    for scenario_expected_state in expected_states:
        scenario_employee_ids = test_scenario_dataset.get_employee_ids_by_scenario(
            scenario_expected_state.scenario_name
        )
        for employee_id in scenario_employee_ids:
            expected = scenario_expected_state.expected_state.state_description
            scenario_employee_end_states = state_logs_by_employee_id.get(employee_id)
            assert (
                expected in scenario_employee_end_states
            ), f"Error asserting employee state - {test_stage}, {scenario_expected_state.scenario_name}, expected: {expected}, found: {scenario_employee_end_states}"


def assert_no_employee_state_logs_by_scenario(
    db_session: db.Session, test_scenario_dataset: TestScenarioDataSet, scenario_name: ScenarioName,
):
    filter_params = [
        StateLog.associated_type == AssociatedClass.EMPLOYEE.value,
        StateLog.employee_id.in_(test_scenario_dataset.get_employee_ids_by_scenario(scenario_name)),
    ]
    state_logs: List[StateLog] = db_session.query(StateLog).join(LatestStateLog).filter(
        *filter_params
    ).all()

    assert (
        len(state_logs) == 0
    ), f"Error asserting skipped employee state for scenario: {scenario_name}, found at least one: {state_logs[0].end_state.state_description}"


def assert_error_reports(file_to_errored_scenarios, test_scenario_dataset):
    # Error reports are based on UTC (via the datetime_util)
    # so can't use the payments_util.get_now() here.
    today = datetime_util.utcnow()  # We freeze time for "day" of the run
    today_str = today.strftime("%Y-%m-%d")
    s3_config = payments_config.get_s3_config()
    folder_path = os.path.join(s3_config.pfml_error_reports_path, today_str)

    error_report_files = file_util.list_files(folder_path, recursive=True)

    for error_report_file in error_report_files:
        # The error_report_file looks like 2020-01-19-{FILENAME}.csv
        path = os.path.join(folder_path, error_report_file)

        # Need what type of file it is, so remove the beginning
        # Note, the date WILL change, but the length won't, so
        # this is fine to be static
        file_type = error_report_file[len("2020-01-19-") :]

        if file_type not in file_to_errored_scenarios.keys():
            continue  # Don't need to check for this file

        error_scenarios = file_to_errored_scenarios.get(file_type)

        with smart_open(path) as csv_file:
            dict_reader = csv.DictReader(csv_file, delimiter=",")
            error_records = list(dict_reader)
            assert len(error_records) == len(error_scenarios)

            if file_type == "CPS-payment-export-error-report.csv":
                # Because payment validation can fail before we
                # know anything about the payment, we need to parse out
                # the identifying number from the description
                # which happens to be the CiIndex

                # The first line of the description will be the CiIndex as a string
                errored_ci_indexes = [
                    error_record["Description of Issue"].split("\n")[0]
                    for error_record in error_records
                ]

                for error_scenario in error_scenarios:
                    expected_ci_indices = test_scenario_dataset.get_payment_ci_index_by_scenario(
                        error_scenario
                    )
                    expected_ci_indices_as_str = [str(ci_index) for ci_index in expected_ci_indices]

                    for ci_index in expected_ci_indices_as_str:
                        assert ci_index in errored_ci_indexes

            else:
                # Grab all the fineos customer numbers
                errored_fineos_customer_numbers = [
                    error_record["FINEOS Customer Number"] for error_record in error_records
                ]

                for error_scenario in error_scenarios:
                    expected_fineos_customer_numbers = test_scenario_dataset.get_fineos_customer_numbers_by_scenario(
                        error_scenario
                    )
                    for number in expected_fineos_customer_numbers:
                        assert number in errored_fineos_customer_numbers


def assert_pei_writeback(is_disbursed, expected_scenarios, test_scenario_dataset):
    s3_config = payments_config.get_s3_config()
    now_str = payments_util.get_now().strftime("%Y-%m-%d-%H-%M-%S")

    # List the files in the FINEOS bucket
    fineos_files = file_util.list_files(s3_config.fineos_data_import_path, recursive=True)

    # List the files in our bucket
    folder_path = os.path.join(
        s3_config.pfml_fineos_outbound_path, payments_util.Constants.S3_OUTBOUND_SENT_DIR
    )
    pei_writeback_files = file_util.list_files(folder_path, recursive=True)

    # The files should be identical in both places
    assert set(fineos_files) == set(pei_writeback_files)
    # And just to be certain, there should BE files
    assert len(pei_writeback_files) > 0

    writeback_file = None
    # There should only be a single writeback file
    # per day including all PEI updates back to FINEOS
    for pei_writeback_file in pei_writeback_files:
        if pei_writeback_file.startswith(now_str):
            writeback_file = pei_writeback_file
            break

    if not writeback_file:
        raise Exception(f"Unexpected scenario - No PEI writeback file found in S3 for {now_str}")

    path = os.path.join(folder_path, pei_writeback_file)

    with smart_open(path) as csv_file:
        dict_reader = csv.DictReader(csv_file, delimiter=",")
        records = list(dict_reader)
        assert len(records) == len(expected_scenarios)

        # Convert the records into a lookup dict using the C/I values as keys
        ci_records = {}
        for record in records:
            # Assert the C and I values are set
            c_value = record["pei_C_value"]
            i_value = record["pei_I_value"]
            assert c_value and i_value
            ci_records[CiIndex(c_value, i_value)] = record

        # for each scenario, lookup the record above with the CiIndex
        for scenario in expected_scenarios:
            ci_indices = test_scenario_dataset.get_payment_ci_index_by_scenario(scenario)
            for ci_index in ci_indices:
                record = ci_records.get(ci_index)
                assert record

                # Always set regardless of whether it is disbursed yet
                assert record["extractionDate"]
                assert record["transactionStatus"]

                # These fields only set if records disbursed (after going through the entire flow)
                if is_disbursed:
                    assert record["stockNo"]
                    assert record["transStatusDate"]


def assert_email_sent_count(log_counts, previous_count, expected_count):
    sent_count = log_counts["Email sent successfully."]
    assert (sent_count - previous_count) == expected_count


def refersh_scenario_dataset(
    db_session: db.Session,
    test_scenario_dataset: TestScenarioDataSet,
    include_payment: bool = False,
):
    payments: List[Payment] = db_session.query(Payment).all()
    payment_by_claim_id = {payment.claim_id: payment for payment in payments}

    for scenario_data in test_scenario_dataset.scenario_dataset:
        db_session.refresh(scenario_data.employee)
        db_session.refresh(scenario_data.claim)

        if include_payment:
            scenario_data.payment = payment_by_claim_id.get(scenario_data.claim.claim_id)


def assert_expected_files_ends_in_list(files_to_check, expected_files):
    for expected_file in expected_files:
        match = False
        for file_to_check in files_to_check:
            if file_to_check.endswith(expected_file):
                match = True

        assert match, f"Expected file {expected_file} not found in {files_to_check}"
