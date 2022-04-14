# See workflow here: https://lucid.app/lucidchart/edf54a33-1a3f-432d-82b7-157cf02667a4/edit?page=T9dnksYTkKxE#
# See implementation design here: https://lwd.atlassian.net/wiki/spaces/API/pages/1478918156/Local+E2E+Test+Suite

import csv
import json
import logging  # noqa: B1
import os
import re
from dataclasses import asdict
from typing import Any, Dict, List, Optional, Tuple, Type
from unittest import mock

import pytest
from freezegun import freeze_time
from sqlalchemy import func

import massgov.pfml.api.util.state_log_util as state_log_util
import massgov.pfml.delegated_payments.delegated_config as payments_config
import massgov.pfml.delegated_payments.delegated_payments_util as payments_util
import massgov.pfml.experian.address_validate_soap.client as soap_api
import massgov.pfml.util.files as file_util
from massgov.pfml import db
from massgov.pfml.db.models.employees import (
    Claim,
    ImportLog,
    ImportLogReportQueue,
    Payment,
    PaymentMethod,
    PaymentTransactionType,
    PrenoteState,
    PubError,
    ReferenceFile,
    ReferenceFileType,
)
from massgov.pfml.db.models.payments import (
    FineosExtractCancelledPayments,
    FineosExtractPaymentFullSnapshot,
    FineosExtractReplacedPayments,
    FineosExtractVbi1099DataSom,
    FineosExtractVpei,
    FineosExtractVpeiClaimDetails,
    FineosExtractVpeiPaymentDetails,
    FineosWritebackDetails,
    LkFineosWritebackTransactionStatus,
    Pfml1099Request,
)
from massgov.pfml.db.models.state import Flow, LkFlow, LkState, State
from massgov.pfml.delegated_payments.address_validation import AddressValidationStep
from massgov.pfml.delegated_payments.audit.delegated_payment_audit_csv import (
    PAYMENT_AUDIT_CSV_HEADERS,
)
from massgov.pfml.delegated_payments.audit.delegated_payment_audit_report import (
    PaymentAuditReportStep,
)
from massgov.pfml.delegated_payments.audit.delegated_payment_rejects import PaymentRejectsStep
from massgov.pfml.delegated_payments.delegated_fineos_1099_extract import Data1099ExtractStep
from massgov.pfml.delegated_payments.delegated_fineos_claimant_extract import ClaimantExtractStep
from massgov.pfml.delegated_payments.delegated_fineos_payment_extract import PaymentExtractStep
from massgov.pfml.delegated_payments.delegated_fineos_pei_writeback import FineosPeiWritebackStep
from massgov.pfml.delegated_payments.delegated_fineos_related_payment_post_processing import (
    RelatedPaymentsPostProcessingStep,
)
from massgov.pfml.delegated_payments.delegated_fineos_related_payment_processing import (
    RelatedPaymentsProcessingStep,
)
from massgov.pfml.delegated_payments.fineos_extract_step import FineosExtractStep
from massgov.pfml.delegated_payments.mock.fineos_extract_data import (
    generate_claimant_data_files,
    generate_payment_extract_files,
    generate_payment_reconciliation_extract_files,
    generate_vbi_taskreport_som_extract_files,
)
from massgov.pfml.delegated_payments.mock.generate_check_response import PubCheckResponseGenerator
from massgov.pfml.delegated_payments.mock.generate_manual_pub_reject_response import (
    ManualPubRejectResponseGenerator,
)
from massgov.pfml.delegated_payments.mock.pub_ach_response_generator import PubACHResponseGenerator
from massgov.pfml.delegated_payments.mock.scenario_data_generator import (
    ScenarioData,
    ScenarioDataConfig,
    ScenarioNameWithCount,
    generate_scenario_dataset,
    get_mock_address_client,
)
from massgov.pfml.delegated_payments.mock.scenarios import (
    DELAYED_SCENARIO_DESCRIPTORS,
    SCENARIO_DESCRIPTORS,
    SCENARIO_DESCRIPTORS_BY_NAME,
    ScenarioDescriptor,
    ScenarioName,
)
from massgov.pfml.delegated_payments.payment_methods_split_step import PaymentMethodsSplitStep
from massgov.pfml.delegated_payments.pickup_response_files_step import PickupResponseFilesStep
from massgov.pfml.delegated_payments.postprocessing.payment_post_processing_step import (
    PaymentPostProcessingStep,
)
from massgov.pfml.delegated_payments.pub.process_check_return_step import ProcessCheckReturnFileStep
from massgov.pfml.delegated_payments.pub.process_manual_pub_rejection_step import (
    ProcessManualPubRejectionStep,
)
from massgov.pfml.delegated_payments.pub.process_nacha_return_step import ProcessNachaReturnFileStep
from massgov.pfml.delegated_payments.pub.transaction_file_creator import TransactionFileCreatorStep
from massgov.pfml.delegated_payments.reporting.delegated_payment_sql_report_step import ReportStep
from massgov.pfml.delegated_payments.reporting.delegated_payment_sql_reports import (
    CREATE_PUB_FILES_REPORTS,
    PROCESS_FINEOS_EXTRACT_REPORTS,
    PROCESS_FINEOS_RECONCILIATION_REPORTS,
    PROCESS_PUB_RESPONSES_REPORTS,
    ReportName,
    get_report_by_name,
)
from massgov.pfml.delegated_payments.state_cleanup_step import StateCleanupStep
from massgov.pfml.delegated_payments.step import Step
from massgov.pfml.delegated_payments.task.process_fineos_extracts import (
    Configuration as FineosTaskConfiguration,
)
from massgov.pfml.delegated_payments.task.process_fineos_extracts import (
    _process_fineos_extracts as run_fineos_ecs_task,
)
from massgov.pfml.delegated_payments.task.process_fineos_reconciliation_extracts import (
    Configuration as ProcessPaymentReconciliationExtractsConfiguration,
)
from massgov.pfml.delegated_payments.task.process_fineos_reconciliation_extracts import (
    _process_fineos_payment_reconciliation_extracts as run_process_fineos_payment_reconciliation_extracts,
)
from massgov.pfml.delegated_payments.task.process_pub_payments import (
    Configuration as ProcessPubPaymentsTaskConfiguration,
)
from massgov.pfml.delegated_payments.task.process_pub_payments import (
    _process_pub_payments as run_process_pub_payments_ecs_task,
)
from massgov.pfml.delegated_payments.task.process_pub_responses import (
    Configuration as ProcessPubResponsesTaskConfiguration,
)
from massgov.pfml.delegated_payments.task.process_pub_responses import (
    _process_pub_responses as run_process_pub_responses_ecs_task,
)
from massgov.pfml.delegated_payments.weekly_max.max_weekly_benefit_amount_validation_step import (
    MaxWeeklyBenefitAmountValidationStep,
)
from massgov.pfml.util.datetime import get_now_us_eastern

# == Constants ==

# These are the pairs of step+import types we expect
EXPECTED_STEPS_PROCESS_FINEOS_EXTRACTS = [
    (StateCleanupStep, ""),
    (FineosExtractStep, ReferenceFileType.FINEOS_CLAIMANT_EXTRACT.reference_file_type_description),
    (FineosExtractStep, ReferenceFileType.FINEOS_PAYMENT_EXTRACT.reference_file_type_description),
    (
        FineosExtractStep,
        ReferenceFileType.FINEOS_VBI_TASKREPORT_SOM_EXTRACT.reference_file_type_description,
    ),
    (ClaimantExtractStep, ""),
    (PaymentExtractStep, ""),
    (FineosExtractStep, ReferenceFileType.FINEOS_1099_DATA_EXTRACT.reference_file_type_description),
    (Data1099ExtractStep, ""),
    (AddressValidationStep, ""),
    (MaxWeeklyBenefitAmountValidationStep, ""),
    (PaymentPostProcessingStep, ""),
    (RelatedPaymentsProcessingStep, ""),
    (PaymentAuditReportStep, ""),
    (FineosPeiWritebackStep, ""),
    (ReportStep, ""),
]

EXPECTED_STEPS_PROCESS_PUB_PAYMENTS = [
    (PickupResponseFilesStep, ""),
    (PaymentRejectsStep, ""),
    (PaymentMethodsSplitStep, ""),
    (TransactionFileCreatorStep, ""),
    (RelatedPaymentsPostProcessingStep, ""),
    (FineosPeiWritebackStep, ""),
    (ReportStep, ""),
]

EXPECTED_STEPS_PROCESS_PUB_RESPONSES = [
    (PickupResponseFilesStep, ""),
    (ProcessNachaReturnFileStep, ""),
    (ProcessCheckReturnFileStep, ""),
    (ProcessCheckReturnFileStep, ""),
    (ProcessManualPubRejectionStep, ""),
    (FineosPeiWritebackStep, ""),
    (ReportStep, ""),
]

# The check file step won't run multiple times
EXPECTED_STEPS_PROCESS_PUB_RESPONSES_NO_FILES = [
    (PickupResponseFilesStep, ""),
    (ProcessNachaReturnFileStep, ""),
    (ProcessCheckReturnFileStep, ""),
    (ProcessManualPubRejectionStep, ""),
    (FineosPeiWritebackStep, ""),
    (ReportStep, ""),
]


# == Data Structures ==


class TestDataSet:
    def __init__(self, scenario_dataset: List[ScenarioData]):
        self.scenario_dataset = scenario_dataset
        self.scenario_dataset_map: Dict[ScenarioName, List[ScenarioData]] = {}

        for scenario_data in scenario_dataset:
            scenario_name: ScenarioName = scenario_data.scenario_descriptor.scenario_name

            if self.scenario_dataset_map.get(scenario_name) is None:
                self.scenario_dataset_map[scenario_name] = []
            self.scenario_dataset_map[scenario_name].append(scenario_data)

    def get_scenario_names(self, scenarios_to_filter: Optional[List[str]] = None) -> List[str]:
        filter_set = set()
        if scenarios_to_filter:
            filter_set.update(scenarios_to_filter)
        return [
            sd.scenario_descriptor.scenario_name
            for sd in self.scenario_dataset
            if sd.scenario_descriptor.scenario_name not in filter_set
        ]

    def get_scenario_data_by_name(
        self, scenario_name: ScenarioName
    ) -> Optional[List[ScenarioData]]:
        return self.scenario_dataset_map.get(scenario_name, None)

    def get_scenario_payments_by_scenario_name(self, scenario_name: ScenarioName) -> List[Payment]:
        scenario_data_items = self.get_scenario_data_by_name(scenario_name)

        payments = []
        if scenario_data_items is not None:
            for scenario_data in scenario_data_items:
                payment = scenario_data.additional_payment or scenario_data.payment
                if payment is not None:
                    payments.append(payment)

                if scenario_data.tax_withholding_payments:
                    payments.extend(scenario_data.tax_withholding_payments)

        return payments

    def is_payment_scenario(self, payment: Payment, scenario_name: ScenarioName):
        scenario_payments = self.get_scenario_payments_by_scenario_name(scenario_name)
        return payment.payment_id in [p.payment_id for p in scenario_payments]

    def get_scenario_data_by_payment_ci(self, c_value: str, i_value: str) -> Optional[ScenarioData]:
        for scenario_data in self.scenario_dataset:
            if (
                scenario_data.payment_c_value == c_value
                and scenario_data.payment_i_value == i_value
            ):
                return scenario_data

            elif (
                scenario_data.additional_payment_c_value == c_value
                and scenario_data.additional_payment_i_value == i_value
            ):
                return scenario_data

            elif (
                scenario_data.tax_withholding_payment_i_values
                and i_value in scenario_data.tax_withholding_payment_i_values
            ):
                return scenario_data

        return None

    def populate_scenario_data_payments(self, db_session) -> None:
        for scenario_data in self.scenario_dataset:
            payment = (
                db_session.query(Payment)
                .filter(
                    Payment.fineos_pei_c_value == scenario_data.payment_c_value,
                    Payment.fineos_pei_i_value == scenario_data.payment_i_value,
                )
                .order_by(Payment.created_at.desc())
                .first()
            )
            scenario_data.payment = payment

            # If it has an additional payment expected, query for it too
            if scenario_data.additional_payment_c_value:
                additional_payment = (
                    db_session.query(Payment)
                    .filter(
                        Payment.fineos_pei_c_value == scenario_data.additional_payment_c_value,
                        Payment.fineos_pei_i_value == scenario_data.additional_payment_i_value,
                    )
                    .order_by(Payment.created_at.desc())
                    .first()
                )
                scenario_data.additional_payment = additional_payment

            if scenario_data.tax_withholding_payment_i_values:
                tax_withholding_payments = (
                    db_session.query(Payment)
                    .filter(
                        Payment.fineos_pei_i_value.in_(
                            scenario_data.tax_withholding_payment_i_values
                        )
                    )
                    .all()
                )
                scenario_data.tax_withholding_payments = tax_withholding_payments

    def populate_scenario_dataset_claims(self, db_session) -> None:
        for scenario_data in self.scenario_dataset:
            if scenario_data.claim:
                continue

            scenario_data.claim = (
                db_session.query(Claim)
                .filter(Claim.fineos_absence_id == scenario_data.absence_case_id)
                .first()
            )


# == The E2E Test ==


