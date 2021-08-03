import os
from dataclasses import dataclass
from datetime import date
from typing import Callable, List, Optional, Tuple, cast

from sqlalchemy import func

import massgov.pfml.api.util.state_log_util as state_log_util
import massgov.pfml.db as db
import massgov.pfml.delegated_payments.delegated_payments_util as payments_util
import massgov.pfml.util.files as file_util
import massgov.pfml.util.logging as logging
from massgov.pfml.db.models.employees import (
    Address,
    ClaimType,
    Employee,
    Payment,
    PaymentCheck,
    PaymentMethod,
    ReferenceFile,
    ReferenceFileType,
    State,
)
from massgov.pfml.db.models.payments import FineosWritebackDetails, FineosWritebackTransactionStatus
from massgov.pfml.delegated_payments.check_issue_file import CheckIssueEntry, CheckIssueFile
from massgov.pfml.delegated_payments.ez_check import EzCheckFile, EzCheckHeader, EzCheckRecord

logger = logging.get_logger(__name__)


class UnSupportedClaimTypeException(Exception):
    """An error during Claim Type other than Family or Medical"""


@dataclass
class RecordContainer:
    ez_check_record: EzCheckRecord
    positive_pay_record: CheckIssueEntry


class Constants:
    SIMPLE_EZ_CHECK_FILENAME = f"{payments_util.Constants.FILE_NAME_PUB_EZ_CHECK}.csv"
    EZ_CHECK_FILENAME_FORMAT = f"%Y-%m-%d-%H-%M-%S-{SIMPLE_EZ_CHECK_FILENAME}"

    EZ_CHECK_MAX_NAME_LENGTH = 85

    # e.g. PFML Medical Leave Payment NTN-240483-ABS-01 [03/01/2021-03/07/2021]
    EZ_CHECK_MEMO_FORMAT = "PFML {} Payment {} [{}-{}]"
    EZ_CHECK_MEMO_DATE_FORMAT = "%m/%d/%Y"

    SIMPLE_POSITIVE_PAY_FILENAME = f"{payments_util.Constants.FILE_NAME_PUB_POSITIVE_PAY}.txt"
    POSITIVE_PAY_FILENAME_FORMAT = f"%Y-%m-%d-%H-%M-%S-{SIMPLE_POSITIVE_PAY_FILENAME}"

    US_COUNTRY_CODE = "US"


def create_check_file(
    db_session: db.Session,
    count_incrementer: Optional[Callable[[str], None]] = None,
    import_log_id: Optional[int] = None,
) -> Tuple[Optional[EzCheckFile], Optional[CheckIssueFile]]:
    eligible_check_payments = _get_eligible_check_payments(db_session)

    if len(eligible_check_payments) == 0:
        logger.info("Not creating a check file because we found no eligible check payments")
        return (None, None)

    # Convert all the payments into EzCheckRecords before initializing the EzCheckFile because
    # all of the eligible payments may fail to be converted. If that happens we also don't want
    # to write an EzCheckFile to PUB.
    encountered_exception = False
    records: List[Tuple[Payment, RecordContainer]] = []

    starting_check_number = os.environ.get("PUB_PAYMENT_STARTING_CHECK_NUMBER")
    if not starting_check_number or not starting_check_number.isnumeric():
        raise Exception("PUB_PAYMENT_STARTING_CHECK_NUMBER is a required environment variable")

    # Generally, we'll start the count from the max check number when we first run in
    # an environment, otherwise we use the maximum from the DB
    # In the event we want to change the next check number, we can
    # update the environment variable to what we want. Note that the next number used
    # is actually that number+1.
    db_check_num = db_session.query(func.max(PaymentCheck.check_number)).scalar()
    if not db_check_num:
        check_number = int(starting_check_number)
    else:
        check_number = max(db_check_num, int(starting_check_number))

    for payment in eligible_check_payments:
        try:
            if count_incrementer:
                count_incrementer("check_payment_count")
            check_number += 1
            payment.check = PaymentCheck(check_number=check_number)
            ez_check_record = _convert_payment_to_ez_check_record(payment, check_number)
            positive_pay_record = _convert_payment_to_check_issue_entry(payment)

            records.append(
                (
                    payment,
                    RecordContainer(
                        ez_check_record=ez_check_record, positive_pay_record=positive_pay_record
                    ),
                )
            )
        except payments_util.ValidationIssueException as e:
            msg = ", ".join([str(issue) for issue in e.issues])
            logger.exception("Error converting payment into PUB EZ check format: " + msg)
            encountered_exception = True
        except Exception:
            logger.exception("Error converting payment into PUB EZ check format")
            encountered_exception = True

    if encountered_exception:
        logger.info("Not creating a check file because we encountered issues adding records")

        # If a single check payment is not added to the payment, then we do not send any check
        # payments to PUB so we need to count all of the check payments we attempted to add.
        if count_incrementer:
            [count_incrementer("failed_to_add_transaction_count") for _ in eligible_check_payments]
        return (None, None)

    ez_check_file = EzCheckFile(_get_ez_check_header())
    check_issue_file = CheckIssueFile()

    for payment, record in records:
        ez_check_file.add_record(record.ez_check_record)
        check_issue_file.add_entry(record.positive_pay_record)

        outcome = state_log_util.build_outcome("Payment added to PUB EZ Check file")
        state_log_util.create_finished_state_log(
            associated_model=payment,
            end_state=State.DELEGATED_PAYMENT_PUB_TRANSACTION_CHECK_SENT,
            outcome=outcome,
            db_session=db_session,
        )

        transaction_status = FineosWritebackTransactionStatus.PAID
        state_log_util.create_finished_state_log(
            end_state=State.DELEGATED_ADD_TO_FINEOS_WRITEBACK,
            outcome=outcome,
            associated_model=payment,
            import_log_id=import_log_id,
            db_session=db_session,
        )
        writeback_details = FineosWritebackDetails(
            payment=payment,
            transaction_status_id=transaction_status.transaction_status_id,
            import_log_id=import_log_id,
        )
        db_session.add(writeback_details)

    return ez_check_file, check_issue_file


