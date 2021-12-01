import enum
from decimal import Decimal
from typing import cast

import massgov.pfml.delegated_payments.delegated_payments_util as payments_util
import massgov.pfml.util.logging as logging
from massgov.pfml.db.models.employees import AbsencePeriod, ReferenceFile, ReferenceFileType
from massgov.pfml.db.models.payments import (
    FineosExtractVbiLeavePlanRequestedAbsence,
    FineosExtractVPaidLeaveInstruction,
)
from massgov.pfml.delegated_payments.step import Step

logger = logging.get_logger(__name__)


class IAWWExtractStep(Step):
    """
    Inspect latest staged Individual Average Weekly Wage (IAWW) data and
    update fineos_average_weekly_wage for matching absence_periods
    """

    class Metrics(str, enum.Enum):
        PAID_LEAVE_INSTRUCTION_RECORD_COUNT = "paid_leave_instruction_record_count"
        PROCESSED_PAID_LEAVE_INSTRUCTION_COUNT = "processed_paid_leave_instruction_count"
        PAID_LEAVE_INSTRUCTION_VALIDATION_ISSUE_COUNT = (
            "paid_leave_instruction_validation_issue_count"
        )
        LEAVE_PLAN_REQUESTED_ABSENCE_RECORD_COUNT = "leave_plan_requested_absence_record_count"
        LEAVE_PLAN_REQUESTED_ABSENCE_RECORD_VALIDAION_ISSUE_COUNT = (
            "leave_plan_requested_absence_record_validation_issue_count"
        )
        NOT_MATCHING_LEAVE_PLAN_REQUESTED_ABSENCE_RECORD_COUNT = (
            "not_matching_leave_plan_requested_absence_record_count"
        )
        ABSENCE_PERIODS_UPDATED = "absence_periods_updated"

    def run_step(self):
        logger.info("Processing IAWW extract data")
        self.process_records()
        logger.info("Successfully processed IAWW extract data")

    def process_paid_leave_instruction_record(
        self,
        raw_paid_leave_instruction_record: FineosExtractVPaidLeaveInstruction,
        reference_file: ReferenceFile,
    ) -> None:
        self.increment(self.Metrics.PROCESSED_PAID_LEAVE_INSTRUCTION_COUNT)

        c_value = raw_paid_leave_instruction_record.c
        i_value = raw_paid_leave_instruction_record.i

        validation_container = payments_util.ValidationContainer(str(f"C={c_value},I={i_value}"))

        try:
            aww_value = payments_util.validate_db_input(
                "averageweeklywage_monamt",
                raw_paid_leave_instruction_record,
                validation_container,
                True,
                custom_validator_func=payments_util.amount_validator,
            )
            c_leaveplan_value = payments_util.validate_db_input(
                "c_selectedleaveplan", raw_paid_leave_instruction_record, validation_container, True
            )
            i_leaveplan_value = payments_util.validate_db_input(
                "i_selectedleaveplan", raw_paid_leave_instruction_record, validation_container, True
            )

            if validation_container.has_validation_issues():
                self.increment(self.Metrics.PAID_LEAVE_INSTRUCTION_VALIDATION_ISSUE_COUNT)
                logger.info(
                    f"Encoutred validation issue while processing leave instruction record: {validation_container.get_reasons()}"
                )
                return None

            logger.debug(f"Processing paid leave instruction record C={c_value}, I={i_value}")

            leave_plan_requested_absence_record = (
                self.db_session.query(FineosExtractVbiLeavePlanRequestedAbsence)
                .filter(
                    FineosExtractVbiLeavePlanRequestedAbsence.selectedplan_classid
                    == c_leaveplan_value,
                    FineosExtractVbiLeavePlanRequestedAbsence.selectedplan_indexid
                    == i_leaveplan_value,
                    FineosExtractVbiLeavePlanRequestedAbsence.reference_file_id
                    == reference_file.reference_file_id,
                )
                .first()
            )

            if leave_plan_requested_absence_record:
                self.increment(self.Metrics.LEAVE_PLAN_REQUESTED_ABSENCE_RECORD_COUNT)

                leaverequest_id_value = payments_util.validate_db_input(
                    "leaverequest_id",
                    leave_plan_requested_absence_record,
                    validation_container,
                    True,
                )

                if leaverequest_id_value is None:
                    self.increment(
                        self.Metrics.LEAVE_PLAN_REQUESTED_ABSENCE_RECORD_VALIDAION_ISSUE_COUNT
                    )
                    logger.info("Leave plan requested does not contain leaverequest_id_value")
                    return None

                # TO-DO post MVP we will need to handle an updated IAWW from FINEOS, but for the MVP
                # we will only populate the IAWW if we don't already have a value for it
                absence_periods = (
                    self.db_session.query(AbsencePeriod)
                    .filter(AbsencePeriod.fineos_leave_request_id == int(leaverequest_id_value))
                    .filter(AbsencePeriod.fineos_average_weekly_wage.is_(None))
                    .all()
                )

                for absence_period in absence_periods:
                    absence_period.fineos_average_weekly_wage = Decimal(cast(str, aww_value))
                    self.increment(self.Metrics.ABSENCE_PERIODS_UPDATED)
                    logger.debug(
                        f"Absence period {absence_period.absence_period_id} updated with AWW={aww_value}"
                    )
            else:
                self.increment(self.Metrics.NOT_MATCHING_LEAVE_PLAN_REQUESTED_ABSENCE_RECORD_COUNT)
                logger.info(
                    f"No corresponding leave plan requested absence record was found C={c_leaveplan_value}, I={i_leaveplan_value}, Reference file id={reference_file.reference_file_id}"
                )

            logger.debug(f"Done processing paid leave instruction record C={c_value}, I={i_value}")

        except Exception:
            # An exception during processing would indicate
            # either a bug or a scenario that we believe invalidates
            # an entire file and warrants investigating
            logger.exception(
                "An error occurred while processing paid leave instructions for CI: %s, %s",
                c_value,
                i_value,
            )
            raise

        return None

    def process_records(self) -> None:
        # Grab the latest payment extract reference file
        reference_file = (
            self.db_session.query(ReferenceFile)
            .filter(
                ReferenceFile.reference_file_type_id
                == ReferenceFileType.FINEOS_IAWW_EXTRACT.reference_file_type_id
            )
            .order_by(ReferenceFile.created_at.desc())
            .first()
        )
        if not reference_file:
            raise Exception(
                "This would only happen the first time you run in an env and have no extracts, make sure FINEOS has created extracts"
            )
        if reference_file.processed_import_log_id:
            logger.warning(
                "Already processed the most recent extracts for %s in import run %s",
                reference_file.file_location,
                reference_file.processed_import_log_id,
            )
            return

        raw_paid_leave_instruction_records = (
            self.db_session.query(FineosExtractVPaidLeaveInstruction)
            .filter(
                FineosExtractVPaidLeaveInstruction.reference_file_id
                == reference_file.reference_file_id
            )
            .all()
        )
        for raw_paid_leave_instruction_record in raw_paid_leave_instruction_records:
            self.increment(self.Metrics.PAID_LEAVE_INSTRUCTION_RECORD_COUNT)
            self.process_paid_leave_instruction_record(
                raw_paid_leave_instruction_record, reference_file
            )

        reference_file.processed_import_log_id = self.get_import_log_id()