def test_e2e_pub_payments(
    local_test_db_session,
    local_test_db_other_session,
    local_initialize_factories_session,
    monkeypatch,
    set_exporter_env_vars,
    caplog,
):
    test_db_session = local_test_db_session
    test_db_other_session = local_test_db_other_session

    # ========================================================================
    # Configuration / Setup
    # ========================================================================

    caplog.set_level(logging.ERROR)  # noqa: B1
    setup_common_env_variables(monkeypatch)
    s3_config = payments_config.get_s3_config()
    mock_experian_client = get_mock_address_client()

    # ========================================================================
    # Data Setup - Mirror DOR Import + Claim Application
    # ========================================================================

    # Free time to hint upcoming processing dates
    # In reality DB data will be populated any time prior to processing
    with freeze_time("2021-05-01 00:00:00", tz_offset=5):
        test_dataset = generate_test_dataset(SCENARIO_DESCRIPTORS, test_db_session)
        # Confirm generated DB rows match expectations
        assert len(test_dataset.scenario_dataset) == len(SCENARIO_DESCRIPTORS)

    # ===============================================================================
    # [Day 1 - Between 7:00 - 9:00 PM] Generate FINEOS vendor extract files
    # ===============================================================================

    with freeze_time("2021-05-01 20:00:00", tz_offset=5):
        fineos_timestamp_prefix = get_current_timestamp_prefix()

        generate_fineos_extract_files(test_dataset.scenario_dataset)

    # ===============================================================================
    # [Day 1 - After 9:00 PM] Run the FINEOS ECS task - Process Claim and Payment Extract
    # ===============================================================================

    with freeze_time("2021-05-01 21:30:00", tz_offset=5):
        # == Run the task
        process_fineos_extracts(
            test_dataset, mock_experian_client, test_db_session, test_db_other_session
        )

        assert_report_queue_items_count(local_test_db_other_session, {PaymentExtractStep: 1})

        # == Validate created rows
        claims = test_db_session.query(Claim).all()
        # Each scenario will have a claim created even if it doesn't start with one
        assert len(claims) == len(test_dataset.scenario_dataset)

        # Payments
        payments = (
            # Only retrieve payments that were generated from processing extracts
            # This ends up being 7: there are 5 steps that occur before as well as an import log for past payments
            # 1:PastPayments,2:StateCleanupStep,3:CLAIMANT_EXTRACT_CONFIG,4:PAYMENT_EXTRACT_CONFIG,
            # 5:VBI_TASKREPORT_SOM_EXTRACT_CONFIG,6:ClaimantExtractStep,7:PaymentExtractStep
            test_db_session.query(Payment)
            .filter(Payment.fineos_extract_import_log_id == 7)
            .all()
        )
        missing_payment = list(
            filter(
                lambda sd: not sd.scenario_descriptor.create_payment, test_dataset.scenario_dataset
            )
        )
        all_scenarios = list(SCENARIO_DESCRIPTORS_BY_NAME.keys())
        assert len(test_db_session.query(FineosExtractVbi1099DataSom).all()) > 1
        assert (
            len(test_db_session.query(FineosExtractVbi1099DataSom.reference_file_id).first()) == 1
        )
        assert len(test_db_session.query(Pfml1099Request).all()) <= len(
            test_db_session.query(FineosExtractVbi1099DataSom).all()
        )
        # split payments added for withholding
        split_payment_scenarios = [
            ScenarioName.HAPPY_PATH_TAX_WITHHOLDING,
            ScenarioName.HAPPY_PATH_TAX_WITHHOLDING,
            ScenarioName.HAPPY_PATH_TAX_WITHHOLDING_PAYMENT_METHOD_CHECK,
            ScenarioName.HAPPY_PATH_TAX_WITHHOLDING_PAYMENT_METHOD_CHECK,
            ScenarioName.TAX_WITHHOLDING_PRIMARY_PAYMENT_NOT_PRENOTED,
            ScenarioName.TAX_WITHHOLDING_PRIMARY_PAYMENT_NOT_PRENOTED,
            ScenarioName.TAX_WITHHOLDING_CANCELLATION_PAYMENT,
            ScenarioName.TAX_WITHHOLDING_CANCELLATION_PAYMENT,
            ScenarioName.TAX_WITHHOLDING_ADDRESS_NO_MATCHES_FROM_EXPERIAN,
            ScenarioName.TAX_WITHHOLDING_ADDRESS_NO_MATCHES_FROM_EXPERIAN,
        ]

        assert len(payments) == len(test_dataset.scenario_dataset) + len(
            split_payment_scenarios
        ) - len(missing_payment)

        # Payment staging tables
        # We don't make a payment for CLAIMANT_PRENOTED_NO_PAYMENT_RECEIVED
        # but do make the records in the other files still
        assert len(test_db_session.query(FineosExtractVpei).all()) == len(payments)
        assert len(test_db_session.query(FineosExtractVpeiClaimDetails).all()) == len(payments) + 1
        assert (
            len(test_db_session.query(FineosExtractVpeiPaymentDetails).all()) == len(payments) + 1
        )

        # == Validate employee state logs
        assert_employee_state_for_scenarios(
            test_dataset=test_dataset,
            scenario_names=[
                ScenarioName.PRENOTE_WITH_EXISTING_EFT_ACCOUNT,
                ScenarioName.EFT_ACCOUNT_NOT_PRENOTED,
                ScenarioName.PUB_ACH_PRENOTE_RETURN,
                ScenarioName.PUB_ACH_PRENOTE_NOTIFICATION,
                ScenarioName.PUB_ACH_PRENOTE_INVALID_PAYMENT_ID_FORMAT,
                ScenarioName.PUB_ACH_PRENOTE_PAYMENT_ID_NOT_FOUND,
            ],
            end_state=State.DELEGATED_EFT_SEND_PRENOTE,
            flow=Flow.DELEGATED_EFT,
            db_session=test_db_session,
        )

        # == Validate payments state logs
        stage_1_happy_path_scenarios = [
            ScenarioName.HAPPY_PATH_MEDICAL_ACH_PRENOTED,
            ScenarioName.HAPPY_PATH_FAMILY_ACH_PRENOTED,
            ScenarioName.HAPPY_PATH_FAMILY_CHECK_PRENOTED,
            ScenarioName.HAPPY_PATH_ACH_PAYMENT_ADDRESS_NO_MATCHES_FROM_EXPERIAN,
            ScenarioName.HAPPY_PATH_CHECK_FAMILY_RETURN_PAID,
            ScenarioName.HAPPY_PATH_CHECK_FAMILY_RETURN_OUTSTANDING,
            ScenarioName.HAPPY_PATH_CHECK_FAMILY_RETURN_FUTURE,
            ScenarioName.HAPPY_PATH_CLAIM_MISSING_EMPLOYEE,
            ScenarioName.HAPPY_PATH_DOR_FINEOS_NAME_MISMATCH,
            ScenarioName.HAPPY_PATH_DUA_ADDITIONAL_INCOME,
            ScenarioName.HAPPY_PATH_DIA_ADDITIONAL_INCOME,
            ScenarioName.HAPPY_PATH_MAX_LEAVE_DURATION_EXCEEDED,
            ScenarioName.HAPPY_PATH_TAX_WITHHOLDING,
            ScenarioName.HAPPY_PATH_PAYMENT_PREAPPROVED,
            ScenarioName.HAPPY_PATH_PAYMENT_IN_WAITING_WEEK,
        ]

        stage_1_non_standard_payments = [
            ScenarioName.ZERO_DOLLAR_PAYMENT,
            ScenarioName.CANCELLATION_PAYMENT,
            ScenarioName.EMPLOYER_REIMBURSEMENT_PAYMENT,
            ScenarioName.TAX_WITHHOLDING_CANCELLATION_PAYMENT,
        ]

        stage_1_overpayment_scenarios = [
            ScenarioName.OVERPAYMENT_PAYMENT_POSITIVE,
            ScenarioName.OVERPAYMENT_PAYMENT_NEGATIVE,
            ScenarioName.OVERPAYMENT_MISSING_NON_VPEI_RECORDS,
        ]

        stage_1_non_standard_splitpayment_scenarios = [
            ScenarioName.TAX_WITHHOLDING_CANCELLATION_PAYMENT,
            ScenarioName.TAX_WITHHOLDING_CANCELLATION_PAYMENT,
        ]

        stage_1_non_standard_payments.extend(stage_1_overpayment_scenarios)
        stage_1_non_standard_payments.extend(stage_1_non_standard_splitpayment_scenarios)

        assert_payment_state_for_scenarios(
            test_dataset=test_dataset,
            scenario_names=stage_1_happy_path_scenarios,
            end_state=State.DELEGATED_PAYMENT_PAYMENT_AUDIT_REPORT_SENT,
            db_session=test_db_session,
        )

        stage_1_scenarios_that_will_later_fail = [
            ScenarioName.PUB_ACH_FAMILY_RETURN,
            ScenarioName.PUB_ACH_FAMILY_NOTIFICATION,
            ScenarioName.PUB_ACH_FAMILY_RETURN_INVALID_PAYMENT_ID_FORMAT,
            ScenarioName.PUB_ACH_MEDICAL_RETURN,
            ScenarioName.PUB_ACH_MEDICAL_NOTIFICATION,
            ScenarioName.PUB_ACH_MANUAL_REJECT,
            ScenarioName.PUB_CHECK_FAMILY_RETURN_VOID,
            ScenarioName.PUB_CHECK_FAMILY_RETURN_STALE,
            ScenarioName.PUB_CHECK_FAMILY_RETURN_STOP,
            ScenarioName.AUDIT_REJECTED,
            ScenarioName.AUDIT_SKIPPED,
            ScenarioName.AUDIT_REJECTED_WITH_NOTE,
            ScenarioName.AUDIT_SKIPPED_WITH_NOTE,
            ScenarioName.PUB_ACH_FAMILY_RETURN_PAYMENT_ID_NOT_FOUND,
            ScenarioName.PUB_CHECK_FAMILY_RETURN_CHECK_NUMBER_NOT_FOUND,
            ScenarioName.HAPPY_PATH_PAYMENT_DATE_MISMATCH,
        ]

        assert_payment_state_for_scenarios(
            test_dataset=test_dataset,
            scenario_names=stage_1_scenarios_that_will_later_fail,
            end_state=State.DELEGATED_PAYMENT_PAYMENT_AUDIT_REPORT_SENT,
            db_session=test_db_session,
        )

        assert_payment_state_for_scenarios(
            test_dataset=test_dataset,
            scenario_names=[ScenarioName.ZERO_DOLLAR_PAYMENT],
            end_state=State.DELEGATED_PAYMENT_PROCESSED_ZERO_PAYMENT,
            db_session=test_db_session,
        )

        assert_payment_state_for_scenarios(
            test_dataset=test_dataset,
            scenario_names=[
                ScenarioName.CANCELLATION_PAYMENT,
                ScenarioName.TAX_WITHHOLDING_CANCELLATION_PAYMENT,
            ],
            end_state=State.DELEGATED_PAYMENT_PROCESSED_CANCELLATION,
            db_session=test_db_session,
        )

        assert_payment_state_for_scenarios(
            test_dataset=test_dataset,
            scenario_names=stage_1_overpayment_scenarios,
            end_state=State.DELEGATED_PAYMENT_PROCESSED_OVERPAYMENT,
            db_session=test_db_session,
        )

        assert_payment_state_for_scenarios(
            test_dataset=test_dataset,
            scenario_names=[ScenarioName.EMPLOYER_REIMBURSEMENT_PAYMENT],
            end_state=State.DELEGATED_PAYMENT_EMPLOYER_REIMBURSEMENT_RESTARTABLE,
            db_session=test_db_session,
        )

        # End State
        assert_payment_state_for_scenarios(
            test_dataset=test_dataset,
            scenario_names=[ScenarioName.CHECK_PAYMENT_ADDRESS_NO_MATCHES_FROM_EXPERIAN],
            end_state=State.PAYMENT_FAILED_ADDRESS_VALIDATION,
            db_session=test_db_session,
        )

        # End State
        assert_payment_state_for_scenarios(
            test_dataset=test_dataset,
            scenario_names=[
                ScenarioName.REJECTED_LEAVE_REQUEST_DECISION,
                ScenarioName.UNKNOWN_LEAVE_REQUEST_DECISION,
            ],
            end_state=State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_ERROR_REPORT,
            db_session=test_db_session,
        )

        state_1_invalid_payment_scenarios = [
            ScenarioName.CLAIM_NOT_ID_PROOFED,
            ScenarioName.PRENOTE_WITH_EXISTING_EFT_ACCOUNT,
            ScenarioName.EFT_ACCOUNT_NOT_PRENOTED,
            ScenarioName.PUB_ACH_PRENOTE_RETURN,
            ScenarioName.PUB_ACH_PRENOTE_NOTIFICATION,
            ScenarioName.PAYMENT_EXTRACT_EMPLOYEE_MISSING_IN_DB,
            ScenarioName.PUB_ACH_PRENOTE_INVALID_PAYMENT_ID_FORMAT,
            ScenarioName.PUB_ACH_PRENOTE_PAYMENT_ID_NOT_FOUND,
            ScenarioName.CLAIM_UNABLE_TO_SET_EMPLOYEE_FROM_EXTRACT,
            ScenarioName.TAX_WITHHOLDING_PRIMARY_PAYMENT_NOT_PRENOTED,
        ]

        assert_payment_state_for_scenarios(
            test_dataset=test_dataset,
            scenario_names=state_1_invalid_payment_scenarios,
            end_state=State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_ERROR_REPORT_RESTARTABLE,
            db_session=test_db_session,
        )

        # == Validate claim state
        invalid_claim_scenarios = [ScenarioName.CLAIM_UNABLE_TO_SET_EMPLOYEE_FROM_EXTRACT]
        valid_claim_scenarios = test_dataset.get_scenario_names(
            scenarios_to_filter=invalid_claim_scenarios
        )

        assert_claim_state_for_scenarios(
            test_dataset=test_dataset,
            scenario_names=valid_claim_scenarios,
            end_state=None,
            db_session=test_db_session,
        )
        assert_claim_state_for_scenarios(
            test_dataset=test_dataset,
            scenario_names=invalid_claim_scenarios,
            end_state=State.DELEGATED_CLAIM_ADD_TO_CLAIM_EXTRACT_ERROR_REPORT,
            db_session=test_db_session,
        )

        # == Validate prenote states
        assert_prenote_state(
            test_dataset=test_dataset,
            scenario_names=[
                ScenarioName.HAPPY_PATH_MEDICAL_ACH_PRENOTED,
                ScenarioName.HAPPY_PATH_FAMILY_ACH_PRENOTED,
                ScenarioName.HAPPY_PATH_ACH_PAYMENT_ADDRESS_NO_MATCHES_FROM_EXPERIAN,
                ScenarioName.HAPPY_PATH_DOR_FINEOS_NAME_MISMATCH,
                ScenarioName.HAPPY_PATH_DUA_ADDITIONAL_INCOME,
                ScenarioName.HAPPY_PATH_DIA_ADDITIONAL_INCOME,
                ScenarioName.PUB_ACH_FAMILY_RETURN,
                ScenarioName.PUB_ACH_FAMILY_NOTIFICATION,
                ScenarioName.PUB_ACH_FAMILY_RETURN_INVALID_PAYMENT_ID_FORMAT,
                ScenarioName.PUB_ACH_MEDICAL_RETURN,
                ScenarioName.PUB_ACH_MEDICAL_NOTIFICATION,
                ScenarioName.PUB_ACH_MANUAL_REJECT,
                ScenarioName.AUDIT_REJECTED,
                ScenarioName.AUDIT_SKIPPED,
                ScenarioName.AUDIT_REJECTED_WITH_NOTE,
                ScenarioName.AUDIT_SKIPPED_WITH_NOTE,
                ScenarioName.PUB_ACH_FAMILY_RETURN_INVALID_PAYMENT_ID_FORMAT,
                ScenarioName.PUB_ACH_FAMILY_RETURN_PAYMENT_ID_NOT_FOUND,
            ],
            expected_prenote_state=PrenoteState.APPROVED,
        )

        assert_prenote_state(
            test_dataset=test_dataset,
            scenario_names=[
                ScenarioName.EFT_ACCOUNT_NOT_PRENOTED,
                ScenarioName.PUB_ACH_PRENOTE_RETURN,
                ScenarioName.PUB_ACH_PRENOTE_NOTIFICATION,
                ScenarioName.PRENOTE_WITH_EXISTING_EFT_ACCOUNT,
                ScenarioName.PUB_ACH_PRENOTE_INVALID_PAYMENT_ID_FORMAT,
                ScenarioName.PUB_ACH_PRENOTE_PAYMENT_ID_NOT_FOUND,
            ],
            expected_prenote_state=PrenoteState.PENDING_PRE_PUB,
        )

        # == Validate audit report
        date_folder = get_current_date_folder()
        timestamp_prefix = get_current_timestamp_prefix()

        payment_audit_report_outbound_folder_path = os.path.join(
            s3_config.dfml_report_outbound_path
        )

        payment_audit_report_sent_folder_path = os.path.join(
            s3_config.pfml_error_reports_archive_path,
            payments_util.Constants.S3_OUTBOUND_SENT_DIR,
            date_folder,
        )

        audit_report_file_name = "Payment-Audit-Report.csv"

        assert_files(payment_audit_report_outbound_folder_path, [audit_report_file_name])
        assert_files(
            payment_audit_report_sent_folder_path, [audit_report_file_name], timestamp_prefix
        )

        audit_report_file_path = os.path.join(
            payment_audit_report_outbound_folder_path, audit_report_file_name
        )

        audit_report_parsed_csv_rows = parse_csv(audit_report_file_path)
        assert len(audit_report_parsed_csv_rows) == len(
            [
                ScenarioName.HAPPY_PATH_ACH_PAYMENT_ADDRESS_NO_MATCHES_FROM_EXPERIAN,
                ScenarioName.HAPPY_PATH_FAMILY_CHECK_PRENOTED,
                ScenarioName.HAPPY_PATH_CHECK_FAMILY_RETURN_PAID,
                ScenarioName.HAPPY_PATH_CHECK_FAMILY_RETURN_OUTSTANDING,
                ScenarioName.HAPPY_PATH_CHECK_FAMILY_RETURN_FUTURE,
                ScenarioName.HAPPY_PATH_MEDICAL_ACH_PRENOTED,
                ScenarioName.HAPPY_PATH_FAMILY_ACH_PRENOTED,
                ScenarioName.PUB_ACH_FAMILY_RETURN,
                ScenarioName.PUB_ACH_FAMILY_NOTIFICATION,
                ScenarioName.PUB_ACH_MEDICAL_RETURN,
                ScenarioName.PUB_ACH_MEDICAL_NOTIFICATION,
                ScenarioName.PUB_ACH_MANUAL_REJECT,
                ScenarioName.PUB_CHECK_FAMILY_RETURN_VOID,
                ScenarioName.PUB_CHECK_FAMILY_RETURN_STALE,
                ScenarioName.PUB_CHECK_FAMILY_RETURN_STOP,
                ScenarioName.AUDIT_REJECTED,
                ScenarioName.AUDIT_SKIPPED,
                ScenarioName.AUDIT_REJECTED_WITH_NOTE,
                ScenarioName.AUDIT_SKIPPED_WITH_NOTE,
                ScenarioName.PUB_ACH_FAMILY_RETURN_INVALID_PAYMENT_ID_FORMAT,
                ScenarioName.PUB_ACH_FAMILY_RETURN_PAYMENT_ID_NOT_FOUND,
                ScenarioName.PUB_CHECK_FAMILY_RETURN_CHECK_NUMBER_NOT_FOUND,
                ScenarioName.HAPPY_PATH_CLAIM_MISSING_EMPLOYEE,
                ScenarioName.HAPPY_PATH_DOR_FINEOS_NAME_MISMATCH,
                ScenarioName.HAPPY_PATH_DUA_ADDITIONAL_INCOME,
                ScenarioName.HAPPY_PATH_DIA_ADDITIONAL_INCOME,
                ScenarioName.HAPPY_PATH_MAX_LEAVE_DURATION_EXCEEDED,
                ScenarioName.HAPPY_PATH_PAYMENT_DATE_MISMATCH,
                ScenarioName.HAPPY_PATH_TAX_WITHHOLDING,
                ScenarioName.HAPPY_PATH_TAX_WITHHOLDING_PAYMENT_METHOD_CHECK,
                ScenarioName.TAX_WITHHOLDING_MISSING_PRIMARY_PAYMENT,
                ScenarioName.IN_REVIEW_LEAVE_REQUEST_ADHOC_PAYMENTS_DECISION,
                ScenarioName.HAPPY_PATH_PAYMENT_PREAPPROVED,
                ScenarioName.HAPPY_PATH_PAYMENT_IN_WAITING_WEEK,
            ]
        )

        audit_report_sent_payments = get_payments_in_end_state(
            test_db_session, State.DELEGATED_PAYMENT_PAYMENT_AUDIT_REPORT_SENT
        )

        audit_report_expected_rows = [
            {
                PAYMENT_AUDIT_CSV_HEADERS.pfml_payment_id: str(p.payment_id),
                PAYMENT_AUDIT_CSV_HEADERS.fineos_customer_number: str(
                    p.claim.employee.fineos_customer_number
                )
                if p.claim.employee
                else None,
                PAYMENT_AUDIT_CSV_HEADERS.rejected_by_program_integrity: ""
                if not test_dataset.is_payment_scenario(
                    p, ScenarioName.HAPPY_PATH_PAYMENT_DATE_MISMATCH
                )
                else "Y",
                PAYMENT_AUDIT_CSV_HEADERS.skipped_by_program_integrity: "Y"
                if test_dataset.is_payment_scenario(
                    p, ScenarioName.IN_REVIEW_LEAVE_REQUEST_DECISION
                )
                else "",
                PAYMENT_AUDIT_CSV_HEADERS.dor_fineos_name_mismatch_details: "DOR Name:"
                if test_dataset.is_payment_scenario(
                    p, ScenarioName.HAPPY_PATH_DOR_FINEOS_NAME_MISMATCH
                )
                else "",
                PAYMENT_AUDIT_CSV_HEADERS.dua_additional_income_details: "DUA Reductions:"
                if test_dataset.is_payment_scenario(
                    p, ScenarioName.HAPPY_PATH_DUA_ADDITIONAL_INCOME
                )
                else "",
                PAYMENT_AUDIT_CSV_HEADERS.dia_additional_income_details: "DIA Reductions:"
                if test_dataset.is_payment_scenario(
                    p, ScenarioName.HAPPY_PATH_DIA_ADDITIONAL_INCOME
                )
                else "",
                PAYMENT_AUDIT_CSV_HEADERS.exceeds_26_weeks_total_leave_details: "^Benefit Year Start: 2020-12-27, Benefit Year End: 2021-12-25\n- Employer ID: (.*?), Leave Duration: 183$"
                if test_dataset.is_payment_scenario(
                    p, ScenarioName.HAPPY_PATH_MAX_LEAVE_DURATION_EXCEEDED
                )
                else "",
                PAYMENT_AUDIT_CSV_HEADERS.payment_date_mismatch_details: "Payment for 2021-05-01 -> 2021-05-16 outside all leave dates. Had absence periods for 2021-01-01 -> 2021-04-01, 2021-01-05 -> 2021-01-12."
                if test_dataset.is_payment_scenario(
                    p, ScenarioName.HAPPY_PATH_PAYMENT_DATE_MISMATCH
                )
                else "",
                PAYMENT_AUDIT_CSV_HEADERS.is_preapproved: "Y"
                if test_dataset.is_payment_scenario(p, ScenarioName.HAPPY_PATH_PAYMENT_PREAPPROVED)
                else "",
                PAYMENT_AUDIT_CSV_HEADERS.preapproval_issues: "Orphaned Tax Withholding"
                if test_dataset.is_payment_scenario(
                    p, ScenarioName.TAX_WITHHOLDING_MISSING_PRIMARY_PAYMENT
                )
                else ""
                if test_dataset.is_payment_scenario(p, ScenarioName.HAPPY_PATH_PAYMENT_PREAPPROVED)
                else "There were less than three previous payments",
                PAYMENT_AUDIT_CSV_HEADERS.waiting_week: "1"
                if test_dataset.is_payment_scenario(
                    p, ScenarioName.HAPPY_PATH_PAYMENT_IN_WAITING_WEEK
                )
                else "",
            }
            for p in audit_report_sent_payments
        ]
        assert_csv_content(audit_report_parsed_csv_rows, audit_report_expected_rows)

        # == Writeback
        # Nearly every scenario has a writeback at this point after task 1
        stage_1_writeback_scenarios = list(all_scenarios)
        # The tax records for these next scenarios don't have writebacks yet, and
        # complicate the logic to check for them
        stage_1_writeback_scenarios.remove(ScenarioName.HAPPY_PATH_TAX_WITHHOLDING)
        stage_1_writeback_scenarios.remove(
            ScenarioName.HAPPY_PATH_TAX_WITHHOLDING_PAYMENT_METHOD_CHECK
        )
        # No payment created for this scenario
        stage_1_writeback_scenarios.remove(ScenarioName.CLAIMANT_PRENOTED_NO_PAYMENT_RECEIVED)

        # Removed writeback for employer remibursement payments
        stage_1_writeback_scenarios.remove(ScenarioName.EMPLOYER_REIMBURSEMENT_PAYMENT)

        assert_writeback_for_stage(test_dataset, stage_1_writeback_scenarios, test_db_session)

        # Now add records to the list for tax withholding scenarios so the counts
        # match as each scenario can have multiple payments for it
        stage_1_writeback_scenarios.extend(
            [
                ScenarioName.TAX_WITHHOLDING_MISSING_PRIMARY_PAYMENT,
                ScenarioName.TAX_WITHHOLDING_MISSING_PRIMARY_PAYMENT,
                ScenarioName.TAX_WITHHOLDING_PRIMARY_PAYMENT_NOT_PRENOTED,
                ScenarioName.TAX_WITHHOLDING_PRIMARY_PAYMENT_NOT_PRENOTED,
                ScenarioName.TAX_WITHHOLDING_CANCELLATION_PAYMENT,
                ScenarioName.TAX_WITHHOLDING_CANCELLATION_PAYMENT,
                ScenarioName.TAX_WITHHOLDING_ADDRESS_NO_MATCHES_FROM_EXPERIAN,
                ScenarioName.TAX_WITHHOLDING_ADDRESS_NO_MATCHES_FROM_EXPERIAN,
            ]
        )

        # Validate reference files
        assert_ref_file(
            f"{s3_config.pfml_fineos_extract_archive_path}processed/{fineos_timestamp_prefix}payment-extract",
            ReferenceFileType.FINEOS_PAYMENT_EXTRACT,
            test_db_session,
        )

        assert_ref_file(
            f"{s3_config.pfml_error_reports_archive_path}/sent/{date_folder}/{timestamp_prefix}Payment-Audit-Report.csv",
            ReferenceFileType.DELEGATED_PAYMENT_AUDIT_REPORT,
            test_db_session,
        )

        # == Validate all reports
        assert_reports(
            s3_config.dfml_report_outbound_path,
            s3_config.pfml_error_reports_archive_path,
            PROCESS_FINEOS_EXTRACT_REPORTS,
            test_db_session,
        )

    # ===============================================================================
    # [Day 2 - Before 5:00 PM] Payment Integrity Team returns Payment Rejects File
    # ===============================================================================

    with freeze_time("2021-05-02 14:00:00", tz_offset=5):
        generate_rejects_file(test_dataset)

    # ==============================================================================================
    # [Day 2 - Between 5:00 - 7:00 PM PM] Run the PUB Processing ECS task - Rejects, PUB Transaction Files, Writeback
    # ==============================================================================================

    with freeze_time("2021-05-02 18:00:00", tz_offset=5):
        # == Run the task
        process_pub_payments(test_db_session, test_db_other_session)

        assert_report_queue_items_count(local_test_db_other_session)

        # == Validate file contents
        date_folder = get_current_date_folder()
        timestamp_prefix = get_current_timestamp_prefix()

        positive_pay_ez_check_payments = get_payments_in_end_state(
            test_db_session, State.DELEGATED_PAYMENT_PUB_TRANSACTION_CHECK_SENT
        )
        ez_check_file_contents = file_util.read_file(
            f"{s3_config.pfml_pub_check_archive_path}/sent/{date_folder}/{timestamp_prefix}{payments_util.Constants.FILE_NAME_PUB_EZ_CHECK}.csv"
        )

        for payment in positive_pay_ez_check_payments:
            assert ez_check_file_contents.index(payment.claim.fineos_absence_id) != -1

        positive_pay_file_contents = file_util.read_file(
            f"{s3_config.pfml_pub_check_archive_path}/sent/{date_folder}/{timestamp_prefix}{payments_util.Constants.FILE_NAME_PUB_POSITIVE_PAY}.txt"
        )

        for payment in positive_pay_ez_check_payments:
            assert positive_pay_file_contents.index(str(payment.check.check_number)) != -1

        ach_file_contents = file_util.read_file(
            f"{s3_config.pfml_pub_ach_archive_path}/sent/{date_folder}/{timestamp_prefix}{payments_util.Constants.FILE_NAME_PUB_NACHA}"
        )

        ach_payments = get_payments_in_end_state(
            test_db_session, State.DELEGATED_PAYMENT_PUB_TRANSACTION_EFT_SENT
        )

        for payment in ach_payments:
            assert ach_file_contents.index(payment.pub_eft.account_nbr) != -1

        # == Validate payments state logs

        # End State
        stage_2_ach_scenarios = [
            ScenarioName.HAPPY_PATH_MEDICAL_ACH_PRENOTED,
            ScenarioName.HAPPY_PATH_FAMILY_ACH_PRENOTED,
            ScenarioName.HAPPY_PATH_ACH_PAYMENT_ADDRESS_NO_MATCHES_FROM_EXPERIAN,
            ScenarioName.PUB_ACH_FAMILY_RETURN,
            ScenarioName.PUB_ACH_FAMILY_NOTIFICATION,
            ScenarioName.PUB_ACH_MEDICAL_RETURN,
            ScenarioName.PUB_ACH_MEDICAL_NOTIFICATION,
            ScenarioName.PUB_ACH_MANUAL_REJECT,
            ScenarioName.PUB_ACH_FAMILY_RETURN_INVALID_PAYMENT_ID_FORMAT,
            ScenarioName.PUB_ACH_FAMILY_RETURN_PAYMENT_ID_NOT_FOUND,
            ScenarioName.HAPPY_PATH_CLAIM_MISSING_EMPLOYEE,
            ScenarioName.HAPPY_PATH_DOR_FINEOS_NAME_MISMATCH,
            ScenarioName.HAPPY_PATH_DUA_ADDITIONAL_INCOME,
            ScenarioName.HAPPY_PATH_DIA_ADDITIONAL_INCOME,
            ScenarioName.HAPPY_PATH_MAX_LEAVE_DURATION_EXCEEDED,
            ScenarioName.HAPPY_PATH_TAX_WITHHOLDING,
            ScenarioName.TAX_WITHHOLDING_MISSING_PRIMARY_PAYMENT,
            ScenarioName.IN_REVIEW_LEAVE_REQUEST_ADHOC_PAYMENTS_DECISION,
        ]

        stage_2_ach_scenarios_excluding_split_payments = [
            ScenarioName.HAPPY_PATH_MEDICAL_ACH_PRENOTED,
            ScenarioName.HAPPY_PATH_FAMILY_ACH_PRENOTED,
            ScenarioName.HAPPY_PATH_ACH_PAYMENT_ADDRESS_NO_MATCHES_FROM_EXPERIAN,
            ScenarioName.PUB_ACH_FAMILY_RETURN,
            ScenarioName.PUB_ACH_FAMILY_NOTIFICATION,
            ScenarioName.PUB_ACH_MEDICAL_RETURN,
            ScenarioName.PUB_ACH_MEDICAL_NOTIFICATION,
            ScenarioName.PUB_ACH_MANUAL_REJECT,
            ScenarioName.PUB_ACH_FAMILY_RETURN_INVALID_PAYMENT_ID_FORMAT,
            ScenarioName.PUB_ACH_FAMILY_RETURN_PAYMENT_ID_NOT_FOUND,
            ScenarioName.HAPPY_PATH_CLAIM_MISSING_EMPLOYEE,
            ScenarioName.HAPPY_PATH_DOR_FINEOS_NAME_MISMATCH,
            ScenarioName.HAPPY_PATH_DUA_ADDITIONAL_INCOME,
            ScenarioName.HAPPY_PATH_DIA_ADDITIONAL_INCOME,
            ScenarioName.HAPPY_PATH_MAX_LEAVE_DURATION_EXCEEDED,
            ScenarioName.HAPPY_PATH_TAX_WITHHOLDING,
            ScenarioName.IN_REVIEW_LEAVE_REQUEST_ADHOC_PAYMENTS_DECISION,
        ]

        assert_payment_state_for_scenarios(
            test_dataset=test_dataset,
            scenario_names=stage_2_ach_scenarios_excluding_split_payments,
            end_state=State.DELEGATED_PAYMENT_PUB_TRANSACTION_EFT_SENT,
            db_session=test_db_session,
        )

        # End State
        stage_2_check_scenarios = [
            ScenarioName.HAPPY_PATH_FAMILY_CHECK_PRENOTED,
            ScenarioName.HAPPY_PATH_CHECK_FAMILY_RETURN_PAID,
            ScenarioName.HAPPY_PATH_CHECK_FAMILY_RETURN_OUTSTANDING,
            ScenarioName.HAPPY_PATH_CHECK_FAMILY_RETURN_FUTURE,
            ScenarioName.PUB_CHECK_FAMILY_RETURN_VOID,
            ScenarioName.PUB_CHECK_FAMILY_RETURN_STALE,
            ScenarioName.PUB_CHECK_FAMILY_RETURN_STOP,
            ScenarioName.PUB_CHECK_FAMILY_RETURN_CHECK_NUMBER_NOT_FOUND,
            ScenarioName.HAPPY_PATH_TAX_WITHHOLDING_PAYMENT_METHOD_CHECK,
            ScenarioName.HAPPY_PATH_PAYMENT_PREAPPROVED,
        ]

        assert_payment_state_for_scenarios(
            test_dataset=test_dataset,
            scenario_names=stage_2_check_scenarios,
            end_state=State.DELEGATED_PAYMENT_PUB_TRANSACTION_CHECK_SENT,
            db_session=test_db_session,
        )

        # End State
        assert_payment_state_for_scenarios(
            test_dataset=test_dataset,
            scenario_names=[
                ScenarioName.AUDIT_REJECTED,
                ScenarioName.AUDIT_REJECTED_WITH_NOTE,
                ScenarioName.HAPPY_PATH_PAYMENT_DATE_MISMATCH,
            ],
            end_state=State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_REJECT_REPORT,
            db_session=test_db_session,
        )

        assert_payment_state_for_scenarios(
            test_dataset=test_dataset,
            scenario_names=[ScenarioName.IN_REVIEW_LEAVE_REQUEST_DECISION],
            end_state=State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_ERROR_REPORT_RESTARTABLE,
            db_session=test_db_session,
        )

        assert_payment_state_for_scenarios(
            test_dataset=test_dataset,
            scenario_names=[ScenarioName.AUDIT_SKIPPED, ScenarioName.AUDIT_SKIPPED_WITH_NOTE],
            end_state=State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_REJECT_REPORT_RESTARTABLE,
            db_session=test_db_session,
        )

        # == Validate prenote states
        stage_2_prenote_scenarios = [
            ScenarioName.PRENOTE_WITH_EXISTING_EFT_ACCOUNT,
            ScenarioName.EFT_ACCOUNT_NOT_PRENOTED,
            ScenarioName.PUB_ACH_PRENOTE_RETURN,
            ScenarioName.PUB_ACH_PRENOTE_NOTIFICATION,
            ScenarioName.PUB_ACH_PRENOTE_INVALID_PAYMENT_ID_FORMAT,
            ScenarioName.PUB_ACH_PRENOTE_PAYMENT_ID_NOT_FOUND,
            ScenarioName.TAX_WITHHOLDING_PRIMARY_PAYMENT_NOT_PRENOTED,
        ]

        assert_prenote_state(
            test_dataset=test_dataset,
            scenario_names=stage_2_prenote_scenarios,
            expected_prenote_state=PrenoteState.PENDING_WITH_PUB,
        )

        # == Rejects processed
        date_folder = get_current_date_folder()
        timestamp_prefix = get_current_timestamp_prefix()

        rejects_file_received_path = os.path.join(
            s3_config.pfml_payment_rejects_archive_path,
            payments_util.Constants.S3_INBOUND_PROCESSED_DIR,
            date_folder,
        )
        assert_files(
            rejects_file_received_path, ["Payment-Audit-Report-Response.csv"], timestamp_prefix
        )

        rejects_file_path = os.path.join(
            rejects_file_received_path, f"{timestamp_prefix}Payment-Audit-Report-Response.csv"
        )
        rejects_file_parsed_rows = parse_csv(rejects_file_path)

        rejected_scenario_data_payments = test_dataset.get_scenario_payments_by_scenario_name(
            ScenarioName.AUDIT_REJECTED
        ) + test_dataset.get_scenario_payments_by_scenario_name(
            ScenarioName.AUDIT_REJECTED_WITH_NOTE
        )

        skipped_scenario_data_payments = test_dataset.get_scenario_payments_by_scenario_name(
            ScenarioName.AUDIT_SKIPPED
        ) + test_dataset.get_scenario_payments_by_scenario_name(
            ScenarioName.AUDIT_SKIPPED_WITH_NOTE
        )

        assert_csv_content(
            rejects_file_parsed_rows,
            [
                {
                    PAYMENT_AUDIT_CSV_HEADERS.pfml_payment_id: str(p.payment_id),
                    PAYMENT_AUDIT_CSV_HEADERS.rejected_by_program_integrity: "Y",
                    PAYMENT_AUDIT_CSV_HEADERS.skipped_by_program_integrity: "",
                }
                for p in rejected_scenario_data_payments
            ],
        )

        assert_csv_content(
            rejects_file_parsed_rows,
            [
                {
                    PAYMENT_AUDIT_CSV_HEADERS.pfml_payment_id: str(p.payment_id),
                    PAYMENT_AUDIT_CSV_HEADERS.rejected_by_program_integrity: "",
                    PAYMENT_AUDIT_CSV_HEADERS.skipped_by_program_integrity: "Y",
                }
                for p in skipped_scenario_data_payments
            ],
        )

        # == Transaction Files
        pub_folder_path = os.path.join(s3_config.pub_moveit_outbound_path)
        pub_check_archive_folder_path = os.path.join(
            s3_config.pfml_pub_check_archive_path,
            payments_util.Constants.S3_OUTBOUND_SENT_DIR,
            date_folder,
        )
        pub_ach_archive_folder_path = os.path.join(
            s3_config.pfml_pub_ach_archive_path,
            payments_util.Constants.S3_OUTBOUND_SENT_DIR,
            date_folder,
        )
        dfml_report_outbound_path = os.path.join(s3_config.dfml_report_outbound_path)

        assert_files(
            dfml_report_outbound_path, [f"{payments_util.Constants.FILE_NAME_PUB_EZ_CHECK}.csv"]
        )
        assert_files(
            pub_check_archive_folder_path,
            [f"{payments_util.Constants.FILE_NAME_PUB_EZ_CHECK}.csv"],
            timestamp_prefix,
        )

        assert_files(pub_folder_path, [f"{payments_util.Constants.FILE_NAME_PUB_POSITIVE_PAY}.txt"])
        assert_files(
            pub_check_archive_folder_path,
            [f"{payments_util.Constants.FILE_NAME_PUB_POSITIVE_PAY}.txt"],
            timestamp_prefix,
        )

        assert_files(pub_folder_path, [payments_util.Constants.FILE_NAME_PUB_NACHA])
        assert_files(
            pub_ach_archive_folder_path,
            [payments_util.Constants.FILE_NAME_PUB_NACHA],
            timestamp_prefix,
        )

        # Validate reference files
        assert_ref_file(
            f"{s3_config.pfml_payment_rejects_archive_path}/processed/{date_folder}/{timestamp_prefix}Payment-Audit-Report-Response.csv",
            ReferenceFileType.DELEGATED_PAYMENT_REJECTS,
            test_db_session,
        )

        assert_ref_file(
            f"{s3_config.pfml_pub_check_archive_path}/sent/{date_folder}/{timestamp_prefix}{payments_util.Constants.FILE_NAME_PUB_EZ_CHECK}.csv",
            ReferenceFileType.PUB_EZ_CHECK,
            test_db_session,
        )

        assert_ref_file(
            f"{s3_config.pfml_pub_check_archive_path}/sent/{date_folder}/{timestamp_prefix}{payments_util.Constants.FILE_NAME_PUB_POSITIVE_PAY}.txt",
            ReferenceFileType.PUB_POSITIVE_PAYMENT,
            test_db_session,
        )

        assert_ref_file(
            f"{s3_config.pfml_pub_ach_archive_path}/sent/{date_folder}/{timestamp_prefix}{payments_util.Constants.FILE_NAME_PUB_NACHA}",
            ReferenceFileType.PUB_NACHA,
            test_db_session,
        )

        # == Writeback
        stage_2_writeback_scenarios = [
            ScenarioName.AUDIT_REJECTED,
            ScenarioName.AUDIT_SKIPPED,
            ScenarioName.AUDIT_REJECTED_WITH_NOTE,
            ScenarioName.AUDIT_SKIPPED_WITH_NOTE,
            ScenarioName.HAPPY_PATH_PAYMENT_DATE_MISMATCH,
        ]
        stage_2_writeback_scenarios.extend(stage_2_ach_scenarios)
        stage_2_writeback_scenarios.extend(stage_2_check_scenarios)

        assert_writeback_for_stage(test_dataset, stage_2_writeback_scenarios, test_db_session)

        # == Reports
        assert_reports(
            s3_config.dfml_report_outbound_path,
            s3_config.pfml_error_reports_archive_path,
            CREATE_PUB_FILES_REPORTS,
            test_db_session,
        )

    # ===============================================================================
    # [Day 3 - 9:00 AM] PUB sends ACH and Check response files
    # ===============================================================================

    with freeze_time("2021-05-03 09:00:00", tz_offset=5):
        generate_pub_returns(test_dataset)

    # ==============================================================================================
    # [Day 3 - 11:00 AM] Run the PUB Response ECS task - response, writeback, reports
    # ==============================================================================================

    with freeze_time("2021-05-03 11:00:00", tz_offset=5):

        # == Run the task
        process_pub_responses(test_db_session, test_db_other_session)

        assert_report_queue_items_count(local_test_db_other_session)

        # == Validate payment states

        # End State
        assert_payment_state_for_scenarios(
            test_dataset=test_dataset,
            scenario_names=[
                ScenarioName.PUB_ACH_MEDICAL_NOTIFICATION,
                ScenarioName.PUB_ACH_FAMILY_NOTIFICATION,
            ],
            end_state=State.DELEGATED_PAYMENT_COMPLETE_WITH_CHANGE_NOTIFICATION,
            db_session=test_db_session,
        )

        # End State
        assert_payment_state_for_scenarios(
            test_dataset=test_dataset,
            scenario_names=[
                ScenarioName.PUB_ACH_FAMILY_RETURN,
                ScenarioName.PUB_ACH_MEDICAL_RETURN,
                ScenarioName.PUB_ACH_MANUAL_REJECT,
            ],
            end_state=State.DELEGATED_PAYMENT_ERROR_FROM_BANK,
            db_session=test_db_session,
        )

        # Unchanged
        assert_payment_state_for_scenarios(
            test_dataset=test_dataset,
            scenario_names=[
                ScenarioName.PUB_ACH_FAMILY_RETURN_INVALID_PAYMENT_ID_FORMAT,
                ScenarioName.PUB_ACH_FAMILY_RETURN_PAYMENT_ID_NOT_FOUND,
            ],
            end_state=State.DELEGATED_PAYMENT_PUB_TRANSACTION_EFT_SENT,
            db_session=test_db_session,
        )

        # Unchanged
        assert_payment_state_for_scenarios(
            test_dataset=test_dataset,
            scenario_names=[
                ScenarioName.HAPPY_PATH_CHECK_FAMILY_RETURN_OUTSTANDING,
                ScenarioName.HAPPY_PATH_CHECK_FAMILY_RETURN_FUTURE,
                ScenarioName.PUB_CHECK_FAMILY_RETURN_CHECK_NUMBER_NOT_FOUND,
            ],
            end_state=State.DELEGATED_PAYMENT_PUB_TRANSACTION_CHECK_SENT,
            db_session=test_db_session,
        )

        # End State
        assert_payment_state_for_scenarios(
            test_dataset=test_dataset,
            scenario_names=[
                ScenarioName.HAPPY_PATH_FAMILY_CHECK_PRENOTED,
                ScenarioName.HAPPY_PATH_CHECK_FAMILY_RETURN_PAID,
            ],
            end_state=State.DELEGATED_PAYMENT_COMPLETE,
            db_session=test_db_session,
        )

        assert_payment_state_for_scenarios(
            test_dataset=test_dataset,
            scenario_names=[
                ScenarioName.PUB_CHECK_FAMILY_RETURN_VOID,
                ScenarioName.PUB_CHECK_FAMILY_RETURN_STALE,
                ScenarioName.PUB_CHECK_FAMILY_RETURN_STOP,
            ],
            end_state=State.DELEGATED_PAYMENT_ERROR_FROM_BANK,
            db_session=test_db_session,
        )

        # == Validate prenote states
        assert_prenote_state(
            test_dataset=test_dataset,
            scenario_names=[
                ScenarioName.PRENOTE_WITH_EXISTING_EFT_ACCOUNT,
                ScenarioName.EFT_ACCOUNT_NOT_PRENOTED,
                ScenarioName.PUB_ACH_PRENOTE_INVALID_PAYMENT_ID_FORMAT,
                ScenarioName.PUB_ACH_PRENOTE_PAYMENT_ID_NOT_FOUND,
            ],
            expected_prenote_state=PrenoteState.PENDING_WITH_PUB,
        )

        assert_prenote_state(
            test_dataset=test_dataset,
            scenario_names=[ScenarioName.PUB_ACH_PRENOTE_NOTIFICATION],
            expected_prenote_state=PrenoteState.APPROVED,
        )

        assert_prenote_state(
            test_dataset=test_dataset,
            scenario_names=[ScenarioName.PUB_ACH_PRENOTE_RETURN],
            expected_prenote_state=PrenoteState.REJECTED,
        )

        # == Assert files

        # processed ach return files
        date_folder = get_current_date_folder()
        timestamp_prefix = get_current_timestamp_prefix()

        pub_ach_response_processed_folder = os.path.join(
            s3_config.pfml_pub_ach_archive_path,
            payments_util.Constants.S3_INBOUND_PROCESSED_DIR,
            date_folder,
        )
        nacha_filenames = [payments_util.Constants.FILE_NAME_PUB_NACHA]
        assert_files(pub_ach_response_processed_folder, nacha_filenames, timestamp_prefix)

        # check content of the ach response file
        nacha_response_file_contents = file_util.read_file(
            os.path.join(
                pub_ach_response_processed_folder,
                f"{timestamp_prefix}{payments_util.Constants.FILE_NAME_PUB_NACHA}",
            )
        )

        for scenario_data in test_dataset.scenario_dataset:
            scenario_descriptor = scenario_data.scenario_descriptor
            scenario_name = scenario_descriptor.scenario_name

            if scenario_descriptor.payment_method != PaymentMethod.ACH or not (
                scenario_descriptor.pub_ach_response_return
                or scenario_descriptor.pub_ach_response_change_notification
            ):
                continue

            payment = scenario_data.additional_payment or scenario_data.payment

            assert payment is not None, f"No Payment found: {scenario_name}"

            pub_eft = payment.pub_eft

            assert pub_eft is not None, f"No PubEft found: {scenario_name}"

            routing_number = pub_eft.routing_nbr
            account_number = pub_eft.account_nbr
            nacha_id_prefix = "P" if scenario_descriptor.prenoted else "E"
            pub_individual_id = (
                payment.pub_individual_id
                if scenario_descriptor.prenoted
                else pub_eft.pub_individual_id
            )
            nacha_id = f"{nacha_id_prefix}{pub_individual_id}"

            assert (
                nacha_id in nacha_response_file_contents
            ), f"Could not find nacha_id: {nacha_id} - {scenario_name}"
            assert (
                routing_number in nacha_response_file_contents
            ), f"Could not find routing_number: {routing_number} - {scenario_name}"
            assert (
                account_number in nacha_response_file_contents
            ), f"Could not find account_number: {account_number} - {scenario_name}"

        # processed check return files
        pub_check_response_processed_folder = os.path.join(
            s3_config.pfml_pub_check_archive_path,
            payments_util.Constants.S3_INBOUND_PROCESSED_DIR,
            date_folder,
        )
        positive_pay_check_response_file = (
            f"Paid-{payments_util.Constants.FILE_NAME_PUB_POSITIVE_PAY}.csv"
        )
        outstanding_check_response_file = (
            f"Outstanding-{payments_util.Constants.FILE_NAME_PUB_POSITIVE_PAY}.csv"
        )
        positive_pay_filenames = [positive_pay_check_response_file, outstanding_check_response_file]
        assert_files(pub_check_response_processed_folder, positive_pay_filenames, timestamp_prefix)

        # check content of the check response files
        positive_pay_check_response_file_contents = file_util.read_file(
            os.path.join(
                pub_check_response_processed_folder,
                f"{timestamp_prefix}{positive_pay_check_response_file}",
            )
        )
        outstanding_check_response_file_contents = file_util.read_file(
            os.path.join(
                pub_check_response_processed_folder,
                f"{timestamp_prefix}{outstanding_check_response_file}",
            )
        )

        for scenario_data in test_dataset.scenario_dataset:
            scenario_descriptor = scenario_data.scenario_descriptor
            scenario_name = scenario_descriptor.scenario_name

            if (
                scenario_descriptor.payment_method != PaymentMethod.CHECK
                or not scenario_descriptor.pub_check_response
            ):
                continue

            employee = scenario_data.employee

            if scenario_descriptor.pub_check_paid_response:
                assert (
                    str(employee.employee_id) in positive_pay_check_response_file_contents
                ), f"Employee id not found in positive pay file for {scenario_name}"
            else:
                assert (
                    str(employee.employee_id) in outstanding_check_response_file_contents
                ), f"Employee id not found in oustanding file for {scenario_name}"

        # == PubError adjust as metric based scenarios below are added
        assert len(test_db_session.query(PubError).all()) == len(
            [
                ScenarioName.PUB_ACH_FAMILY_NOTIFICATION,
                ScenarioName.PUB_ACH_FAMILY_RETURN,
                ScenarioName.PUB_ACH_MEDICAL_NOTIFICATION,
                ScenarioName.PUB_ACH_MANUAL_REJECT,
                ScenarioName.PUB_ACH_MEDICAL_RETURN,
                ScenarioName.PUB_ACH_PRENOTE_INVALID_PAYMENT_ID_FORMAT,
                ScenarioName.PUB_ACH_PRENOTE_PAYMENT_ID_NOT_FOUND,
                ScenarioName.PUB_ACH_PRENOTE_RETURN,
                ScenarioName.PUB_ACH_PRENOTE_NOTIFICATION,
                ScenarioName.PUB_CHECK_FAMILY_RETURN_STALE,
                ScenarioName.PUB_CHECK_FAMILY_RETURN_STOP,
                ScenarioName.PUB_CHECK_FAMILY_RETURN_VOID,
                ScenarioName.PUB_ACH_FAMILY_RETURN_INVALID_PAYMENT_ID_FORMAT,
                ScenarioName.PUB_ACH_FAMILY_RETURN_PAYMENT_ID_NOT_FOUND,
                ScenarioName.PUB_CHECK_FAMILY_RETURN_CHECK_NUMBER_NOT_FOUND,
            ]
        )

        # == Writeback
        stage_3_errored_writeback_scenarios_ach = [
            ScenarioName.PUB_ACH_FAMILY_RETURN,
            ScenarioName.PUB_ACH_MEDICAL_RETURN,
        ]
        stage_3_errored_writeback_scenarios_check_void = [ScenarioName.PUB_CHECK_FAMILY_RETURN_VOID]
        stage_3_errored_writeback_scenarios_check_stale = [
            ScenarioName.PUB_CHECK_FAMILY_RETURN_STALE
        ]
        stage_3_errored_writeback_scenarios_check_stop = [ScenarioName.PUB_CHECK_FAMILY_RETURN_STOP]
        stage_3_successful_writeback_scenarios = [
            ScenarioName.HAPPY_PATH_FAMILY_CHECK_PRENOTED,
            ScenarioName.HAPPY_PATH_CHECK_FAMILY_RETURN_PAID,
            ScenarioName.PUB_ACH_MEDICAL_NOTIFICATION,
            ScenarioName.PUB_ACH_FAMILY_NOTIFICATION,
            ScenarioName.HAPPY_PATH_TAX_WITHHOLDING_PAYMENT_METHOD_CHECK,
            ScenarioName.HAPPY_PATH_PAYMENT_PREAPPROVED,
        ]
        stage_3_manual_pub_reject_scenarios = [ScenarioName.PUB_ACH_MANUAL_REJECT]

        stage_3_all_writeback_scenarios = (
            stage_3_errored_writeback_scenarios_ach
            + stage_3_errored_writeback_scenarios_check_void
            + stage_3_errored_writeback_scenarios_check_stale
            + stage_3_errored_writeback_scenarios_check_stop
            + stage_3_successful_writeback_scenarios
            + stage_3_manual_pub_reject_scenarios
        )

        assert_writeback_for_stage(
            test_dataset,
            stage_3_all_writeback_scenarios,
            test_db_session,
            do_related_payments=False,
        )

        # == Reports
        assert_reports(
            s3_config.dfml_report_outbound_path,
            s3_config.pfml_error_reports_archive_path,
            PROCESS_PUB_RESPONSES_REPORTS,
            test_db_session,
        )

    # ===============================================================================
    # [Day 7 - 7:00 PM] Generate FINEOS extract files
    # ===============================================================================
    with freeze_time("2021-05-07 18:00:00", tz_offset=5):
        generate_fineos_extract_files(test_dataset.scenario_dataset)

    # ===============================================================================
    # [Day 7 - 9:00 PM] Run the FINEOS ECS task - Process Claim and Payment Extract
    # ===============================================================================

    with freeze_time("2021-05-07 21:30:00", tz_offset=5):

        process_fineos_extracts(
            test_dataset, mock_experian_client, test_db_session, test_db_other_session
        )

        assert_report_queue_items_count(
            test_db_other_session,
            {
                PaymentExtractStep: 1,
            },
        )

        assert_payment_state_for_scenarios(
            test_dataset=test_dataset,
            scenario_names=[
                ScenarioName.PRENOTE_WITH_EXISTING_EFT_ACCOUNT,
                ScenarioName.EFT_ACCOUNT_NOT_PRENOTED,
                ScenarioName.PUB_ACH_PRENOTE_INVALID_PAYMENT_ID_FORMAT,
                ScenarioName.PUB_ACH_PRENOTE_PAYMENT_ID_NOT_FOUND,
                ScenarioName.PUB_ACH_PRENOTE_NOTIFICATION,
            ],
            end_state=State.DELEGATED_PAYMENT_PAYMENT_AUDIT_REPORT_SENT,
            db_session=test_db_session,
        )

        assert_payment_state_for_scenarios(
            test_dataset=test_dataset,
            scenario_names=[ScenarioName.PUB_ACH_PRENOTE_RETURN],
            end_state=State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_ERROR_REPORT,
            db_session=test_db_session,
        )

        # validate other scenarios that have reached an end state are erroring out
        assert_payment_state_for_scenarios(
            test_dataset=test_dataset,
            scenario_names=stage_1_happy_path_scenarios,
            end_state=State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_ERROR_REPORT,
            db_session=test_db_session,
        )

        # assert prenote states
        assert_prenote_state(
            test_dataset=test_dataset,
            scenario_names=[
                ScenarioName.PRENOTE_WITH_EXISTING_EFT_ACCOUNT,
                ScenarioName.EFT_ACCOUNT_NOT_PRENOTED,
                ScenarioName.PUB_ACH_PRENOTE_INVALID_PAYMENT_ID_FORMAT,
                ScenarioName.PUB_ACH_PRENOTE_PAYMENT_ID_NOT_FOUND,
                ScenarioName.PUB_ACH_PRENOTE_NOTIFICATION,
            ],
            expected_prenote_state=PrenoteState.APPROVED,
        )

        assert_prenote_state(
            test_dataset=test_dataset,
            scenario_names=[ScenarioName.PUB_ACH_PRENOTE_RETURN],
            expected_prenote_state=PrenoteState.REJECTED,
        )

        # Writeback
        stage_4_writeback_scenarios = [ScenarioName.PUB_ACH_PRENOTE_RETURN]

        assert_writeback_for_stage(test_dataset, stage_4_writeback_scenarios, test_db_session)

        # Metrics
        assert_metrics(
            test_db_other_session,
            "FineosPeiWritebackStep",
            {
                "eft_account_information_error_writeback_transaction_status_count": len(
                    [ScenarioName.PUB_ACH_PRENOTE_RETURN]
                )
            },
        )