def send_check_file(
    check_file: EzCheckFile, archive_folder_path: str, outgoing_folder_path: str
) -> ReferenceFile:
    now = payments_util.get_now()
    ez_check_file_name = now.strftime(Constants.EZ_CHECK_FILENAME_FORMAT)
    archive_s3_path = payments_util.build_archive_path(
        archive_folder_path, payments_util.Constants.S3_OUTBOUND_SENT_DIR, ez_check_file_name, now
    )

    with file_util.write_file(archive_s3_path) as s3_file:
        check_file.write_to(s3_file)
    logger.info("Wrote check file to archive path %s", archive_s3_path)

    # The outgoing file doesn't have the timestamp in the path and goes directly in the directory configured
    outgoing_s3_path = os.path.join(outgoing_folder_path, Constants.SIMPLE_EZ_CHECK_FILENAME)
    file_util.copy_file(archive_s3_path, outgoing_s3_path)
    logger.info("Copied check file to outgoing path %s", outgoing_s3_path)

    return ReferenceFile(
        file_location=archive_s3_path,
        reference_file_type_id=ReferenceFileType.PUB_EZ_CHECK.reference_file_type_id,
    )


def send_positive_pay_file(
    check_file: CheckIssueFile, archive_folder_path: str, outgoing_folder_path: str
) -> ReferenceFile:
    now = payments_util.get_now()
    positive_pay_file_name = now.strftime(Constants.POSITIVE_PAY_FILENAME_FORMAT)
    archive_s3_path = payments_util.build_archive_path(
        archive_folder_path,
        payments_util.Constants.S3_OUTBOUND_SENT_DIR,
        positive_pay_file_name,
        now,
    )

    with file_util.write_file(archive_s3_path, "wb") as s3_file:
        s3_file.write(check_file.to_bytes())
    logger.info("Wrote positive pay file to archive path %s", archive_s3_path)

    # The outgoing file doesn't have the timestamp in the path and goes directly in the directory configured
    outgoing_s3_path = os.path.join(outgoing_folder_path, Constants.SIMPLE_POSITIVE_PAY_FILENAME)
    file_util.copy_file(archive_s3_path, outgoing_s3_path)
    logger.info("Copied positive pay file to outgoing path %s", outgoing_s3_path)

    return ReferenceFile(
        file_location=archive_s3_path,
        reference_file_type_id=ReferenceFileType.PUB_POSITIVE_PAYMENT.reference_file_type_id,
    )