def test_e2e_pub_payments_delayed_scenarios(
    local_test_db_session,
    local_test_db_other_session,
    local_initialize_factories_session,
    monkeypatch,
    set_exporter_env_vars,
    caplog,
):
    # ========================================================================
    # Configuration / Setup
    # ========================================================================

    caplog.set_level(logging.ERROR)  # noqa: B1
    setup_common_env_variables(monkeypatch)
    mock_experian_client = get_mock_address_client()

    # ========================================================================
    # Data Setup - Mirror DOR Import + Claim Application
    # ========================================================================

    test_dataset = generate_test_dataset(DELAYED_SCENARIO_DESCRIPTORS, local_test_db_session)
    # Confirm generated DB rows match expectations
    assert len(test_dataset.scenario_dataset) == len(DELAYED_SCENARIO_DESCRIPTORS)

    # ===============================================================================
    # [Day 1 - Between 7:00 - 9:00 PM] Generate FINEOS extract files
    # ===============================================================================

    with freeze_time("2021-05-01 20:00:00", tz_offset=5):
        generate_fineos_extract_files(test_dataset.scenario_dataset)

    # ===============================================================================
    # [Day 1 - After 9:00 PM] Run the FINEOS ECS task - Process Claim and Payment Extract
    # ===============================================================================

    with freeze_time("2021-05-01 21:30:00", tz_offset=5):
        process_fineos_extracts(
            test_dataset, mock_experian_client, local_test_db_session, local_test_db_other_session
        )
        assert_report_queue_items_count(
            local_test_db_other_session,
            {
                PaymentExtractStep: 1,
            },
        )

        assert_payment_state_for_scenarios(
            test_dataset=test_dataset,
            scenario_names=[
                ScenarioName.AUDIT_REJECTED_THEN_ACCEPTED,
                ScenarioName.AUDIT_SKIPPED_THEN_ACCEPTED,
                ScenarioName.SECOND_PAYMENT_FOR_PERIOD_OVER_CAP,
                ScenarioName.HAPPY_PATH_TWO_PAYMENTS_UNDER_WEEKLY_CAP,
                ScenarioName.HAPPY_PATH_TWO_ADHOC_PAYMENTS_OVER_CAP,
                ScenarioName.TAX_WITHHOLDING_AUDIT_SKIPPED_THEN_ACCEPTED,
            ],
            end_state=State.DELEGATED_PAYMENT_PAYMENT_AUDIT_REPORT_SENT,
            db_session=local_test_db_session,
        )

        assert_payment_state_for_scenarios(
            test_dataset=test_dataset,
            scenario_names=[ScenarioName.CHECK_PAYMENT_ADDRESS_NO_MATCHES_FROM_EXPERIAN_FIXED],
            end_state=State.PAYMENT_FAILED_ADDRESS_VALIDATION,
            db_session=local_test_db_session,
        )

        assert_payment_state_for_scenarios(
            test_dataset=test_dataset,
            scenario_names=[ScenarioName.INVALID_ADDRESS_FIXED],
            end_state=State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_ERROR_REPORT,
            db_session=local_test_db_session,
        )

        stage_1_writeback_scenarios = [
            ScenarioName.CHECK_PAYMENT_ADDRESS_NO_MATCHES_FROM_EXPERIAN_FIXED,
            ScenarioName.INVALID_ADDRESS_FIXED,
        ]

        assert_writeback_for_stage(test_dataset, stage_1_writeback_scenarios, local_test_db_session)

    # ===============================================================================
    # [Day 2 - Before 5:00 PM] Payment Integrity Team returns Payment Rejects File
    # ===============================================================================

    with freeze_time("2021-05-02 14:00:00", tz_offset=5):
        generate_rejects_file(test_dataset, round=1)

    # ============================================================================================================
    # [Day 2 - Between 5:00 - 7:00 PM] Run the PUB Processing ECS task - Rejects, PUB Transaction Files, Writeback
    # ============================================================================================================

    with freeze_time("2021-05-02 18:00:00", tz_offset=5):
        process_pub_payments(local_test_db_session, local_test_db_other_session)

        assert_report_queue_items_count(local_test_db_other_session)

        assert_payment_state_for_scenarios(
            test_dataset=test_dataset,
            scenario_names=[
                ScenarioName.HAPPY_PATH_TWO_PAYMENTS_UNDER_WEEKLY_CAP,
                ScenarioName.HAPPY_PATH_TWO_ADHOC_PAYMENTS_OVER_CAP,
            ],
            end_state=State.DELEGATED_PAYMENT_PUB_TRANSACTION_EFT_SENT,
            db_session=local_test_db_session,
        )

        assert_payment_state_for_scenarios(
            test_dataset=test_dataset,
            scenario_names=[ScenarioName.AUDIT_REJECTED_THEN_ACCEPTED],
            end_state=State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_REJECT_REPORT,
            db_session=local_test_db_session,
        )

        assert_payment_state_for_scenarios(
            test_dataset=test_dataset,
            scenario_names=[
                ScenarioName.AUDIT_SKIPPED_THEN_ACCEPTED,
                ScenarioName.TAX_WITHHOLDING_AUDIT_SKIPPED_THEN_ACCEPTED,
            ],
            end_state=State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_REJECT_REPORT_RESTARTABLE,
            db_session=local_test_db_session,
        )

        # == Validate FINEOS status writeback states
        stage_2_writeback_scenarios = [
            ScenarioName.HAPPY_PATH_TWO_PAYMENTS_UNDER_WEEKLY_CAP,
            ScenarioName.HAPPY_PATH_TWO_ADHOC_PAYMENTS_OVER_CAP,
            ScenarioName.AUDIT_REJECTED_THEN_ACCEPTED,
            ScenarioName.TAX_WITHHOLDING_AUDIT_SKIPPED_THEN_ACCEPTED,
            ScenarioName.AUDIT_SKIPPED_THEN_ACCEPTED,
        ]

        assert_writeback_for_stage(
            test_dataset,
            stage_2_writeback_scenarios,
            local_test_db_session,
            do_related_payments=False,
        )

    # ===============================================================================
    # [Day 2 - 7:00 PM] Generate FINEOS extract files
    # ===============================================================================
    with freeze_time("2021-05-02 19:00:00", tz_offset=5):
        generate_fineos_extract_files(test_dataset.scenario_dataset, round=2)

    # ===============================================================================
    # [Day 2 - 9:00 PM] Run the FINEOS ECS task - Process Claim and Payment Extract
    # ===============================================================================

    with freeze_time("2021-05-02 21:00:00", tz_offset=5):
        process_fineos_extracts(
            test_dataset, mock_experian_client, local_test_db_session, local_test_db_other_session
        )
        assert_report_queue_items_count(local_test_db_other_session, {PaymentExtractStep: 1})

        assert_payment_state_for_scenarios(
            test_dataset=test_dataset,
            scenario_names=[
                ScenarioName.AUDIT_REJECTED_THEN_ACCEPTED,
                ScenarioName.AUDIT_SKIPPED_THEN_ACCEPTED,
                ScenarioName.CHECK_PAYMENT_ADDRESS_NO_MATCHES_FROM_EXPERIAN_FIXED,
                ScenarioName.INVALID_ADDRESS_FIXED,
                ScenarioName.HAPPY_PATH_TWO_PAYMENTS_UNDER_WEEKLY_CAP,
                ScenarioName.HAPPY_PATH_TWO_ADHOC_PAYMENTS_OVER_CAP,
                ScenarioName.TAX_WITHHOLDING_AUDIT_SKIPPED_THEN_ACCEPTED,
            ],
            end_state=State.DELEGATED_PAYMENT_PAYMENT_AUDIT_REPORT_SENT,
            db_session=local_test_db_session,
            check_additional_payment=True,
        )

        assert_payment_state_for_scenarios(
            test_dataset=test_dataset,
            scenario_names=[ScenarioName.SECOND_PAYMENT_FOR_PERIOD_OVER_CAP],
            end_state=State.PAYMENT_FAILED_MAX_WEEKLY_BENEFIT_AMOUNT_VALIDATION,
            db_session=local_test_db_session,
            check_additional_payment=True,
        )

        stage_3_writeback_scenarios = [ScenarioName.SECOND_PAYMENT_FOR_PERIOD_OVER_CAP]

        assert_writeback_for_stage(test_dataset, stage_3_writeback_scenarios, local_test_db_session)

    # ===============================================================================
    # [Day 3 - 9:00 AM] PUB sends ACH and Check response files
    # ===============================================================================

    # with freeze_time("2021-05-03 09:00:00", tz_offset=5):
    #     generate_pub_returns(test_dataset)

    # ==============================================================================================
    # [Day 3 - 11:00 AM] Run the PUB Response ECS task - response, writeback, reports
    # ==============================================================================================

    # with freeze_time("2021-05-03 11:00:00", tz_offset=5):

    #     # == Run the task
    #     process_pub_responses(test_db_session, test_db_other_session)

    # ===============================================================================
    # [Day 3 - Before 5:00 PM] Payment Integrity Team returns Payment Rejects File
    # ===============================================================================

    with freeze_time("2021-05-03 14:00:00", tz_offset=5):
        generate_rejects_file(test_dataset, round=2)

    # ============================================================================================================
    # [Day 3 - Between 5:00 - 7:00 PM] Run the PUB Processing ECS task - Rejects, PUB Transaction Files, Writeback
    # ============================================================================================================

    with freeze_time("2021-05-03 18:00:00", tz_offset=5):
        process_pub_payments(local_test_db_session, local_test_db_other_session)

        assert_report_queue_items_count(local_test_db_other_session)

        assert_payment_state_for_scenarios(
            test_dataset=test_dataset,
            scenario_names=[
                ScenarioName.AUDIT_REJECTED_THEN_ACCEPTED,
                ScenarioName.AUDIT_SKIPPED_THEN_ACCEPTED,
                ScenarioName.HAPPY_PATH_TWO_PAYMENTS_UNDER_WEEKLY_CAP,
                ScenarioName.HAPPY_PATH_TWO_ADHOC_PAYMENTS_OVER_CAP,
                ScenarioName.TAX_WITHHOLDING_AUDIT_SKIPPED_THEN_ACCEPTED,
            ],
            end_state=State.DELEGATED_PAYMENT_PUB_TRANSACTION_EFT_SENT,
            db_session=local_test_db_session,
            check_additional_payment=True,
        )

        stage_4_writeback_scenarios = [
            ScenarioName.AUDIT_REJECTED_THEN_ACCEPTED,
            ScenarioName.AUDIT_SKIPPED_THEN_ACCEPTED,
            ScenarioName.HAPPY_PATH_TWO_PAYMENTS_UNDER_WEEKLY_CAP,
            ScenarioName.HAPPY_PATH_TWO_ADHOC_PAYMENTS_OVER_CAP,
            ScenarioName.TAX_WITHHOLDING_AUDIT_SKIPPED_THEN_ACCEPTED,
        ]

        assert_writeback_for_stage(
            test_dataset,
            stage_4_writeback_scenarios,
            local_test_db_session,
            do_related_payments=False,
        )

    # ===============================================================================
    # [Day 3 - 7:00 PM] Generate FINEOS extract files
    # ===============================================================================
    with freeze_time("2021-05-03 18:00:00", tz_offset=5):
        generate_fineos_extract_files(test_dataset.scenario_dataset)

    # ===============================================================================
    # [Day 3 - 9:00 PM] Run the FINEOS ECS task - Process Claim and Payment Extract
    # ===============================================================================

    with freeze_time("2021-05-03 21:30:00", tz_offset=5):
        process_fineos_extracts(
            test_dataset, mock_experian_client, local_test_db_session, local_test_db_other_session
        )

        assert_report_queue_items_count(local_test_db_other_session, {PaymentExtractStep: 1})

        assert_payment_state_for_scenarios(
            test_dataset=test_dataset,
            scenario_names=[ScenarioName.AUDIT_REJECTED_THEN_ACCEPTED],
            end_state=State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_ERROR_REPORT,
            db_session=local_test_db_session,
        )

    # TODO Scenario: Day 6 Prenote Rejection
    # TODO Scenario: Fix for invalid ach return
    # TODO Scenario: Fix for invalid check return


def test_e2e_pub_payments_fails(
    local_test_db_session,
    local_test_db_other_session,
    local_initialize_factories_session,
    monkeypatch,
    set_exporter_env_vars,
    mock_s3_bucket,
):
    test_db_session = local_test_db_session
    test_db_other_session = local_test_db_other_session
    setup_common_env_variables(monkeypatch)

    # Make it error when the first step in the task runs
    with mock.patch(
        "massgov.pfml.delegated_payments.step.Step.set_metrics", side_effect=Exception("Error msg")
    ):

        # Run and error all 3 ECS tasks
        with pytest.raises(Exception, match="Error msg"):
            run_fineos_ecs_task(
                db_session=test_db_session,
                log_entry_db_session=test_db_other_session,
                config=FineosTaskConfiguration(["--steps", "ALL"]),
            )

        with pytest.raises(Exception, match="Error msg"):
            run_process_pub_payments_ecs_task(
                db_session=test_db_session,
                log_entry_db_session=test_db_other_session,
                config=ProcessPubPaymentsTaskConfiguration(["--steps", "ALL"]),
            )

        with pytest.raises(Exception, match="Error msg"):
            run_process_pub_responses_ecs_task(
                db_session=test_db_session,
                log_entry_db_session=test_db_other_session,
                config=ProcessPubResponsesTaskConfiguration(["--steps", "ALL"]),
            )

        # Despite the failure, the metrics are still written to S3
        # although the only "metric" is the error message as it failed
        # to initialize the metrics with how it errors above
        # The PickupResponseFilesStep appears twice as it's the first
        # step in the 2nd & 3rd ECS task
        expected_metrics = {"message": "Exception: Error msg"}
        assert_metrics(test_db_other_session, "StateCleanupStep", expected_metrics)
        assert_metrics(test_db_other_session, "PickupResponseFilesStep", expected_metrics)
        assert_metrics(
            test_db_other_session, "PickupResponseFilesStep", expected_metrics, log_report_index=1
        )

        # Nothing should have been written to s3
        all_files = file_util.list_files(f"s3://{mock_s3_bucket}", recursive=True)
        assert len(all_files) == 0