def _get_eligible_check_payments(db_session: db.Session) -> List[Payment]:
    state_logs = state_log_util.get_all_latest_state_logs_in_end_state(
        associated_class=state_log_util.AssociatedClass.PAYMENT,
        end_state=State.DELEGATED_PAYMENT_ADD_TO_PUB_TRANSACTION_CHECK,
        db_session=db_session,
    )

    for state_log in state_logs:
        if state_log.payment.disb_method_id != PaymentMethod.CHECK.payment_method_id:
            raise Exception(
                f"Non-Check payment method detected in state log: { state_log.state_log_id }, payment: {state_log.payment.payment_id}"
            )

    check_payments = [state_log.payment for state_log in state_logs]

    return check_payments


def _convert_payment_to_check_issue_entry(payment: Payment) -> CheckIssueEntry:
    employee = payment.claim.employee

    return CheckIssueEntry(
        status_code="I",  # Always use the issue code? Use "V" for void.
        check_number=payment.check.check_number,  # check number has already been generated in previous EZ Check step
        issue_date=cast(date, payment.payment_date),
        amount=payment.amount,
        payee_id=payment.pub_individual_id,
        payee_name=_format_employee_name_for_ez_check(employee),
        account_number=int(os.environ.get("DFML_PUB_ACCOUNT_NUMBER")),  # type: ignore
    )


def _convert_payment_to_ez_check_record(payment: Payment, check_number: int) -> EzCheckRecord:
    if payment.claim_type_id not in [
        ClaimType.FAMILY_LEAVE.claim_type_id,
        ClaimType.MEDICAL_LEAVE.claim_type_id,
    ]:
        raise UnSupportedClaimTypeException(
            "Expected claim type to be either family or medical. Found {}".format(
                payment.claim_type.claim_type_description
            )
        )

    employee = payment.claim.employee
    experian_address_pair = payment.experian_address_pair
    address = cast(Address, experian_address_pair.experian_address)

    geo_state = address.geo_state

    return EzCheckRecord(
        check_number=check_number,
        check_date=cast(date, payment.payment_date),
        amount=payment.amount,
        memo=_format_check_memo(payment),
        payee_name=_format_employee_name_for_ez_check(employee),
        address_line_1=cast(str, address.address_line_one),
        address_line_2=address.address_line_two,
        city=cast(str, address.city),
        state=cast(str, geo_state.geo_state_description),
        zip_code=cast(str, address.zip_code),
        # Hard-coding country to US because we store country codes in 3 characters in our database
        # and the EZcheck format requires 2 character country codes.
        country=Constants.US_COUNTRY_CODE,
    )


def _format_check_memo(payment: Payment) -> str:
    start_date = cast(date, payment.period_start_date).strftime(Constants.EZ_CHECK_MEMO_DATE_FORMAT)
    end_date = cast(date, payment.period_end_date).strftime(Constants.EZ_CHECK_MEMO_DATE_FORMAT)

    claim_type = payment.claim_type.claim_type_description if payment.claim_type else ""

    return Constants.EZ_CHECK_MEMO_FORMAT.format(
        claim_type, payment.claim.fineos_absence_id, start_date, end_date
    )


# Follow same truncation rules as described for the ACH file names.
# https://lwd.atlassian.net/wiki/spaces/API/pages/1313800323/PUB+ACH+File+Format
def _format_employee_name_for_ez_check(employee: Employee) -> str:
    # If last name is > 85 characters, truncate to 85.
    last_name = employee.last_name[: Constants.EZ_CHECK_MAX_NAME_LENGTH]
    remaining_characters = Constants.EZ_CHECK_MAX_NAME_LENGTH - len(last_name)

    # If last name is exactly 84 or 85 characters just use last name.
    if remaining_characters <= 1:
        return last_name

    # If last name < 85 characters use full last name and truncate the first name to use the
    # remaining space.
    remaining_characters = remaining_characters - 1  # Make room for the space character.
    return "{} {}".format(employee.first_name[:remaining_characters], last_name)


def _get_ez_check_header() -> EzCheckHeader:
    return EzCheckHeader(
        name_line_1="MA Department of Family and Medical Leave",
        name_line_2="Commonwealth of Massachusetts",
        address_line_1="P.O. Box 838",
        address_line_2="",
        city="Lawrence",
        state="MA",
        zip_code="01842",  # Pass the zip code in as a string since it starts with a zero.
        country="US",
        account_number=int(os.environ.get("DFML_PUB_ACCOUNT_NUMBER")),  # type: ignore
        routing_number=int(os.environ.get("DFML_PUB_ROUTING_NUMBER")),  # type: ignore
    )