def test_e2e_pub_payments_report_queue(
    local_test_db_session,
    local_test_db_other_session,
    local_initialize_factories_session,
    monkeypatch,
    set_exporter_env_vars,
    caplog,
):

    test_db_session = local_test_db_session
    test_db_other_session = local_test_db_other_session

    # ========================================================================
    # Configuration / Setup
    # ========================================================================

    caplog.set_level(logging.ERROR)  # noqa: B1
    setup_common_env_variables(monkeypatch)
    mock_experian_client = get_mock_address_client()

    # ========================================================================
    # Data Setup - Mirror DOR Import + Claim Application
    # ========================================================================

    # Free time to hint upcoming processing dates
    # In reality DB data will be populated any time prior to processing
    with freeze_time("2021-05-01 00:00:00", tz_offset=5):
        test_dataset = generate_test_dataset(SCENARIO_DESCRIPTORS, test_db_session)

    # ===============================================================================
    # [Day 1]
    #  - [Between 7:00 - 9:00 PM] Generate FINEOS vendor extract files
    #  - [After 9:00 PM] Run the FINEOS ECS task without Reports - Process Claim and Payment Extract
    # ===============================================================================

    with freeze_time("2021-05-01 20:00:00", tz_offset=5):
        generate_fineos_extract_files(test_dataset.scenario_dataset)

    with freeze_time("2021-05-01 21:30:00", tz_offset=5):
        # == Run task with args excluding report
        task_config = FineosTaskConfiguration(["--steps", "ALL"])
        task_config.make_reports = False
        process_fineos_extracts(
            test_dataset,
            mock_experian_client,
            test_db_session,
            test_db_other_session,
            task_config,
            expected_steps_override=EXPECTED_STEPS_PROCESS_FINEOS_EXTRACTS[:-1],
        )

    # Claimant extract step has not cleared since report not ran
    assert_report_queue_items_count(
        test_db_other_session,
        {
            PaymentExtractStep: 1,
            ClaimantExtractStep: 1,
        },
    )

    # ===============================================================================
    # [Day 2]
    #  - [Before 5:00 PM] Payment Integrity Team returns Payment Rejects File
    #  - [Between 7:00 - 9:00 PM] Generate FINEOS vendor extract files
    #  - [After 9:00 PM] Run the FINEOS ECS task - Process Claim and Payment Extract
    # ===============================================================================

    with freeze_time("2021-05-02 14:00:00", tz_offset=5):
        generate_rejects_file(test_dataset)

    with freeze_time("2021-05-02 18:00:00", tz_offset=5):
        generate_fineos_extract_files(test_dataset.scenario_dataset)

    with freeze_time("2021-05-02 21:30:00", tz_offset=5):
        process_fineos_extracts(
            test_dataset, mock_experian_client, test_db_session, test_db_other_session
        )

    # Claimant extract step(s) cleared and additional Payment extract step has been added
    assert_report_queue_items_count(
        test_db_other_session,
        {
            PaymentExtractStep: 2,
        },
    )

    # ===============================================================================
    # [Day 3]
    #  - [Before 5:00 PM] Payment Integrity Team returns Payment Rejects File
    #  - [Between 5:00 - 7:00 PM PM] Run the PUB Processing ECS task without Reports - Rejects, PUB Transaction Files, Writeback
    # ===============================================================================
    with freeze_time("2021-05-03 14:00:00", tz_offset=5):
        generate_rejects_file(test_dataset)

    with freeze_time("2021-05-03 18:00:00", tz_offset=5):
        # == Run task with args excluding report
        task_config = ProcessPubPaymentsTaskConfiguration(["--steps", "ALL"])
        task_config.make_reports = False

        process_pub_payments(
            test_db_session,
            test_db_other_session,
            task_config,
            expected_steps_override=EXPECTED_STEPS_PROCESS_PUB_PAYMENTS[:-1],
        )

    # Payment extract step carried over since report not ran
    assert_report_queue_items_count(
        test_db_other_session,
        {
            PaymentExtractStep: 2,
        },
    )

    # ===============================================================================
    # [Day 4]
    #  - [9:00 AM] PUB sends ACH and Check response files
    #  - [11:00 AM] Run the PUB Response ECS task without Reports - response, writeback
    # ===============================================================================

    with freeze_time("2021-05-04 09:00:00", tz_offset=5):
        generate_pub_returns(test_dataset)

    with freeze_time("2021-05-04 11:00:00", tz_offset=5):
        # == Run task with args excluding report
        task_config = ProcessPubResponsesTaskConfiguration(["--steps", "ALL"])
        task_config.make_reports = False
        process_pub_responses(
            test_db_session,
            test_db_other_session,
            task_config,
            expected_steps_override=EXPECTED_STEPS_PROCESS_PUB_RESPONSES[:-1],
        )

    # Process files in path steps carried over since report not ran
    assert_report_queue_items_count(
        test_db_other_session,
        {
            ProcessCheckReturnFileStep: 2,
            ProcessNachaReturnFileStep: 1,
            ProcessManualPubRejectionStep: 1,
            PaymentExtractStep: 2,
        },
    )

    # ===============================================================================
    # [Day 5]
    #  - [Between 7:00 - 9:00 PM] Generate FINEOS vendor extract files
    #  - [After 9:00 PM] Run the FINEOS ECS task - Process Claim and Payment Extract
    # ===============================================================================

    with freeze_time("2021-05-05 19:00:00", tz_offset=5):
        generate_fineos_extract_files(test_dataset.scenario_dataset)

    with freeze_time("2021-05-05 21:30:00", tz_offset=5):
        process_fineos_extracts(
            test_dataset, mock_experian_client, test_db_session, test_db_other_session
        )

    # Additional Payment extract step has been added
    assert_report_queue_items_count(
        test_db_other_session,
        {
            ProcessCheckReturnFileStep: 2,
            ProcessNachaReturnFileStep: 1,
            ProcessManualPubRejectionStep: 1,
            PaymentExtractStep: 3,
        },
    )

    # ===============================================================================
    # [Day 6]
    #  - [Before 5:00 PM] Payment Integrity Team returns Payment Rejects File
    #  - [Between 5:00 - 7:00 PM PM] Run the PUB Processing ECS task - Rejects, PUB Transaction Files, Writeback
    # ===============================================================================
    with freeze_time("2021-05-06 14:00:00", tz_offset=5):
        generate_rejects_file(test_dataset)

    with freeze_time("2021-05-06 18:00:00", tz_offset=5):
        process_pub_payments(test_db_session, test_db_other_session)

    # Payment extract steps cleared
    assert_report_queue_items_count(
        test_db_other_session,
        {
            ProcessCheckReturnFileStep: 2,
            ProcessNachaReturnFileStep: 1,
            ProcessManualPubRejectionStep: 1,
        },
    )

    # ===============================================================================
    # [Day 7]
    #  - [9:00 AM] PUB sends ACH and Check response files
    #  - [11:00 AM] Run the PUB Response ECS task - response, writeback, reports
    # ===============================================================================

    with freeze_time("2021-05-07 09:00:00", tz_offset=5):
        generate_pub_returns(test_dataset)

    with freeze_time("2021-05-07 11:00:00", tz_offset=5):
        # Because we don't generate check files, we don't run the check
        # step twice, so remove that from the list:
        process_pub_responses(
            test_db_session,
            test_db_other_session,
            expected_steps_override=EXPECTED_STEPS_PROCESS_PUB_RESPONSES_NO_FILES,
        )

    # All queue items should be processed
    assert_report_queue_items_count(test_db_other_session, {})


def test_e2e_process_payment_reconciliation(
    local_test_db_session,
    local_test_db_other_session,
    local_initialize_factories_session,
    monkeypatch,
    set_exporter_env_vars,
):
    monkeypatch.setenv("FINEOS_PAYMENT_RECONCILIATION_EXTRACT_MAX_HISTORY_DATE", "2019-12-31")
    s3_config = payments_config.get_s3_config()

    extract_count = 10
    # Create payment reconciliation extract files
    with freeze_time("2021-05-01 20:00:00", tz_offset=5):
        folder_path = s3_config.fineos_adhoc_data_export_path
        generate_payment_reconciliation_extract_files(
            folder_path, get_current_timestamp_prefix(), extract_count
        )

        # run the task
        run_process_fineos_payment_reconciliation_extracts(
            db_session=local_test_db_session,
            log_entry_db_session=local_test_db_other_session,
            config=ProcessPaymentReconciliationExtractsConfiguration(["--steps", "ALL"]),
        )
        assert_success_file("pub-payments-process-snapshot")

        # confirm the files were generated
        processed_path = os.path.join(
            s3_config.pfml_fineos_extract_archive_path,
            payments_util.Constants.S3_INBOUND_PROCESSED_DIR,
            f"{get_current_timestamp_prefix()}payment-reconciliation-extract",
        )
        files = file_util.list_files(processed_path, recursive=True)
        assert len(files) == 3

        # confirm staging files were populated
        assert (
            len(local_test_db_session.query(FineosExtractPaymentFullSnapshot).all())
            == extract_count
        )
        assert (
            len(local_test_db_session.query(FineosExtractCancelledPayments).all()) == extract_count
        )
        assert (
            len(local_test_db_session.query(FineosExtractReplacedPayments).all()) == extract_count
        )

        # report
        assert_reports(
            s3_config.dfml_report_outbound_path,
            s3_config.pfml_error_reports_archive_path,
            PROCESS_FINEOS_RECONCILIATION_REPORTS,
            local_test_db_session,
        )

        # confirm metrics
        assert_metrics(
            local_test_db_other_session,
            "FineosExtractStep",
            {
                "fineos_prefix": "2021-05-01-21-00-00",
                "archive_path": "s3://test_bucket/cps/inbound/processed/2021-05-01-21-00-00-payment-reconciliation-extract",
                "records_processed_count": len(payments_util.PAYMENT_RECONCILIATION_EXTRACT_FILES)
                * extract_count,
            },
        )

        assert_metrics(
            local_test_db_other_session,
            "ReportStep",
            {
                "processed_report_count": len(PROCESS_FINEOS_RECONCILIATION_REPORTS),
                "report_error_count": 0,
                "report_generated_count": len(PROCESS_FINEOS_RECONCILIATION_REPORTS),
            },
        )


# == Common E2E Workflow Segments ==


def generate_test_dataset(
    scenario_descriptors: List[ScenarioDescriptor], db_session: db.Session
) -> TestDataSet:
    config = ScenarioDataConfig(
        scenarios_with_count=[
            ScenarioNameWithCount(scenario_name=scenario_descriptor.scenario_name, count=1)
            for scenario_descriptor in scenario_descriptors
        ]
    )
    scenario_dataset = generate_scenario_dataset(config=config, db_session=db_session)
    return TestDataSet(scenario_dataset)


def generate_fineos_extract_files(scenario_dataset: List[ScenarioData], round: int = 1):
    s3_config = payments_config.get_s3_config()

    fineos_data_export_path = s3_config.fineos_data_export_path
    fineos_extract_date_prefix = get_current_timestamp_prefix()

    # claimant extract
    generate_claimant_data_files(
        scenario_dataset, fineos_data_export_path, get_now_us_eastern(), round=round
    )
    # Confirm expected claimant files were generated
    assert_files(
        fineos_data_export_path,
        payments_util.CLAIMANT_EXTRACT_FILE_NAMES,
        fineos_extract_date_prefix,
    )
    # Confirm 1099 extract files were generated
    assert_files(
        fineos_data_export_path,
        payments_util.REQUEST_1099_EXTRACT_FILES_NAMES,
        fineos_extract_date_prefix,
    )

    # payment extract
    generate_payment_extract_files(
        scenario_dataset, fineos_data_export_path, get_now_us_eastern(), round=round
    )
    # Confirm expected payment files were generated
    assert_files(
        fineos_data_export_path,
        payments_util.PAYMENT_EXTRACT_FILE_NAMES,
        fineos_extract_date_prefix,
    )

    # vbi taskreport som extract
    generate_vbi_taskreport_som_extract_files(
        scenario_dataset, fineos_data_export_path, get_now_us_eastern()
    )
    assert_files(
        fineos_data_export_path,
        payments_util.VBI_TASKREPORT_SOM_EXTRACT_FILE_NAMES,
        fineos_extract_date_prefix,
    )


def generate_rejects_file(test_dataset: TestDataSet, round: int = 1):
    s3_config = payments_config.get_s3_config()

    rejects_file_received_path = os.path.join(
        s3_config.dfml_response_inbound_path, "Payment-Audit-Report-Response.csv"
    )

    audit_report_file_path = os.path.join(
        s3_config.dfml_report_outbound_path, "Payment-Audit-Report.csv"
    )

    parsed_audit_rows = parse_csv(audit_report_file_path)

    csv_file = file_util.write_file(rejects_file_received_path)
    csv_output = csv.DictWriter(
        csv_file,
        fieldnames=asdict(PAYMENT_AUDIT_CSV_HEADERS).values(),
        lineterminator="\n",
        quotechar='"',
        quoting=csv.QUOTE_ALL,
    )
    csv_output.writeheader()

    for parsed_audit_row in parsed_audit_rows:
        c_value = parsed_audit_row[PAYMENT_AUDIT_CSV_HEADERS.c_value]
        i_value = parsed_audit_row[PAYMENT_AUDIT_CSV_HEADERS.i_value]

        scenario_data = test_dataset.get_scenario_data_by_payment_ci(c_value, i_value)
        assert scenario_data, f"Can not find scenario data with c: {c_value}, i:{i_value}"

        scenario_descriptor = scenario_data.scenario_descriptor
        if scenario_descriptor.is_audit_rejected and scenario_descriptor.is_audit_skipped:
            raise Exception(
                "Invalid scenario with both audit rejected and audit skipped set to true"
            )

        if scenario_descriptor.is_audit_rejected:
            rejected_value = "Y"
            if scenario_descriptor.is_audit_approved_delayed and round > 1:
                rejected_value = "N"
            parsed_audit_row[
                PAYMENT_AUDIT_CSV_HEADERS.rejected_by_program_integrity
            ] = rejected_value
            parsed_audit_row[
                PAYMENT_AUDIT_CSV_HEADERS.rejected_notes
            ] = scenario_descriptor.audit_response_note

        if scenario_descriptor.is_audit_skipped:
            skipped_value = "Y"
            if scenario_descriptor.is_audit_approved_delayed and round > 1:
                skipped_value = "N"
            parsed_audit_row[PAYMENT_AUDIT_CSV_HEADERS.skipped_by_program_integrity] = skipped_value
            parsed_audit_row[
                PAYMENT_AUDIT_CSV_HEADERS.rejected_notes
            ] = scenario_descriptor.audit_response_note

    csv_output.writerows(parsed_audit_rows)
    csv_file.close()


def generate_pub_returns(test_dataset: TestDataSet):
    s3_config = payments_config.get_s3_config()

    pub_response_folder = os.path.join(s3_config.pub_moveit_inbound_path)
    PubACHResponseGenerator(test_dataset.scenario_dataset, pub_response_folder).run()

    PubCheckResponseGenerator(test_dataset.scenario_dataset, pub_response_folder).run()

    ManualPubRejectResponseGenerator(
        test_dataset.scenario_dataset, s3_config.dfml_response_inbound_path
    ).run()


def process_fineos_extracts(
    test_dataset: TestDataSet,
    mock_experian_client: soap_api.Client,
    db_session: db.Session,
    log_entry_db_session: db.Session,
    config: Optional[FineosTaskConfiguration] = None,
    expected_steps_override: List[Tuple[str, str]] = None,
):
    config = config if config else FineosTaskConfiguration(["--steps", "ALL"])
    with mock.patch(
        "massgov.pfml.delegated_payments.address_validation._get_experian_soap_client",
        return_value=mock_experian_client,
    ):
        run_fineos_ecs_task(
            db_session=db_session,
            log_entry_db_session=log_entry_db_session,
            config=config,
        )

    expected_steps = expected_steps_override or EXPECTED_STEPS_PROCESS_FINEOS_EXTRACTS
    assert_steps_run_in_order(log_entry_db_session, expected_steps)
    assert_success_file("pub-payments-process-fineos")
    test_dataset.populate_scenario_data_payments(db_session)
    test_dataset.populate_scenario_dataset_claims(db_session)


def process_pub_payments(
    db_session: db.Session,
    log_entry_db_session: db.Session,
    config: Optional[ProcessPubPaymentsTaskConfiguration] = None,
    expected_steps_override: List[Tuple[str, str]] = None,
):
    config = config if config else ProcessPubPaymentsTaskConfiguration(["--steps", "ALL"])
    run_process_pub_payments_ecs_task(
        db_session=db_session,
        log_entry_db_session=log_entry_db_session,
        config=config,
    )

    expected_steps = expected_steps_override or EXPECTED_STEPS_PROCESS_PUB_PAYMENTS
    assert_steps_run_in_order(log_entry_db_session, expected_steps)
    assert_success_file("pub-payments-create-pub-files")


def process_pub_responses(
    db_session: db.Session,
    log_entry_db_session: db.Session,
    config: Optional[ProcessPubResponsesTaskConfiguration] = None,
    expected_steps_override: List[Tuple[Type[Step], str]] = None,
):
    config = config if config else ProcessPubResponsesTaskConfiguration(["--steps", "ALL"])
    run_process_pub_responses_ecs_task(
        db_session=db_session,
        log_entry_db_session=log_entry_db_session,
        config=config,
    )

    expected_steps = expected_steps_override or EXPECTED_STEPS_PROCESS_PUB_RESPONSES
    assert_steps_run_in_order(log_entry_db_session, expected_steps)
    assert_success_file("pub-payments-process-pub-returns")


def setup_common_env_variables(monkeypatch):
    monkeypatch.setenv("FINEOS_CLAIMANT_EXTRACT_MAX_HISTORY_DATE", "2021-04-30")
    monkeypatch.setenv("FINEOS_PAYMENT_EXTRACT_MAX_HISTORY_DATE", "2021-04-30")
    monkeypatch.setenv("FINEOS_VBI_TASKREPORT_SOM_EXTRACT_MAX_HISTORY_DATE", "2021-04-30")

    monkeypatch.setenv("DFML_PUB_ACCOUNT_NUMBER", "123456789")
    monkeypatch.setenv("DFML_PUB_ROUTING_NUMBER", "234567890")
    monkeypatch.setenv("PUB_PAYMENT_STARTING_CHECK_NUMBER", "100")
    monkeypatch.setenv("USE_AUDIT_REJECT_TRANSACTION_STATUS", "1")
    monkeypatch.setenv("ENABLE_EMPLOYER_REIMBURSEMENT_PAYMENTS", "0")


# == Assertion Helpers ==


def assert_files(folder_path, expected_files, file_prefix=""):
    files_in_folder = file_util.list_files(folder_path)
    for expected_file in expected_files:
        assert (
            f"{file_prefix}{expected_file}" in files_in_folder
        ), f"Can not find {file_prefix}{expected_file} under path: {folder_path}, found files: {files_in_folder}"


def assert_claim_state_for_scenarios(
    test_dataset: TestDataSet,
    scenario_names: List[ScenarioName],
    end_state: Optional[LkState],
    db_session: db.Session,
):
    for scenario_name in scenario_names:
        scenario_data_items = test_dataset.get_scenario_data_by_name(scenario_name)

        assert scenario_data_items is not None, f"No data found for scenario: {scenario_name}"

        for scenario_data in scenario_data_items:
            claim = scenario_data.claim
            state_log = state_log_util.get_latest_state_log_in_flow(
                claim, Flow.DELEGATED_CLAIM_VALIDATION, db_session
            )
            if end_state is None:
                assert (
                    state_log is None
                ), f"Expected state log to be none for claim in scenario {scenario_name}, found {state_log.end_state.state_description}"
            else:
                assert (
                    state_log is not None
                ), f"No state found for scenario: {scenario_name}, {claim.state_logs}"
                assert (
                    state_log.end_state_id == end_state.state_id
                ), f"Unexpected claim state for scenario: {scenario_name}, expected: {end_state.state_description}, found: {state_log.end_state.state_description}"


def assert_payment_state_for_scenarios(
    test_dataset: TestDataSet,
    scenario_names: List[ScenarioName],
    end_state: LkState,
    db_session: db.Session,
    flow: LkFlow = Flow.DELEGATED_PAYMENT,
    check_additional_payment: bool = False,
):
    for scenario_name in scenario_names:
        scenario_data_items = test_dataset.get_scenario_data_by_name(scenario_name)
        assert scenario_data_items is not None, f"No data found for scenario: {scenario_name}"

        for scenario_data in scenario_data_items:
            if check_additional_payment:
                payment = scenario_data.additional_payment
            else:
                payment = scenario_data.payment
            assert payment is not None, f"No payment found for scenario: {scenario_name}"

            state_log = state_log_util.get_latest_state_log_in_flow(payment, flow, db_session)

            assert (
                state_log is not None
            ), f"No payment state log found for scenario: {scenario_name}"
            assert (
                state_log.end_state_id == end_state.state_id
            ), f"Unexpected payment state for scenario: {scenario_name}, expected: {end_state.state_description}, found: {state_log.end_state.state_description}, validation: {state_log.outcome}"


def assert_prenote_state(
    test_dataset: TestDataSet,
    scenario_names: List[ScenarioName],
    expected_prenote_state: PrenoteState,
):
    assertion_errors = []
    for scenario_name in scenario_names:
        scenario_data_items = test_dataset.get_scenario_data_by_name(scenario_name)

        assert scenario_data_items is not None, f"No data found for scenario: {scenario_name}"

        for scenario_data in scenario_data_items:
            payment = scenario_data.payment

            assert payment is not None, f"No Payment found: {scenario_name}"

            pub_eft = payment.pub_eft

            assert pub_eft is not None, f"No PubEft found: {scenario_name}"

            if pub_eft.prenote_state_id != expected_prenote_state.prenote_state_id:
                assertion_errors.append(
                    f"Scenario: {scenario_name}, found state: {pub_eft.prenote_state.prenote_state_description}\n"
                )

    errors = "".join(assertion_errors)
    assert (
        len(assertion_errors) == 0
    ), f"Unexpected prenote state for scenario(s) - expected state: {expected_prenote_state.prenote_state_description}\n{errors}"


def assert_employee_state_for_scenarios(
    test_dataset: TestDataSet,
    scenario_names: List[ScenarioName],
    end_state: LkState,
    flow: LkFlow,
    db_session: db.Session,
):
    for scenario_name in scenario_names:
        scenario_data_items = test_dataset.get_scenario_data_by_name(scenario_name)

        assert scenario_data_items is not None, f"No data found for scenario: {scenario_name}"

        for scenario_data in scenario_data_items:
            employee = scenario_data.employee

            state_log = state_log_util.get_latest_state_log_in_flow(employee, flow, db_session)

            assert (
                state_log is not None
            ), f"No employee state log found for scenario: {scenario_name}"
            assert (
                state_log.end_state_id == end_state.state_id
            ), f"Unexpected employee state for scenario: {scenario_name}, expected: {end_state.state_description}, found: {state_log.end_state.state_description}"


# Assert csv content contains expected row values (may be a subset of columns in rows)
# Will match part of the expected value
# Note: not order sensitive
def assert_csv_content(rows: Dict[str, str], rows_expected_values: List[Dict[str, str]]):
    def is_row_match(row_expected_values):
        for row in rows:
            match = False
            for column, expected_value in row_expected_values.items():
                value = row.get(column, None)
                if expected_value == "":
                    match = value == expected_value
                else:
                    match = (value == expected_value) or bool(re.match(expected_value, value))

                if not match:
                    break

            if match:
                return True

        return False

    for row_expected_values in rows_expected_values:
        assert is_row_match(
            row_expected_values
        ), f"Expected csv row not found - expected row values: {row_expected_values}"


def assert_reports(
    reports_folder_path: str,
    reports_archive_folder_path: str,
    report_names: List[ReportName],
    db_session: db.Session,
):
    date_folder = get_current_date_folder()
    timestamp_prefix = get_current_timestamp_prefix()

    for report_name in report_names:
        report = get_report_by_name(report_name)
        file_name = f"{report.report_name.value}.csv"

        outbound_folder = reports_folder_path
        sent_folder = os.path.join(
            reports_archive_folder_path, payments_util.Constants.S3_OUTBOUND_SENT_DIR, date_folder
        )

        assert_files(outbound_folder, [file_name])
        assert_files(sent_folder, [file_name], timestamp_prefix)

        assert_ref_file(
            f"{reports_archive_folder_path}/sent/{date_folder}/{timestamp_prefix}{file_name}",
            ReferenceFileType.DELEGATED_PAYMENT_REPORT_FILE,
            db_session,
        )


def assert_success_file(process_name):
    s3_config = payments_config.get_s3_config()

    processed_folder = os.path.join(
        s3_config.pfml_error_reports_archive_path,
        payments_util.Constants.S3_INBOUND_PROCESSED_DIR,
        get_current_date_folder(),
    )
    expected_file_name = f"{process_name}.SUCCESS"
    assert_files(processed_folder, [expected_file_name], get_current_timestamp_prefix())


def assert_report_queue_items_count(
    log_report_db_session: db.Session,
    import_log_expected_values: Optional[Dict[Type[Step], int]] = None,
):
    import_log_expected_values = import_log_expected_values if import_log_expected_values else {}
    expected_sources = set()
    assertion_errors = []

    report_queue_source_counts = (
        log_report_db_session.query(
            func.count(ImportLog.source),
            ImportLog.source,
        )
        .join(ImportLogReportQueue)
        .group_by(ImportLog.source)
        .all()
    )

    for step, expected_count in import_log_expected_values.items():
        source = step.__name__
        expected_sources.add(source)
        found_source = next(x for x in report_queue_source_counts if x.source == source)
        found_count = found_source[0] if found_source else 0
        if expected_count != found_count:
            assertion_errors.append(
                f"log source: {source}, expected: {expected_count}, found: {found_count}"
            )

    for found_count, source in report_queue_source_counts:
        if source not in expected_sources:
            assertion_errors.append(f"log source: {source}, expected: 0, found: {found_count}")

    errors = "\n".join(assertion_errors)
    assert len(assertion_errors) == 0, f"Unexpected report queue item count(s)\n{errors}"


def assert_metrics(
    log_report_db_session: db.Session,
    log_report_name: str,
    metrics_expected_values: Dict[str, Any],
    description: str = "",
    log_report_index: int = 0,  # we may have more than one report for a step
):
    log_reports = (
        log_report_db_session.query(ImportLog)
        .filter(ImportLog.source == log_report_name)
        .order_by(ImportLog.import_log_id.desc())
        .all()
    )

    log_report = log_reports[log_report_index]
    log_report = json.loads(log_report.report)

    assertion_errors = []
    for metric_key, expected_value in metrics_expected_values.items():
        value = log_report.get(metric_key, None)
        if value != expected_value:
            assertion_errors.append(
                f"metric: {metric_key}, expected: {expected_value}, found: {value}\n"
            )

    errors = "".join(assertion_errors)
    assert (
        len(assertion_errors) == 0
    ), f"Unexpected metric value(s) in log report '{log_report_name}', description: {description}\n{errors}"


def assert_steps_run_in_order(
    log_report_db_session: db.Session, step_type_pairs: List[Tuple[Step, str]]
):
    # Grab every import log during the current time freeze
    reports = (
        log_report_db_session.query(ImportLog)
        .filter(ImportLog.created_at >= get_now_us_eastern())
        .order_by(ImportLog.import_log_id.asc())
        .all()
    )

    assert len(reports) == len(
        step_type_pairs
    ), f"Expected {len(step_type_pairs)} steps to have run and generated import logs, and only found {len(reports)}"

    assertion_errors = []
    for report, step_type_pair in zip(reports, step_type_pairs):
        report_log = f"{report.import_log_id}, {report.source}, {report.import_type}"

        if step_type_pair[0].__name__ != report.source or step_type_pair[1] != report.import_type:
            assertion_errors.append(
                f"Expected pair source+type of {step_type_pair} and found {report_log}"
            )

        if report.status != "success":
            assertion_errors.append(f"Import log {report_log} was not successful")

        if not report.report:
            assertion_errors.append(f"No metrics found for import log {report_log}")
        else:
            # Convert it to a dictionary and verify at least some metrics were created
            # although we won't worry about specifics here.
            data = json.loads(report.report)
            if len(data) == 0:
                assertion_errors.append(f"No metrics generated for import log {report_log}")

            for metric in step_type_pair[0].Metrics:
                if metric not in data:
                    assertion_errors.append(f"Metric {metric} was missing in {report_log}")

    assert (
        len(assertion_errors) == 0
    ), f"Unxpected issues encountered with import log metrics: {assertion_errors}"


def assert_writeback_for_stage(
    test_dataset: TestDataSet,
    writeback_scenario_names: List[ScenarioName],
    db_session: db.Session,
    do_related_payments: bool = True,
):

    # Validate file creation
    s3_config = payments_config.get_s3_config()
    date_folder = get_current_date_folder()
    timestamp_prefix = get_current_timestamp_prefix()

    writeback_folder_path = os.path.join(s3_config.fineos_data_import_path)
    assert_files(writeback_folder_path, ["pei_writeback.csv"], timestamp_prefix)

    writeback_file_path = f"{s3_config.pfml_fineos_writeback_archive_path}sent/{date_folder}/{timestamp_prefix}pei_writeback.csv"
    assert_ref_file(writeback_file_path, ReferenceFileType.PEI_WRITEBACK, db_session)

    # Validate FINEOS status writeback states
    assert_payment_state_for_scenarios(
        test_dataset=test_dataset,
        scenario_names=writeback_scenario_names,
        end_state=State.DELEGATED_FINEOS_WRITEBACK_SENT,
        flow=Flow.DELEGATED_PEI_WRITEBACK,
        db_session=db_session,
    )

    # Validate counts
    generic_flow_scenario_payments = []
    for writeback_scenario_name in writeback_scenario_names:
        scenario_payments = test_dataset.get_scenario_payments_by_scenario_name(
            writeback_scenario_name
        )
        # In some cases, we know the related payments (ie. tax withholdings)
        # Won't have a new writeback, so skip validating them below
        for scenario_payment in scenario_payments:
            if not do_related_payments and scenario_payment.payment_transaction_type_id in [
                PaymentTransactionType.STATE_TAX_WITHHOLDING.payment_transaction_type_id,
                PaymentTransactionType.FEDERAL_TAX_WITHHOLDING.payment_transaction_type_id,
            ]:
                continue
            generic_flow_scenario_payments.append(scenario_payment)

    generic_flow_scenario_payment_ids = set([p.payment_id for p in generic_flow_scenario_payments])

    writeback_details = (
        db_session.query(FineosWritebackDetails)
        .filter(
            FineosWritebackDetails.payment_id.in_(generic_flow_scenario_payment_ids),
            FineosWritebackDetails.created_at
            >= get_now_us_eastern(),  # get writeback items created during current time freeze
        )
        .all()
    )
    assert len(writeback_details) == len(generic_flow_scenario_payment_ids)

    # Validate csv content
    expected_csv_rows = []
    for p in generic_flow_scenario_payments:
        expected_csv_row = {
            "pei_C_Value": p.fineos_pei_c_value,
            "pei_I_Value": p.fineos_pei_i_value,
        }

        # TODO remove condition when we are fully transitioned to using generic flow
        if p.payment_id in generic_flow_scenario_payment_ids:
            transaction_status = get_writeback_transaction_status_for_payment(db_session, p)
            expected_csv_row[
                "transactionStatus"
            ] = transaction_status.transaction_status_description
            expected_csv_row["status"] = transaction_status.writeback_record_status

            transaction_status_date = payments_util.get_transaction_status_date(p)
            expected_csv_row["transStatusDate"] = transaction_status_date.strftime(
                "%Y-%m-%d %H:%M:%S"
            )

        else:
            expected_csv_row["status"] = "Active"

        expected_csv_rows.append(expected_csv_row)

    writeback_csv_rows = parse_csv(writeback_file_path)
    assert_csv_content(writeback_csv_rows, expected_csv_rows)


# == Utility Helpers ==


def parse_csv(csv_file_path: str):
    parsed_csv = csv.DictReader(file_util.open_stream(csv_file_path))
    return list(parsed_csv)


def get_payments_in_end_state(db_session: db.Session, end_state: LkState) -> List[Payment]:
    state_logs = state_log_util.get_all_latest_state_logs_in_end_state(
        associated_class=state_log_util.AssociatedClass.PAYMENT,
        end_state=end_state,
        db_session=db_session,
    )

    return [state_log.payment for state_log in state_logs]


def get_writeback_transaction_status_for_payment(
    db_session: db.Session, payment: Payment
) -> LkFineosWritebackTransactionStatus:
    writeback_details = (
        db_session.query(FineosWritebackDetails)
        .filter(FineosWritebackDetails.payment_id == payment.payment_id)
        .order_by(FineosWritebackDetails.created_at.desc())
        .first()
    )

    assert writeback_details is not None

    return writeback_details.transaction_status


def get_current_date_folder():
    return get_now_us_eastern().strftime("%Y-%m-%d")


def get_current_timestamp_prefix():
    return get_now_us_eastern().strftime("%Y-%m-%d-%H-%M-%S-")


def assert_ref_file(file_path: str, ref_file_type: ReferenceFileType, db_session: db.Session):
    found = (
        db_session.query(ReferenceFile)
        .filter(ReferenceFile.file_location == file_path)
        .filter(ReferenceFile.reference_file_type_id == ref_file_type.reference_file_type_id)
        .one_or_none()
    )

    assert (
        found is not None
    ), f"No reference file found for type: {ref_file_type.reference_file_type_description}, file path: {file_path}"
