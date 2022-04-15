import os
from datetime import date
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import and_, case, cast, func, or_
from sqlalchemy.sql import literal_column
from sqlalchemy.sql.sqltypes import Date

import massgov.pfml.api.app as app
import massgov.pfml.db as db
import massgov.pfml.util.logging as logging
from massgov.pfml.db.models.employees import (
    Address,
    Claim,
    Employee,
    ExperianAddressPair,
    LkGeoState,
    LkPaymentTransactionType,
    Payment,
    PaymentTransactionType,
    State,
    StateLog,
    TaxIdentifier,
)
from massgov.pfml.db.models.payments import (
    FineosExtractEmployeeFeed,
    FineosExtractVpei,
    MmarsPaymentData,
    Pfml1099,
    Pfml1099Batch,
    Pfml1099MMARSPayment,
    Pfml1099Payment,
    Pfml1099Refund,
    Pfml1099Request,
    Pfml1099Withholding,
    WithholdingType,
)
from massgov.pfml.util.datetime import get_now_us_eastern


class Constants:
    CREATED_STATUS = "Created"
    GENERATED_STATUS = "Generated"
    MERGED_STATUS = "Merged"
    COMPLETED_STATUS = "Printed and Mailed"
    REPLACED_STATUS = "Replacement Batch Created: "
    ARCHIVED_STATUS = "Archived: "
    ERRORED_STATUS = "Invalid: "

    FEDERAL_WITHHOLDING_TYPE = "FEDERAL"
    STATE_WITHHOLDING_TYPE = "STATE"


class Corrected1099Data:
    employee_id: str
    latest_pfml_1099_id: str
    pfml_1099_id: str
    latest_pfml_batch_id: str
    pfml_1099_batch_id: str

    def __init__(
        self,
        employee_id: str,
        latest_pfml_1099_id: str,
        pfml_1099_id: str,
        latest_pfml_batch_id: str,
        pfml_1099_batch_id: str,
    ):
        self.employee_id = employee_id
        self.latest_pfml_1099_id = latest_pfml_1099_id
        self.pfml_1099_id = pfml_1099_id
        self.latest_pfml_batch_id = latest_pfml_batch_id
        self.pfml_1099_batch_id = pfml_1099_batch_id

    def get_traceable_details(self) -> Dict[str, Optional[Any]]:

        return {
            "employee_id": self.employee_id,
            "latest_pfml_1099_id": self.latest_pfml_1099_id,
            "pfml_1099_id": self.pfml_1099_id,
            "latest_pfml_batch_id": self.latest_pfml_batch_id,
            "pfml_1099_batch_id": self.pfml_1099_batch_id,
        }


ACTIVE_STATES = [Constants.CREATED_STATUS, Constants.GENERATED_STATUS, Constants.MERGED_STATUS]

END_STATES = [
    Constants.COMPLETED_STATUS,
    Constants.REPLACED_STATUS,
    Constants.ARCHIVED_STATUS,
    Constants.ERRORED_STATUS,
]

OVERPAYMENT_TYPES_1099 = frozenset(
    [
        PaymentTransactionType.OVERPAYMENT_ACTUAL_RECOVERY,
        PaymentTransactionType.OVERPAYMENT_RECOVERY,
        PaymentTransactionType.OVERPAYMENT_RECOVERY_CANCELLATION,
        PaymentTransactionType.OVERPAYMENT_RECOVERY_REVERSE,
    ]
)
OVERPAYMENT_TYPES_1099_IDS = frozenset(
    [overpayment_type.payment_transaction_type_id for overpayment_type in OVERPAYMENT_TYPES_1099]
)


logger = logging.get_logger(__package__)


def is_generate_1099_pdf_enabled() -> bool:
    return app.get_config().enable_generate_1099_pdf


def is_merge_1099_pdf_enabled() -> bool:
    return app.get_config().enable_merge_1099_pdf


def is_upload_1099_pdf_enabled() -> bool:
    return app.get_config().enable_upload_1099_pdf


def get_pdf_api_generate_endpoint() -> str:
    return f"{__get_pdf_api_endpoint()}/api/pdf/generate"


def get_pdf_api_merge_endpoint() -> str:
    return f"{__get_pdf_api_endpoint()}/api/pdf/merge"


def get_pdf_api_update_template_endpoint() -> str:
    return f"{__get_pdf_api_endpoint()}/api/pdf/updateTemplate"


def __get_pdf_api_endpoint() -> Optional[str]:
    if os.environ.get("PDF_API_HOST") is None:
        raise Exception("Env var 'PDF_API_HOST' has not being defined.")

    return os.environ.get("PDF_API_HOST")


def get_payments(db_session: db.Session, batch: Pfml1099Batch) -> List[Any]:

    year = get_tax_year()

    is_none = None

    payments = []
    if batch.correction_ind:
        # Get all the  payment data for a reprint/correction run
        # Get the list of 1099 requests that remain open
        requests = get_1099_requests(db_session)

        # For each request, copy or requery for payments
        for request in requests:
            if request.correction_ind:
                # Query for updated Payment data for the employee
                check_payments = (
                    db_session.query(
                        StateLog.payment_id, cast(StateLog.ended_at, Date).label("ended_at")
                    )
                    .filter(
                        StateLog.end_state_id
                        == State.DELEGATED_PAYMENT_PUB_TRANSACTION_CHECK_SENT.state_id
                    )
                    .subquery()
                )
                eft_payments = (
                    db_session.query(
                        StateLog.payment_id, cast(StateLog.ended_at, Date).label("ended_at")
                    )
                    .filter(
                        StateLog.end_state_id
                        == State.DELEGATED_PAYMENT_PUB_TRANSACTION_EFT_SENT.state_id
                    )
                    .subquery()
                )
                bank_errors = (
                    db_session.query(
                        StateLog.payment_id, cast(StateLog.ended_at, Date).label("ended_at")
                    )
                    .filter(
                        StateLog.end_state_id == State.DELEGATED_PAYMENT_ERROR_FROM_BANK.state_id
                    )
                    .subquery()
                )

                pub_payments = (
                    db_session.query(
                        Payment.payment_id.label("payment_id"),
                        Payment.claim_id.label("claim_id"),
                        Employee.employee_id.label("employee_id"),
                        Payment.amount.label("payment_amount"),
                    )
                    .add_columns(
                        case(
                            [
                                (check_payments.c.payment_id != is_none, check_payments.c.ended_at),
                                (eft_payments.c.payment_id != is_none, eft_payments.c.ended_at),
                            ]
                        ).label("payment_date"),
                        case([(bank_errors.c.payment_id != is_none, bank_errors.c.ended_at)]).label(
                            "cancel_date"
                        ),
                    )
                    .join(Claim, Payment.claim_id == Claim.claim_id)
                    .join(Employee, Claim.employee_id == Employee.employee_id)
                    .outerjoin(check_payments, Payment.payment_id == check_payments.c.payment_id)
                    .outerjoin(eft_payments, Payment.payment_id == eft_payments.c.payment_id)
                    .outerjoin(bank_errors, Payment.payment_id == bank_errors.c.payment_id)
                    .join(Pfml1099Request, Employee.employee_id == Pfml1099Request.employee_id)
                    .filter(
                        Pfml1099Request.employee_id == request.employee_id,
                        Pfml1099Request.pfml_1099_batch_id == is_none,
                    )
                    .filter(
                        or_(
                            check_payments.c.payment_id != is_none,
                            eft_payments.c.payment_id != is_none,
                        )
                    )
                    .filter(
                        or_(
                            case(
                                [
                                    (
                                        check_payments.c.payment_id != is_none,
                                        func.date_part("YEAR", check_payments.c.ended_at),
                                    ),
                                    (
                                        eft_payments.c.payment_id != is_none,
                                        func.date_part("YEAR", eft_payments.c.ended_at),
                                    ),
                                ]
                            )
                            == year,
                            case(
                                [
                                    (
                                        bank_errors.c.payment_id != is_none,
                                        func.date_part("YEAR", bank_errors.c.ended_at),
                                    )
                                ]
                            )
                            == year,
                        )
                    )
                    .all()
                )

                payments.extend(pub_payments)
            else:
                # Copy the Payment data in the last batch for the employee
                last_batch = get_last_1099_batch_for_employee(db_session, request.employee_id)

                if last_batch is not None:
                    pub_payments = (
                        db_session.query(
                            Pfml1099Payment.payment_id.label("payment_id"),
                            Pfml1099Payment.claim_id.label("claim_id"),
                            Pfml1099Payment.employee_id.label("employee_id"),
                            Pfml1099Payment.payment_amount.label("payment_amount"),
                            Pfml1099Payment.payment_date.label("payment_date"),
                            Pfml1099Payment.cancel_date.label("cancel_date"),
                        )
                        .filter(
                            Pfml1099Payment.pfml_1099_batch_id == last_batch.pfml_1099_batch_id,
                            Pfml1099Payment.employee_id == request.employee_id,
                        )
                        .all()
                    )

                    payments.extend(pub_payments)
    else:
        # Get all payment data for the 1099 batch
        # WITH CHECK_PAYMENTS     AS (SELECT PAYMENT_ID, CAST(ENDED_AT AS DATE) FROM STATE_LOG WHERE END_STATE_ID = 137),
        #     EFT_PAYMENTS       AS (SELECT PAYMENT_ID, CAST(ENDED_AT AS DATE) FROM STATE_LOG WHERE END_STATE_ID = 139),
        #     BANK_ERRORS        AS (SELECT PAYMENT_ID, CAST(ENDED_AT AS DATE) FROM STATE_LOG WHERE END_STATE_ID = 182)
        # SELECT CURRENT_TIMESTAMP CREATED_AT,
        #     CURRENT_TIMESTAMP UPDATED_AT,
        #     GEN_RANDOM_UUID() PFML_1099_PAYMENT_ID,
        #     PFML_1099_BATCH_ID,
        #     E.EMPLOYEE_ID EMPLOYEE_ID,
        #     CL.CLAIM_ID CLAIM_ID,
        #     P.PAYMENT_ID PAYMENT_ID,
        #     P.AMOUNT PAYMENT_AMOUNT,
        #     CASE WHEN CP.PAYMENT_ID IS NOT NULL THEN CP.ENDED_AT
        #             WHEN EFT.PAYMENT_ID IS NOT NULL THEN EFT.ENDED_AT
        #             ELSE NULL END PAYMENT_DATE,
        #     CASE WHEN BE.PAYMENT_ID IS NOT NULL THEN BE.ENDED_AT
        #             ELSE NULL END CANCEL_DATE
        # FROM PAYMENT P
        # INNER JOIN CLAIM CL ON P.CLAIM_ID = CL.CLAIM_ID
        # INNER JOIN EMPLOYEE E ON CL.EMPLOYEE_ID = E.EMPLOYEE_ID
        # LEFT OUTER JOIN CHECK_PAYMENTS CP ON P.PAYMENT_ID = CP.PAYMENT_ID
        # LEFT OUTER JOIN EFT_PAYMENTS EFT ON P.PAYMENT_ID = EFT.PAYMENT_ID
        # LEFT OUTER JOIN BANK_ERRORS BE ON P.PAYMENT_ID = BE.PAYMENT_ID
        # WHERE (CP.PAYMENT_ID IS NOT NULL OR EFT.PAYMENT_ID IS NOT NULL)
        # AND (CASE WHEN CP.PAYMENT_ID  IS NOT NULL THEN DATE_PART('YEAR', CP.ENDED_AT)
        #             WHEN EFT.PAYMENT_ID IS NOT NULL THEN DATE_PART('YEAR', EFT.ENDED_AT) END = 2021
        #     OR
        #     CASE WHEN BE.PAYMENT_ID IS NOT NULL THEN DATE_PART('YEAR', BE.ENDED_AT)   END = 2021)
        check_payments = (
            db_session.query(StateLog.payment_id, cast(StateLog.ended_at, Date).label("ended_at"))
            .filter(
                StateLog.end_state_id == State.DELEGATED_PAYMENT_PUB_TRANSACTION_CHECK_SENT.state_id
            )
            .subquery()
        )
        eft_payments = (
            db_session.query(StateLog.payment_id, cast(StateLog.ended_at, Date).label("ended_at"))
            .filter(
                StateLog.end_state_id == State.DELEGATED_PAYMENT_PUB_TRANSACTION_EFT_SENT.state_id
            )
            .subquery()
        )
        bank_errors = (
            db_session.query(StateLog.payment_id, cast(StateLog.ended_at, Date).label("ended_at"))
            .filter(StateLog.end_state_id == State.DELEGATED_PAYMENT_ERROR_FROM_BANK.state_id)
            .subquery()
        )

        payments = (
            db_session.query(
                Payment.payment_id.label("payment_id"),
                Payment.claim_id.label("claim_id"),
                Employee.employee_id.label("employee_id"),
                Payment.amount.label("payment_amount"),
            )
            .add_columns(
                case(
                    [
                        (check_payments.c.payment_id != is_none, check_payments.c.ended_at),
                        (eft_payments.c.payment_id != is_none, eft_payments.c.ended_at),
                    ]
                ).label("payment_date"),
                case([(bank_errors.c.payment_id != is_none, bank_errors.c.ended_at)]).label(
                    "cancel_date"
                ),
            )
            .join(Claim, Payment.claim_id == Claim.claim_id)
            .join(Employee, Claim.employee_id == Employee.employee_id)
            .outerjoin(check_payments, Payment.payment_id == check_payments.c.payment_id)
            .outerjoin(eft_payments, Payment.payment_id == eft_payments.c.payment_id)
            .outerjoin(bank_errors, Payment.payment_id == bank_errors.c.payment_id)
            .filter(
                or_(check_payments.c.payment_id != is_none, eft_payments.c.payment_id != is_none)
            )
            .filter(
                or_(
                    case(
                        [
                            (
                                check_payments.c.payment_id != is_none,
                                func.date_part("YEAR", check_payments.c.ended_at),
                            ),
                            (
                                eft_payments.c.payment_id != is_none,
                                func.date_part("YEAR", eft_payments.c.ended_at),
                            ),
                        ]
                    )
                    == year,
                    case(
                        [
                            (
                                bank_errors.c.payment_id != is_none,
                                func.date_part("YEAR", bank_errors.c.ended_at),
                            )
                        ]
                    )
                    == year,
                )
            )
            .all()
        )

    logger.info("Number of Payments for %s: %s", year, len(payments))

    return payments


def get_mmars_payments(db_session: db.Session, batch: Pfml1099Batch) -> List[Any]:

    year = get_tax_year()

    is_none = None

    payments = []
    if batch.correction_ind:
        # Get all the MMARS payment data for a reprint/correction run
        # Get the list of 1099 requests that remain open
        requests = get_1099_requests(db_session)

        # For each request, copy or requery for MMARS payments
        for request in requests:
            if request.correction_ind:
                # Query for updated MMARS Payment data for the employee
                mmars_payments = (
                    db_session.query(
                        MmarsPaymentData.mmars_payment_data_id.label("mmars_payment_id"),
                        MmarsPaymentData.pymt_actg_line_amount.label("payment_amount"),
                        MmarsPaymentData.warrant_select_date.label("payment_date"),
                        Employee.employee_id.label("employee_id"),
                        MmarsPaymentData.vendor_customer_code,
                    )
                    .join(
                        Employee,
                        MmarsPaymentData.vendor_customer_code == Employee.ctr_vendor_customer_code,
                    )
                    .join(Pfml1099Request, Employee.employee_id == Pfml1099Request.employee_id)
                    .filter(
                        MmarsPaymentData.warrant_select_date >= date(year, 1, 1),
                        MmarsPaymentData.warrant_select_date < date(year + 1, 1, 1),
                        Pfml1099Request.employee_id == request.employee_id,
                        Pfml1099Request.pfml_1099_batch_id == is_none,
                    )
                    .all()
                )

                payments.extend(mmars_payments)
            else:
                # Copy the MMARS Payment data in the last batch for the employee
                last_batch = get_last_1099_batch_for_employee(db_session, request.employee_id)

                if last_batch is not None:
                    mmars_payments = (
                        db_session.query(
                            Pfml1099MMARSPayment.mmars_payment_id.label("mmars_payment_id"),
                            Pfml1099MMARSPayment.payment_amount.label("payment_amount"),
                            Pfml1099MMARSPayment.payment_date.label("payment_date"),
                            Pfml1099MMARSPayment.employee_id.label("employee_id"),
                        )
                        .filter(
                            Pfml1099MMARSPayment.pfml_1099_batch_id
                            == last_batch.pfml_1099_batch_id,
                            Pfml1099MMARSPayment.employee_id == request.employee_id,
                        )
                        .all()
                    )

                    payments.extend(mmars_payments)
    else:
        # Get all MMARS payment data for the 1099 batch
        # SELECT CURRENT_TIMESTAMP CREATED_AT,
        #        CURRENT_TIMESTAMP UPDATED_AT,
        #        GEN_RANDOM_UUID() PFML_1099_MMARS_PAYMENT_ID,
        #        PFML_1099_BATCH_ID,
        #        PYMT_DOC_IDENTIFIER MMARS_PAYMENT_ID,
        #        E.EMPLOYEE_ID EMPLOYEE_ID,
        #        PYMT_ACTG_LINE_AMOUNT PAYMENT_AMOUNT,
        #        CAST(WARRANT_SELECT_DATE AS DATE) PAYMENT_DATE
        # FROM MMARS_PAYMENT_DATA MPD
        # INNER JOIN EMPLOYEE E ON MPD.VENDOR_CUSTOMER_CODE = E.CTR_VENDOR_CUSTOMER_CODE
        # WHERE TO_CHAR(WARRANT_SELECT_DATE, 'YYYY') = '2021'
        payments = (
            db_session.query(
                MmarsPaymentData.mmars_payment_data_id.label("mmars_payment_id"),
                MmarsPaymentData.pymt_actg_line_amount.label("payment_amount"),
                MmarsPaymentData.warrant_select_date.label("payment_date"),
                Employee.employee_id.label("employee_id"),
                MmarsPaymentData.vendor_customer_code,
            )
            .join(
                Employee, MmarsPaymentData.vendor_customer_code == Employee.ctr_vendor_customer_code
            )
            .filter(
                MmarsPaymentData.warrant_select_date >= date(year, 1, 1),
                MmarsPaymentData.warrant_select_date < date(year + 1, 1, 1),
            )
            .all()
        )

    logger.info("Number of MMARS Payments for %s: %s", year, len(payments))

    return payments


def get_overpayments(db_session: db.Session, batch: Pfml1099Batch) -> List[Any]:

    year = get_tax_year()

    is_none = None

    refunds = []
    if batch.correction_ind:
        # Get all the overpayment repayment data for a reprint/correction run
        # Get the list of 1099 requests that remain open
        requests = get_1099_requests(db_session)

        # For each request, copy or requery for overpayment repayments
        for request in requests:
            if request.correction_ind:
                # Query for updated overpayment repayment data for the employee
                overpayments = (
                    db_session.query(
                        StateLog.payment_id, cast(StateLog.ended_at, Date).label("ended_at")
                    )
                    .filter(
                        StateLog.end_state_id
                        == State.DELEGATED_PAYMENT_PROCESSED_OVERPAYMENT.state_id
                    )
                    .subquery()
                )
                vpei = db_session.query(
                    FineosExtractVpei,
                    func.rank()
                    .over(
                        order_by=[FineosExtractVpei.fineos_extract_import_log_id.desc()],
                        partition_by=FineosExtractVpei.i,
                    )
                    .label("R"),
                ).subquery()

                overpayment_repayments = (
                    db_session.query(
                        overpayments,
                        Payment.payment_id.label("payment_id"),
                        Payment.amount.label("payment_amount"),
                        Employee.employee_id.label("employee_id"),
                        Payment.payment_date.label("payment_date"),
                    )
                    .join(Payment, overpayments.c.payment_id == Payment.payment_id)
                    .join(
                        vpei,
                        (Payment.fineos_pei_c_value == vpei.c.c)
                        & (Payment.fineos_pei_i_value == vpei.c.i),
                    )
                    .join(Employee, vpei.c.payeecustomer == Employee.fineos_customer_number)
                    .join(
                        LkPaymentTransactionType,
                        Payment.payment_transaction_type_id
                        == LkPaymentTransactionType.payment_transaction_type_id,
                    )
                    .join(Pfml1099Request, Employee.employee_id == Pfml1099Request.employee_id)
                    .filter(
                        Pfml1099Request.employee_id == request.employee_id,
                        Pfml1099Request.pfml_1099_batch_id == is_none,
                    )
                    .filter(
                        Payment.payment_transaction_type_id.in_(OVERPAYMENT_TYPES_1099_IDS),
                        func.extract("YEAR", overpayments.c.ended_at) == year,
                        vpei.c.paymentmethod.notin_(
                            ["Inflight Recovery", "Automatic Offset Recovery"]
                        ),
                        vpei.c.R == 1,
                    )
                    .all()
                )

                refunds.extend(overpayment_repayments)
            else:
                # Copy the overpayment repayment data in the last batch for the employee
                last_batch = get_last_1099_batch_for_employee(db_session, request.employee_id)

                if last_batch is not None:
                    overpayment_repayments = (
                        db_session.query(
                            Pfml1099Refund.payment_id.label("payment_id"),
                            Pfml1099Refund.refund_amount.label("payment_amount"),
                            Pfml1099Refund.employee_id.label("employee_id"),
                            Pfml1099Refund.refund_date.label("payment_date"),
                        )
                        .filter(
                            Pfml1099Refund.pfml_1099_batch_id == last_batch.pfml_1099_batch_id,
                            Pfml1099Refund.employee_id == request.employee_id,
                        )
                        .all()
                    )

                    refunds.extend(overpayment_repayments)
    else:
        # Get all overpayment repayment data for the 1099 batch
        # WITH OVER_PAYMENTS      AS (SELECT PAYMENT_ID, CAST(ENDED_AT AS DATE) FROM STATE_LOG WHERE END_STATE_ID = 125),
        # VPEI               AS (SELECT RANK() OVER (PARTITION BY I ORDER BY FINEOS_EXTRACT_IMPORT_LOG_ID DESC) R, PEI.*
        # FROM FINEOS_EXTRACT_VPEI PEI)
        # SELECT CURRENT_TIMESTAMP CREATED_AT,
        #       CURRENT_TIMESTAMP UPDATED_AT,
        #       GEN_RANDOM_UUID() PFML_1099_REFUND_ID,
        #       XXX PFML_1099_BATCH_ID,
        #       E.EMPLOYEE_ID EMPLOYEE_ID,
        #       NULL CLAIM_ID,
        #       P.PAYMENT_ID PAYMENT_ID,
        #       P.AMOUNT REFUND_AMOUNT
        # FROM OVER_PAYMENTS OP
        # INNER JOIN PAYMENT P ON OP.PAYMENT_ID = P.PAYMENT_ID
        # INNER JOIN VPEI ON P.FINEOS_PEI_C_VALUE = VPEI.C
        # AND P.FINEOS_PEI_I_VALUE = VPEI.I
        # INNER JOIN EMPLOYEE E ON VPEI.PAYEECUSTOMER = E.FINEOS_CUSTOMER_NUMBER
        # INNER JOIN LK_PAYMENT_TRANSACTION_TYPE PTT ON P.PAYMENT_TRANSACTION_TYPE_ID = PTT.PAYMENT_TRANSACTION_TYPE_ID
        # WHERE PTT.PAYMENT_TRANSACTION_TYPE_DESCRIPTION IN ('Overpayment Actual Recovery',
        #                                                   'Overpayment Recovery',
        #                                                   'Overpayment Recovery Reverse',
        #                                                   'Overpayment Recovery Cancellation')
        # AND DATE_PART('YEAR', OP.ENDED_AT) = 2021
        # AND VPEI.PAYMENTMETHOD NOT IN ('Inflight Recovery', 'Automatic Offset Recovery')
        # AND VPEI.R = 1
        overpayments = (
            db_session.query(StateLog.payment_id, cast(StateLog.ended_at, Date).label("ended_at"))
            .filter(StateLog.end_state_id == State.DELEGATED_PAYMENT_PROCESSED_OVERPAYMENT.state_id)
            .subquery()
        )
        vpei = db_session.query(
            FineosExtractVpei,
            func.rank()
            .over(
                order_by=[FineosExtractVpei.fineos_extract_import_log_id.desc()],
                partition_by=FineosExtractVpei.i,
            )
            .label("R"),
        ).subquery()

        refunds = (
            db_session.query(
                overpayments,
                Payment.payment_id.label("payment_id"),
                Payment.amount.label("payment_amount"),
                Employee.employee_id.label("employee_id"),
                Payment.payment_date.label("payment_date"),
            )
            .join(Payment, overpayments.c.payment_id == Payment.payment_id)
            .join(
                vpei,
                (Payment.fineos_pei_c_value == vpei.c.c) & (Payment.fineos_pei_i_value == vpei.c.i),
            )
            .join(Employee, vpei.c.payeecustomer == Employee.fineos_customer_number)
            .join(
                LkPaymentTransactionType,
                Payment.payment_transaction_type_id
                == LkPaymentTransactionType.payment_transaction_type_id,
            )
            .filter(
                Payment.payment_transaction_type_id.in_(OVERPAYMENT_TYPES_1099_IDS),
                func.extract("YEAR", overpayments.c.ended_at) == year,
                vpei.c.paymentmethod.notin_(["Inflight Recovery", "Automatic Offset Recovery"]),
                vpei.c.R == 1,
            )
            .all()
        )

    logger.info("Number of Overpayments for %s: %s", year, len(refunds))

    return refunds


def get_1099s(db_session: db.Session, batch: Pfml1099Batch) -> List[Any]:

    year = get_tax_year()

    is_none = None

    irs_1099s = []
    if batch.correction_ind:
        # Get all 1099 data for a reprint/correction run
        # Get a list of 1099 requests that remain open
        requests = get_1099_requests(db_session)

        # For each request, copy or requery for 1099 data
        for request in requests:
            if request.correction_ind:
                # Query for updated 1099 data for the employee
                employees = (
                    db_session.query(
                        Employee.employee_id.label("employee_id"),
                        Employee.tax_identifier_id.label("tax_identifier_id"),
                        FineosExtractEmployeeFeed.c.label("c"),
                        FineosExtractEmployeeFeed.i.label("i"),
                        FineosExtractEmployeeFeed.firstnames.label("first_name"),
                        FineosExtractEmployeeFeed.lastname.label("last_name"),
                        FineosExtractEmployeeFeed.customerno.label("customerno"),
                        FineosExtractEmployeeFeed.address1.label("address1"),
                        FineosExtractEmployeeFeed.address2.label("address2"),
                        FineosExtractEmployeeFeed.address4.label("address4"),
                        FineosExtractEmployeeFeed.address6.label("address6"),
                        FineosExtractEmployeeFeed.postcode.label("postcode"),
                        cast(
                            case(
                                [
                                    (
                                        FineosExtractEmployeeFeed.effectivefrom == is_none,
                                        "1900-01-01",
                                    ),
                                    (FineosExtractEmployeeFeed.effectivefrom == "", "1900-01-01"),
                                ],
                                else_=FineosExtractEmployeeFeed.effectivefrom,
                            ),
                            Date,
                        ).label("ADDRESS_DATE"),
                        func.rank()
                        .over(
                            order_by=[
                                FineosExtractEmployeeFeed.fineos_extract_import_log_id.desc(),
                                FineosExtractEmployeeFeed.effectivefrom.desc(),
                                FineosExtractEmployeeFeed.effectiveto.desc(),
                                FineosExtractEmployeeFeed.created_at.desc(),
                            ],
                            partition_by=FineosExtractEmployeeFeed.customerno,
                        )
                        .label("R"),
                    )
                    .join(
                        Employee,
                        FineosExtractEmployeeFeed.customerno == Employee.fineos_customer_number,
                    )
                    .join(Pfml1099Request, Employee.employee_id == Pfml1099Request.employee_id)
                    .filter(
                        Employee.employee_id == request.employee_id,
                        Pfml1099Request.pfml_1099_batch_id == is_none,
                    )
                    .subquery()
                )

                payments = (
                    db_session.query(
                        Pfml1099Payment.employee_id,
                        func.sum(Pfml1099Payment.payment_amount).label("GROSS_PAYMENTS"),
                    )
                    .filter(
                        Pfml1099Payment.pfml_1099_batch_id == batch.pfml_1099_batch_id,
                        func.extract("YEAR", Pfml1099Payment.payment_date) == year,
                        func.extract(
                            "YEAR", func.coalesce(Pfml1099Payment.cancel_date, "01-01-1999")
                        )
                        != year,
                    )
                    .group_by(Pfml1099Payment.employee_id)
                    .subquery()
                )

                credits = (
                    db_session.query(
                        Pfml1099Payment.employee_id,
                        func.sum(Pfml1099Payment.payment_amount).label("OTHER_CREDITS"),
                    )
                    .filter(
                        Pfml1099Payment.pfml_1099_batch_id == batch.pfml_1099_batch_id,
                        func.extract("YEAR", Pfml1099Payment.payment_date) != year,
                        func.extract(
                            "YEAR", func.coalesce(Pfml1099Payment.cancel_date, "01-01-1999")
                        )
                        == year,
                    )
                    .group_by(Pfml1099Payment.employee_id)
                    .subquery()
                )

                mmars_payments = (
                    db_session.query(
                        Pfml1099MMARSPayment.employee_id,
                        func.sum(Pfml1099MMARSPayment.payment_amount).label("GROSS_PAYMENTS"),
                    )
                    .filter(Pfml1099MMARSPayment.pfml_1099_batch_id == batch.pfml_1099_batch_id)
                    .group_by(Pfml1099MMARSPayment.employee_id)
                    .subquery()
                )

                overpayments = (
                    db_session.query(
                        Pfml1099Refund.employee_id,
                        func.sum(Pfml1099Refund.refund_amount).label("OVERPAYMENT_REPAYMENTS"),
                    )
                    .filter(Pfml1099Refund.pfml_1099_batch_id == batch.pfml_1099_batch_id)
                    .group_by(Pfml1099Refund.employee_id)
                    .subquery()
                )

                taxes = (
                    db_session.query(
                        Pfml1099Withholding.employee_id,
                        func.sum(
                            case(
                                [
                                    (
                                        Pfml1099Withholding.withholding_type
                                        == WithholdingType.STATE,
                                        Pfml1099Withholding.withholding_amount,
                                    )
                                ],
                                else_=0,
                            )
                        ).label("STATE_TAX_WITHHOLDINGS"),
                        func.sum(
                            case(
                                [
                                    (
                                        Pfml1099Withholding.withholding_type
                                        == WithholdingType.FEDERAL,
                                        Pfml1099Withholding.withholding_amount,
                                    )
                                ],
                                else_=0,
                            )
                        ).label("FEDERAL_TAX_WITHHOLDINGS"),
                    )
                    .filter(Pfml1099Withholding.pfml_1099_batch_id == batch.pfml_1099_batch_id)
                    .group_by(Pfml1099Withholding.employee_id)
                    .subquery()
                )

                mmars_addresses = (
                    db_session.query(
                        Pfml1099MMARSPayment.employee_id,
                        cast(MmarsPaymentData.scheduled_payment_date, Date).label("PAYMENT_DATE"),
                        MmarsPaymentData.address_line_1,
                        MmarsPaymentData.address_line_2,
                        MmarsPaymentData.city,
                        MmarsPaymentData.state,
                        MmarsPaymentData.zip_code,
                        func.rank()
                        .over(
                            order_by=[
                                MmarsPaymentData.scheduled_payment_date.desc(),
                                MmarsPaymentData.created_at.desc(),
                                MmarsPaymentData.mmars_payment_data_id.desc(),
                            ],
                            partition_by=Pfml1099MMARSPayment.employee_id,
                        )
                        .label("R"),
                    )
                    .join(
                        Pfml1099MMARSPayment,
                        MmarsPaymentData.mmars_payment_data_id
                        == Pfml1099MMARSPayment.mmars_payment_id,
                    )
                    .filter(Pfml1099MMARSPayment.pfml_1099_batch_id == batch.pfml_1099_batch_id)
                    .subquery()
                )

                pub_addresses = (
                    db_session.query(
                        Pfml1099Payment.employee_id,
                        Payment.payment_date.label("PAYMENT_DATE"),
                        Address.address_line_one,
                        Address.address_line_two,
                        Address.city,
                        LkGeoState.geo_state_description.label("state"),
                        Address.zip_code,
                        func.rank()
                        .over(
                            order_by=[
                                Pfml1099Payment.payment_date.desc(),
                                Payment.fineos_extract_import_log_id.desc(),
                                Payment.payment_id.desc(),
                            ],
                            partition_by=Pfml1099Payment.employee_id,
                        )
                        .label("R"),
                    )
                    .join(Payment, Pfml1099Payment.payment_id == Payment.payment_id)
                    .join(
                        ExperianAddressPair,
                        Payment.experian_address_pair_id == ExperianAddressPair.fineos_address_id,
                    )
                    .join(
                        Address,
                        Address.address_id
                        == case(
                            [
                                (
                                    ExperianAddressPair.experian_address_id != is_none,
                                    ExperianAddressPair.experian_address_id,
                                )
                            ],
                            else_=ExperianAddressPair.fineos_address_id,
                        ),
                    )
                    .join(LkGeoState, Address.geo_state_id == LkGeoState.geo_state_id)
                    .filter(Pfml1099Payment.pfml_1099_batch_id == batch.pfml_1099_batch_id)
                    .subquery()
                )

                employee_1099 = (
                    db_session.query(
                        employees.c.employee_id,
                        employees.c.tax_identifier_id,
                        employees.c.c,
                        employees.c.i,
                        employees.c.first_name,
                        employees.c.last_name,
                        employees.c.customerno,
                        employees.c.ADDRESS_DATE,
                        employees.c.R,
                        payments.c.GROSS_PAYMENTS.label("GROSS_PAYMENTS"),
                        mmars_payments.c.GROSS_PAYMENTS.label("GROSS_MMARS_PAYMENTS"),
                        taxes.c.STATE_TAX_WITHHOLDINGS,
                        taxes.c.FEDERAL_TAX_WITHHOLDINGS,
                        overpayments.c.OVERPAYMENT_REPAYMENTS,
                        credits.c.OTHER_CREDITS,
                        literal_column("TRUE").label("CORRECTION_IND"),
                        mmars_addresses.c.PAYMENT_DATE.label("MMARS_ADDRESS_DATE"),
                        pub_addresses.c.PAYMENT_DATE.label("PUB_ADDRESS_DATE"),
                        case(
                            [
                                (
                                    employees.c.ADDRESS_DATE
                                    == func.greatest(
                                        employees.c.ADDRESS_DATE,
                                        mmars_addresses.c.PAYMENT_DATE,
                                        pub_addresses.c.PAYMENT_DATE,
                                    ),
                                    "Using Employee Feed Address",
                                ),
                                (
                                    mmars_addresses.c.PAYMENT_DATE
                                    == func.greatest(
                                        employees.c.ADDRESS_DATE,
                                        mmars_addresses.c.PAYMENT_DATE,
                                        pub_addresses.c.PAYMENT_DATE,
                                    ),
                                    "Using MMARS Payment Address",
                                ),
                                (
                                    pub_addresses.c.PAYMENT_DATE
                                    == func.greatest(
                                        employees.c.ADDRESS_DATE,
                                        mmars_addresses.c.PAYMENT_DATE,
                                        pub_addresses.c.PAYMENT_DATE,
                                    ),
                                    "Using PUB Payment Address",
                                ),
                            ]
                        ).label("ADDRESS_SOURCE"),
                        case(
                            [
                                (
                                    employees.c.ADDRESS_DATE
                                    == func.greatest(
                                        employees.c.ADDRESS_DATE,
                                        mmars_addresses.c.PAYMENT_DATE,
                                        pub_addresses.c.PAYMENT_DATE,
                                    ),
                                    employees.c.address1,
                                ),
                                (
                                    mmars_addresses.c.PAYMENT_DATE
                                    == func.greatest(
                                        employees.c.ADDRESS_DATE,
                                        mmars_addresses.c.PAYMENT_DATE,
                                        pub_addresses.c.PAYMENT_DATE,
                                    ),
                                    mmars_addresses.c.address_line_1,
                                ),
                                (
                                    pub_addresses.c.PAYMENT_DATE
                                    == func.greatest(
                                        employees.c.ADDRESS_DATE,
                                        mmars_addresses.c.PAYMENT_DATE,
                                        pub_addresses.c.PAYMENT_DATE,
                                    ),
                                    pub_addresses.c.address_line_one,
                                ),
                            ]
                        ).label("ADDRESS_LINE_1"),
                        case(
                            [
                                (
                                    employees.c.ADDRESS_DATE
                                    == func.greatest(
                                        employees.c.ADDRESS_DATE,
                                        mmars_addresses.c.PAYMENT_DATE,
                                        pub_addresses.c.PAYMENT_DATE,
                                    ),
                                    employees.c.address2,
                                ),
                                (
                                    mmars_addresses.c.PAYMENT_DATE
                                    == func.greatest(
                                        employees.c.ADDRESS_DATE,
                                        mmars_addresses.c.PAYMENT_DATE,
                                        pub_addresses.c.PAYMENT_DATE,
                                    ),
                                    mmars_addresses.c.address_line_2,
                                ),
                                (
                                    pub_addresses.c.PAYMENT_DATE
                                    == func.greatest(
                                        employees.c.ADDRESS_DATE,
                                        mmars_addresses.c.PAYMENT_DATE,
                                        pub_addresses.c.PAYMENT_DATE,
                                    ),
                                    pub_addresses.c.address_line_two,
                                ),
                            ]
                        ).label("ADDRESS_LINE_2"),
                        case(
                            [
                                (
                                    employees.c.ADDRESS_DATE
                                    == func.greatest(
                                        employees.c.ADDRESS_DATE,
                                        mmars_addresses.c.PAYMENT_DATE,
                                        pub_addresses.c.PAYMENT_DATE,
                                    ),
                                    employees.c.address4,
                                ),
                                (
                                    mmars_addresses.c.PAYMENT_DATE
                                    == func.greatest(
                                        employees.c.ADDRESS_DATE,
                                        mmars_addresses.c.PAYMENT_DATE,
                                        pub_addresses.c.PAYMENT_DATE,
                                    ),
                                    mmars_addresses.c.city,
                                ),
                                (
                                    pub_addresses.c.PAYMENT_DATE
                                    == func.greatest(
                                        employees.c.ADDRESS_DATE,
                                        mmars_addresses.c.PAYMENT_DATE,
                                        pub_addresses.c.PAYMENT_DATE,
                                    ),
                                    pub_addresses.c.city,
                                ),
                            ]
                        ).label("CITY"),
                        case(
                            [
                                (
                                    employees.c.ADDRESS_DATE
                                    == func.greatest(
                                        employees.c.ADDRESS_DATE,
                                        mmars_addresses.c.PAYMENT_DATE,
                                        pub_addresses.c.PAYMENT_DATE,
                                    ),
                                    employees.c.address6,
                                ),
                                (
                                    mmars_addresses.c.PAYMENT_DATE
                                    == func.greatest(
                                        employees.c.ADDRESS_DATE,
                                        mmars_addresses.c.PAYMENT_DATE,
                                        pub_addresses.c.PAYMENT_DATE,
                                    ),
                                    mmars_addresses.c.state,
                                ),
                                (
                                    pub_addresses.c.PAYMENT_DATE
                                    == func.greatest(
                                        employees.c.ADDRESS_DATE,
                                        mmars_addresses.c.PAYMENT_DATE,
                                        pub_addresses.c.PAYMENT_DATE,
                                    ),
                                    pub_addresses.c.state,
                                ),
                            ]
                        ).label("STATE"),
                        case(
                            [
                                (
                                    employees.c.ADDRESS_DATE
                                    == func.greatest(
                                        employees.c.ADDRESS_DATE,
                                        mmars_addresses.c.PAYMENT_DATE,
                                        pub_addresses.c.PAYMENT_DATE,
                                    ),
                                    employees.c.postcode,
                                ),
                                (
                                    mmars_addresses.c.PAYMENT_DATE
                                    == func.greatest(
                                        employees.c.ADDRESS_DATE,
                                        mmars_addresses.c.PAYMENT_DATE,
                                        pub_addresses.c.PAYMENT_DATE,
                                    ),
                                    mmars_addresses.c.zip_code,
                                ),
                                (
                                    pub_addresses.c.PAYMENT_DATE
                                    == func.greatest(
                                        employees.c.ADDRESS_DATE,
                                        mmars_addresses.c.PAYMENT_DATE,
                                        pub_addresses.c.PAYMENT_DATE,
                                    ),
                                    pub_addresses.c.zip_code,
                                ),
                            ]
                        ).label("ZIP_CODE"),
                    )
                    .join(Employee, employees.c.customerno == Employee.fineos_customer_number)
                    .join(Pfml1099Request, Employee.employee_id == Pfml1099Request.employee_id)
                    .outerjoin(payments, Employee.employee_id == payments.c.employee_id)
                    .outerjoin(credits, Employee.employee_id == credits.c.employee_id)
                    .outerjoin(mmars_payments, Employee.employee_id == mmars_payments.c.employee_id)
                    .outerjoin(overpayments, Employee.employee_id == overpayments.c.employee_id)
                    .outerjoin(taxes, Employee.employee_id == taxes.c.employee_id)
                    .outerjoin(
                        mmars_addresses,
                        (Employee.employee_id == mmars_addresses.c.employee_id)
                        & (mmars_addresses.c.R == 1),
                    )
                    .outerjoin(
                        pub_addresses,
                        (Employee.employee_id == pub_addresses.c.employee_id)
                        & (pub_addresses.c.R == 1),
                    )
                    .filter(
                        employees.c.R == 1,
                        Pfml1099Request.employee_id == request.employee_id,
                        Pfml1099Request.pfml_1099_batch_id == is_none,
                    )
                    .all()
                )

                irs_1099s.extend(employee_1099)
            else:
                # Copy the 1099 data in the last batch for the employee
                last_batch = get_last_1099_batch_for_employee(db_session, request.employee_id)

                if last_batch is not None:
                    employee_1099 = (
                        db_session.query(
                            Pfml1099.employee_id.label("employee_id"),
                            Pfml1099.tax_identifier_id.label("tax_identifier_id"),
                            Pfml1099.c.label("c"),
                            Pfml1099.i.label("i"),
                            Pfml1099.first_name.label("first_name"),
                            Pfml1099.last_name.label("last_name"),
                            Pfml1099.account_number.label("customerno"),
                            literal_column("0").label("GROSS_MMARS_PAYMENTS"),
                            Pfml1099.gross_payments.label("GROSS_PAYMENTS"),
                            Pfml1099.state_tax_withholdings.label("STATE_TAX_WITHHOLDINGS"),
                            Pfml1099.federal_tax_withholdings.label("FEDERAL_TAX_WITHHOLDINGS"),
                            Pfml1099.overpayment_repayments.label("OVERPAYMENT_REPAYMENTS"),
                            literal_column("0").label("OTHER_CREDITS"),
                            literal_column("FALSE").label("CORRECTION_IND"),
                            literal_column("'Using Pfml1099 Address'").label("ADDRESS_SOURCE"),
                            Pfml1099.address_line_1.label("ADDRESS_LINE_1"),
                            Pfml1099.address_line_2.label("ADDRESS_LINE_2"),
                            Pfml1099.city.label("CITY"),
                            Pfml1099.state.label("STATE"),
                            Pfml1099.zip.label("ZIP_CODE"),
                        )
                        .filter(
                            Pfml1099.pfml_1099_batch_id == last_batch.pfml_1099_batch_id,
                            Pfml1099.employee_id == request.employee_id,
                        )
                        .all()
                    )

                    irs_1099s.extend(employee_1099)

            # Mark the request as processed by setting the batch id
            request.pfml_1099_batch_id = batch.pfml_1099_batch_id
    else:
        # Get all 1099 data
        # WITH TXNS           AS (SELECT EMPLOYEE_ID FROM PFML_1099_PAYMENT WHERE PFML_BATCH_ID = ''
        #                         UNION ALL
        #                         SELECT EMPLOYEE_ID FROM PFML_1099_MMARS_PAYMENT WHERE PFML_BATCH_ID = ''
        #                         UNION ALL
        #                         SELECT EMPLOYEE_ID FROM PFML_1099_REFUND WHERE PFML_BATCH_ID = ''
        #                         UNION ALL
        #                         SELECT EMPLOYEE_ID FROM PFML_1099_WITHHOLDING WHERE PFML_BATCH_ID = ''),
        #     EMPLOYEE_FEED  AS (SELECT E.EMPLOYEE_ID, FEEF.FIRSTNAMES, FEEF.LASTNAME, FEEF.C, FEEF.I, FEEF.CUSTOMERNO, FEEF.ADDRESS1, FEEF.ADDRESS2, FEEF.ADDRESS4, FEEF.ADDRESS6, FEEF.POSTCODE, FEEF.COUNTRY,
        #                             FEEF.FINEOS_EXTRACT_IMPORT_LOG_ID, FEEF.EFFECTIVEFROM, FEEF.EFFECTIVETO, FEEF.CREATED_AT,
        #                             CAST (CASE WHEN FEEF.EFFECTIVEFROM IS NULL THEN '1900-01-01' WHEN FEEF.EFFECTIVEFROM = '' THEN '1900-01-01' ELSE FEEF.EFFECTIVEFROM END AS DATE) ADDRESS_DATE,
        #                             RANK() OVER (PARTITION BY FEEF.CUSTOMERNO ORDER BY FEEF.FINEOS_EXTRACT_IMPORT_LOG_ID DESC, FEEF.EFFECTIVEFROM DESC, FEEF.EFFECTIVETO DESC, FEEF.CREATED_AT DESC) R
        #                             FROM FINEOS_EXTRACT_EMPLOYEE_FEED FEEF
        #                             INNER JOIN EMPLOYEE E ON E.FINEOS_CUSTOMER_NUMBER = FEEF.CUSTOMERNO
        #                         WHERE E.EMPLOYEE_ID IN (SELECT EMPLOYEE_ID FROM TXNS)),
        #     PMT_TXNS       AS (SELECT EMPLOYEE_ID, SUM(PAYMENT_AMOUNT) GROSS_PAYMENTS
        #                         FROM PFML_1099_PAYMENT
        #                         WHERE PFML_BATCH_ID = ''
        #                         AND TO_CHAR(PAYMENT_DATE, 'YYYY') = '2021'
        #                         AND TO_CHAR(COALESCE(CANCEL_DATE, '01-01-1999'), 'YYYY') <> '2021'
        #                         GROUP BY EMPLOYEE_ID),
        #     CNL_TXNS       AS (SELECT EMPLOYEE_ID, SUM(PAYMENT_AMOUNT) OTHER_CREDITS
        #                         FROM PFML_1099_PAYMENT
        #                         WHERE PFML_BATCH_ID = ''
        #                         AND TO_CHAR(CANCEL_DATE, 'YYYY') = '2021'
        #                         AND TO_CHAR(PAYMENT_DATE, 'YYYY') <> '2021'
        #                         GROUP BY EMPLOYEE_ID),
        #     MMARS_PMT_TXNS AS (SELECT EMPLOYEE_ID, SUM(PAYMENT_AMOUNT) GROSS_PAYMENTS
        #                         FROM PFML_1099_MMARS_PAYMENT
        #                         WHERE PFML_BATCH_ID = ''
        #                         GROUP BY EMPLOYEE_ID),
        #     OP_RPMT_TXNS   AS (SELECT EMPLOYEE_ID, SUM(REFUND_AMOUNT) OVERPAYMENT_REPAYMENTS
        #                         FROM PFML_1099_REFUND
        #                         WHERE PFML_BATCH_ID = ''
        #                         GROUP BY EMPLOYEE_ID),
        #     TAX_TXNS       AS (SELECT EMPLOYEE_ID,
        #                             SUM(CASE WHEN WITHHOLDING_TYPE_ID = 2 THEN WITHHOLDING_AMOUNT ELSE 0 END) STATE_TAX_WITHHOLDINGS,
        #                             SUM(CASE WHEN WITHHOLDING_TYPE_ID = 1 THEN WITHHOLDING_AMOUNT ELSE 0 END) FEDERAL_TAX_WITHHOLDINGS
        #                         FROM PFML_1099_WITHHOLDING
        #                         WHERE PFML_BATCH_ID = ''
        #                         GROUP BY EMPLOYEE_ID),
        #     MMARS_PMT_ADD  AS (SELECT MP.EMPLOYEE_ID, CAST(MPD.SCHEDULED_PAYMENT_DATE AS DATE) PAYMENT_DATE, MPD.ADDRESS_LINE_1, MPD.ADDRESS_LINE_2, MPD.CITY,
        #                            MPD.STATE, MPD.ZIP_CODE,
        #                            RANK() OVER(PARTITION BY MP.EMPLOYEE_ID ORDER BY MPD.SCHEDULED_PAYMENT_DATE DESC, MPD.CREATED_AT DESC, MP.MMARS_PAYMENT_ID) R
        #                         FROM MMARS_PAYMENT_DATA MPD
        #                         INNER JOIN PFML_1099_MMARS_PAYMENT MP ON MPD.MMARS_PAYMENT_DATA_ID = MP.MMARS_PAYMENT_ID
        #                         WHERE MP.PFML_1099_BATCH_ID = ''),
        #     PUB_PMT_ADD    AS (SELECT PPD.EMPLOYEE_ID, P.PAYMENT_DATE, A.ADDRESS_LINE_ONE, A.ADDRESS_LINE_TWO, A.CITY, GS.GEO_STATE_DESCRIPTION STATE, A.ZIP_CODE,
        #                            RANK() OVER(PARTITION BY PPD.EMPLOYEE_ID ORDER BY P.PAYMENT_DATE DESC, P.FINEOS_EXTRACT_IMPORT_LOG_ID DESC, P.PAYMENT_ID) R
        #                         FROM PFML_1099_PAYMENT PPD
        #                         INNER JOIN PAYMENT P ON PPD.PAYMENT_ID = P.PAYMENT_ID
        #                         INNER JOIN LINK_EXPERIAN_ADDRESS_PAIR EAP ON P.EXPERIAN_ADDRESS_PAIR_ID = EAP.FINEOS_ADDRESS_ID
        #                         INNER JOIN ADDRESS A ON A.ADDRESS_ID =
        #                               CASE WHEN EAP.EXPERIAN_ADDRESS_ID IS NOT NULL
        #                               THEN EAP.EXPERIAN_ADDRESS_ID
        #                               ELSE EAP.FINEOS_ADDRESS_ID END
        #                         INNER JOIN LK_GEO_STATE GS ON A.GEO_STATE_ID = GS.GEO_STATE_ID
        #                         WHERE PPD.PFML_1099_BATCH_ID = '')
        # SELECT CURRENT_TIMESTAMP CREATED_AT,
        #     CURRENT_TIMESTAMP UPDATED_AT,
        #     GEN_RANDOM_UUID() PFML_1099_ID,
        #     PFML_1099_BATCH_ID,
        #     2021 TAX_YEAR,
        #     E.EMPLOYEE_ID EMPLOYEE_ID,
        #     TAX_IDENTIFIER_ID,
        #     EF.CUSTOMERNO,
        #     EF.FIRSTNAMES FIRST_NAME,
        #     EF.LASTNAME LAST_NAME,
        #     ADDRESS_DATE EMPLOYEE_FEED_ADDRESS_DATE,
        #     MPA.PAYMENT_DATE MMARS_ADDRESS_DATE,
        #     PPA.PAYMENT_DATE PUB_ADDRESS_DATE,
        #     CASE WHEN EF.ADDRESS_DATE = GREATEST(EF.ADDRESS_DATE, MPA.PAYMENT_DATE, PPA.PAYMENT_DATE) THEN 'Using Employee Feed Address'
        #         WHEN MPA.PAYMENT_DATE = GREATEST(EF.ADDRESS_DATE, MPA.PAYMENT_DATE, PPA.PAYMENT_DATE) THEN 'Using MMARS Payment Address'
        #         WHEN PPA.PAYMENT_DATE = GREATEST(EF.ADDRESS_DATE, MPA.PAYMENT_DATE, PPA.PAYMENT_DATE) THEN 'Using PUB Payment Address'
        #     END ADDRESS_SOURCE,
        #     CASE WHEN EF.ADDRESS_DATE = GREATEST(EF.ADDRESS_DATE, MPA.PAYMENT_DATE, PPA.PAYMENT_DATE) THEN EF.ADDRESS1
        #         WHEN MPA.PAYMENT_DATE = GREATEST(EF.ADDRESS_DATE, MPA.PAYMENT_DATE, PPA.PAYMENT_DATE) THEN MPA.ADDRESS_LINE_1
        #         WHEN PPA.PAYMENT_DATE = GREATEST(EF.ADDRESS_DATE, MPA.PAYMENT_DATE, PPA.PAYMENT_DATE) THEN PPA.ADDRESS_LINE_ONE
        #     END ADDRESS_LINE_1,
        #     CASE WHEN EF.ADDRESS_DATE = GREATEST(EF.ADDRESS_DATE, MPA.PAYMENT_DATE, PPA.PAYMENT_DATE) THEN EF.ADDRESS2
        #         WHEN MPA.PAYMENT_DATE = GREATEST(EF.ADDRESS_DATE, MPA.PAYMENT_DATE, PPA.PAYMENT_DATE) THEN MPA.ADDRESS_LINE_2
        #         WHEN PPA.PAYMENT_DATE = GREATEST(EF.ADDRESS_DATE, MPA.PAYMENT_DATE, PPA.PAYMENT_DATE) THEN PPA.ADDRESS_LINE_TWO
        #     END ADDRESS_LINE_2,
        #     CASE WHEN EF.ADDRESS_DATE = GREATEST(EF.ADDRESS_DATE, MPA.PAYMENT_DATE, PPA.PAYMENT_DATE) THEN EF.ADDRESS4
        #         WHEN MPA.PAYMENT_DATE = GREATEST(EF.ADDRESS_DATE, MPA.PAYMENT_DATE, PPA.PAYMENT_DATE) THEN MPA.CITY
        #         WHEN PPA.PAYMENT_DATE = GREATEST(EF.ADDRESS_DATE, MPA.PAYMENT_DATE, PPA.PAYMENT_DATE) THEN PPA.CITY
        #     END CITY,
        #     CASE WHEN EF.ADDRESS_DATE = GREATEST(EF.ADDRESS_DATE, MPA.PAYMENT_DATE, PPA.PAYMENT_DATE) THEN EF.ADDRESS6
        #         WHEN MPA.PAYMENT_DATE = GREATEST(EF.ADDRESS_DATE, MPA.PAYMENT_DATE, PPA.PAYMENT_DATE) THEN MPA.STATE
        #         WHEN PPA.PAYMENT_DATE = GREATEST(EF.ADDRESS_DATE, MPA.PAYMENT_DATE, PPA.PAYMENT_DATE) THEN PPA.STATE
        #     END STATE,
        #     CASE WHEN EF.ADDRESS_DATE = GREATEST(EF.ADDRESS_DATE, MPA.PAYMENT_DATE, PPA.PAYMENT_DATE) THEN EF.POSTCODE
        #         WHEN MPA.PAYMENT_DATE = GREATEST(EF.ADDRESS_DATE, MPA.PAYMENT_DATE, PPA.PAYMENT_DATE) THEN MPA.ZIP_CODE
        #         WHEN PPA.PAYMENT_DATE = GREATEST(EF.ADDRESS_DATE, MPA.PAYMENT_DATE, PPA.PAYMENT_DATE) THEN PPA.ZIP_CODE
        #     END ZIP_CODE,
        #     PT.GROSS_PAYMENTS + MPT.GROSS_PAYMENTS GROSS_PAYMENTS,
        #     TT.STATE_TAX_WITHHOLDINGS STATE_TAX_WITHHOLDINGS,
        #     TT.FEDERAL_TAX_WITHHOLDINGS FEDERAL_TAX_WITHHOLDINGS,
        #     OPT.OVERPAYMENT_REPAYMENTS OVERPAYMENT_REPAYMENTS,
        #     CT.OTHER_CREDITS OTHER_CREDITS,
        #     0 CORRECTION_ID
        # FROM EMPLOYEE_FEED EF
        # INNER JOIN EMPLOYEE E ON EF.CUSTOMERNO = E.FINEOS_CUSTOMER_NUMBER
        # LEFT OUTER JOIN PMT_TXNS PT ON E.EMPLOYEE_ID = PT.EMPLOYEE_ID
        # LEFT OUTER JOIN CNL_TXNS CT ON E.EMPLOYEE_ID = CT.EMPLOYEE_ID
        # LEFT OUTER JOIN MMARS_PMT_TXNS MPT ON E.EMPLOYEE_ID = MPT.EMPLOYEE_ID
        # LEFT OUTER JOIN OP_RPMT_TXNS OPT ON E.EMPLOYEE_ID = OPT.EMPLOYEE_ID
        # LEFT OUTER JOIN TAX_TXNS TT ON E.EMPLOYEE_ID = TT.EMPLOYEE_ID
        # LEFT OUTER JOIN MMARS_PMT_ADD MPA ON E.EMPLOYEE_ID = MPA.EMPLOYEE_ID
        #                                AND MPA.R = 1
        # LEFT OUTER JOIN PUB_PMT_ADD PPA ON E.EMPLOYEE_ID = PPA.EMPLOYEE_ID
        #                                AND PPA.R = 1
        # WHERE EF.R = 1
        payments_employees = db_session.query(
            Pfml1099Payment.employee_id.label("EMPLOYEE_ID")
        ).filter(Pfml1099Payment.pfml_1099_batch_id == batch.pfml_1099_batch_id)
        mmars_payments_employees = db_session.query(
            Pfml1099MMARSPayment.employee_id.label("EMPLOYEE_ID")
        ).filter(Pfml1099MMARSPayment.pfml_1099_batch_id == batch.pfml_1099_batch_id)
        refunds_employees = db_session.query(
            Pfml1099Refund.employee_id.label("EMPLOYEE_ID")
        ).filter(Pfml1099Refund.pfml_1099_batch_id == batch.pfml_1099_batch_id)
        withholdings_employees = db_session.query(
            Pfml1099Withholding.employee_id.label("EMPLOYEE_ID")
        ).filter(Pfml1099Withholding.pfml_1099_batch_id == batch.pfml_1099_batch_id)

        transactions = payments_employees.union_all(
            mmars_payments_employees, refunds_employees, withholdings_employees
        )

        employees = (
            db_session.query(
                Employee.employee_id.label("employee_id"),
                Employee.tax_identifier_id.label("tax_identifier_id"),
                FineosExtractEmployeeFeed.c.label("c"),
                FineosExtractEmployeeFeed.i.label("i"),
                FineosExtractEmployeeFeed.firstnames.label("first_name"),
                FineosExtractEmployeeFeed.lastname.label("last_name"),
                FineosExtractEmployeeFeed.customerno.label("customerno"),
                FineosExtractEmployeeFeed.address1.label("address1"),
                FineosExtractEmployeeFeed.address2.label("address2"),
                FineosExtractEmployeeFeed.address4.label("address4"),
                FineosExtractEmployeeFeed.address6.label("address6"),
                FineosExtractEmployeeFeed.postcode.label("postcode"),
                cast(
                    case(
                        [
                            (FineosExtractEmployeeFeed.effectivefrom == is_none, "1900-01-01"),
                            (FineosExtractEmployeeFeed.effectivefrom == "", "1900-01-01"),
                        ],
                        else_=FineosExtractEmployeeFeed.effectivefrom,
                    ),
                    Date,
                ).label("ADDRESS_DATE"),
                func.rank()
                .over(
                    order_by=[
                        FineosExtractEmployeeFeed.fineos_extract_import_log_id.desc(),
                        FineosExtractEmployeeFeed.effectivefrom.desc(),
                        FineosExtractEmployeeFeed.effectiveto.desc(),
                        FineosExtractEmployeeFeed.created_at.desc(),
                    ],
                    partition_by=FineosExtractEmployeeFeed.customerno,
                )
                .label("R"),
            )
            .join(Employee, FineosExtractEmployeeFeed.customerno == Employee.fineos_customer_number)
            .filter(Employee.employee_id.in_(transactions))
            .subquery()
        )

        payments = (
            db_session.query(
                Pfml1099Payment.employee_id,
                func.sum(Pfml1099Payment.payment_amount).label("GROSS_PAYMENTS"),
            )
            .filter(
                Pfml1099Payment.pfml_1099_batch_id == batch.pfml_1099_batch_id,
                func.extract("YEAR", Pfml1099Payment.payment_date) == year,
                func.extract("YEAR", func.coalesce(Pfml1099Payment.cancel_date, "01-01-1999"))
                != year,
            )
            .group_by(Pfml1099Payment.employee_id)
            .subquery()
        )

        credits = (
            db_session.query(
                Pfml1099Payment.employee_id,
                func.sum(Pfml1099Payment.payment_amount).label("OTHER_CREDITS"),
            )
            .filter(
                Pfml1099Payment.pfml_1099_batch_id == batch.pfml_1099_batch_id,
                func.extract("YEAR", Pfml1099Payment.payment_date) != year,
                func.extract("YEAR", func.coalesce(Pfml1099Payment.cancel_date, "01-01-1999"))
                == year,
            )
            .group_by(Pfml1099Payment.employee_id)
            .subquery()
        )

        mmars_payments = (
            db_session.query(
                Pfml1099MMARSPayment.employee_id,
                func.sum(Pfml1099MMARSPayment.payment_amount).label("GROSS_PAYMENTS"),
            )
            .filter(Pfml1099MMARSPayment.pfml_1099_batch_id == batch.pfml_1099_batch_id)
            .group_by(Pfml1099MMARSPayment.employee_id)
            .subquery()
        )

        overpayments = (
            db_session.query(
                Pfml1099Refund.employee_id,
                func.sum(Pfml1099Refund.refund_amount).label("OVERPAYMENT_REPAYMENTS"),
            )
            .filter(Pfml1099Refund.pfml_1099_batch_id == batch.pfml_1099_batch_id)
            .group_by(Pfml1099Refund.employee_id)
            .subquery()
        )

        taxes = (
            db_session.query(
                Pfml1099Withholding.employee_id,
                func.sum(
                    case(
                        [
                            (
                                Pfml1099Withholding.withholding_type == WithholdingType.STATE,
                                Pfml1099Withholding.withholding_amount,
                            )
                        ],
                        else_=0,
                    )
                ).label("STATE_TAX_WITHHOLDINGS"),
                func.sum(
                    case(
                        [
                            (
                                Pfml1099Withholding.withholding_type == WithholdingType.FEDERAL,
                                Pfml1099Withholding.withholding_amount,
                            )
                        ],
                        else_=0,
                    )
                ).label("FEDERAL_TAX_WITHHOLDINGS"),
            )
            .filter(Pfml1099Withholding.pfml_1099_batch_id == batch.pfml_1099_batch_id)
            .group_by(Pfml1099Withholding.employee_id)
            .subquery()
        )

        mmars_addresses = (
            db_session.query(
                Pfml1099MMARSPayment.employee_id,
                cast(MmarsPaymentData.scheduled_payment_date, Date).label("PAYMENT_DATE"),
                MmarsPaymentData.address_line_1,
                MmarsPaymentData.address_line_2,
                MmarsPaymentData.city,
                MmarsPaymentData.state,
                MmarsPaymentData.zip_code,
                func.rank()
                .over(
                    order_by=[
                        MmarsPaymentData.scheduled_payment_date.desc(),
                        MmarsPaymentData.created_at.desc(),
                        MmarsPaymentData.mmars_payment_data_id.desc(),
                    ],
                    partition_by=Pfml1099MMARSPayment.employee_id,
                )
                .label("R"),
            )
            .join(
                Pfml1099MMARSPayment,
                MmarsPaymentData.mmars_payment_data_id == Pfml1099MMARSPayment.mmars_payment_id,
            )
            .filter(Pfml1099MMARSPayment.pfml_1099_batch_id == batch.pfml_1099_batch_id)
            .subquery()
        )

        pub_addresses = (
            db_session.query(
                Pfml1099Payment.employee_id,
                Payment.payment_date.label("PAYMENT_DATE"),
                Address.address_line_one,
                Address.address_line_two,
                Address.city,
                LkGeoState.geo_state_description.label("state"),
                Address.zip_code,
                func.rank()
                .over(
                    order_by=[
                        Pfml1099Payment.payment_date.desc(),
                        Payment.fineos_extract_import_log_id.desc(),
                        Payment.payment_id.desc(),
                    ],
                    partition_by=Pfml1099Payment.employee_id,
                )
                .label("R"),
            )
            .join(Payment, Pfml1099Payment.payment_id == Payment.payment_id)
            .join(
                ExperianAddressPair,
                Payment.experian_address_pair_id == ExperianAddressPair.fineos_address_id,
            )
            .join(
                Address,
                Address.address_id
                == case(
                    [
                        (
                            ExperianAddressPair.experian_address_id != is_none,
                            ExperianAddressPair.experian_address_id,
                        )
                    ],
                    else_=ExperianAddressPair.fineos_address_id,
                ),
            )
            .join(LkGeoState, Address.geo_state_id == LkGeoState.geo_state_id)
            .filter(Pfml1099Payment.pfml_1099_batch_id == batch.pfml_1099_batch_id)
            .subquery()
        )

        irs_1099s = (
            db_session.query(
                employees.c.employee_id,
                employees.c.tax_identifier_id,
                employees.c.c,
                employees.c.i,
                employees.c.first_name,
                employees.c.last_name,
                employees.c.customerno,
                employees.c.ADDRESS_DATE,
                employees.c.R,
                payments.c.GROSS_PAYMENTS.label("GROSS_PAYMENTS"),
                mmars_payments.c.GROSS_PAYMENTS.label("GROSS_MMARS_PAYMENTS"),
                taxes.c.STATE_TAX_WITHHOLDINGS,
                taxes.c.FEDERAL_TAX_WITHHOLDINGS,
                overpayments.c.OVERPAYMENT_REPAYMENTS,
                credits.c.OTHER_CREDITS,
                literal_column("FALSE").label("CORRECTION_IND"),
                mmars_addresses.c.PAYMENT_DATE.label("MMARS_ADDRESS_DATE"),
                pub_addresses.c.PAYMENT_DATE.label("PUB_ADDRESS_DATE"),
                case(
                    [
                        (
                            employees.c.ADDRESS_DATE
                            == func.greatest(
                                employees.c.ADDRESS_DATE,
                                mmars_addresses.c.PAYMENT_DATE,
                                pub_addresses.c.PAYMENT_DATE,
                            ),
                            "Using Employee Feed Address",
                        ),
                        (
                            mmars_addresses.c.PAYMENT_DATE
                            == func.greatest(
                                employees.c.ADDRESS_DATE,
                                mmars_addresses.c.PAYMENT_DATE,
                                pub_addresses.c.PAYMENT_DATE,
                            ),
                            "Using MMARS Payment Address",
                        ),
                        (
                            pub_addresses.c.PAYMENT_DATE
                            == func.greatest(
                                employees.c.ADDRESS_DATE,
                                mmars_addresses.c.PAYMENT_DATE,
                                pub_addresses.c.PAYMENT_DATE,
                            ),
                            "Using PUB Payment Address",
                        ),
                    ]
                ).label("ADDRESS_SOURCE"),
                case(
                    [
                        (
                            employees.c.ADDRESS_DATE
                            == func.greatest(
                                employees.c.ADDRESS_DATE,
                                mmars_addresses.c.PAYMENT_DATE,
                                pub_addresses.c.PAYMENT_DATE,
                            ),
                            employees.c.address1,
                        ),
                        (
                            mmars_addresses.c.PAYMENT_DATE
                            == func.greatest(
                                employees.c.ADDRESS_DATE,
                                mmars_addresses.c.PAYMENT_DATE,
                                pub_addresses.c.PAYMENT_DATE,
                            ),
                            mmars_addresses.c.address_line_1,
                        ),
                        (
                            pub_addresses.c.PAYMENT_DATE
                            == func.greatest(
                                employees.c.ADDRESS_DATE,
                                mmars_addresses.c.PAYMENT_DATE,
                                pub_addresses.c.PAYMENT_DATE,
                            ),
                            pub_addresses.c.address_line_one,
                        ),
                    ]
                ).label("ADDRESS_LINE_1"),
                case(
                    [
                        (
                            employees.c.ADDRESS_DATE
                            == func.greatest(
                                employees.c.ADDRESS_DATE,
                                mmars_addresses.c.PAYMENT_DATE,
                                pub_addresses.c.PAYMENT_DATE,
                            ),
                            employees.c.address2,
                        ),
                        (
                            mmars_addresses.c.PAYMENT_DATE
                            == func.greatest(
                                employees.c.ADDRESS_DATE,
                                mmars_addresses.c.PAYMENT_DATE,
                                pub_addresses.c.PAYMENT_DATE,
                            ),
                            mmars_addresses.c.address_line_2,
                        ),
                        (
                            pub_addresses.c.PAYMENT_DATE
                            == func.greatest(
                                employees.c.ADDRESS_DATE,
                                mmars_addresses.c.PAYMENT_DATE,
                                pub_addresses.c.PAYMENT_DATE,
                            ),
                            pub_addresses.c.address_line_two,
                        ),
                    ]
                ).label("ADDRESS_LINE_2"),
                case(
                    [
                        (
                            employees.c.ADDRESS_DATE
                            == func.greatest(
                                employees.c.ADDRESS_DATE,
                                mmars_addresses.c.PAYMENT_DATE,
                                pub_addresses.c.PAYMENT_DATE,
                            ),
                            employees.c.address4,
                        ),
                        (
                            mmars_addresses.c.PAYMENT_DATE
                            == func.greatest(
                                employees.c.ADDRESS_DATE,
                                mmars_addresses.c.PAYMENT_DATE,
                                pub_addresses.c.PAYMENT_DATE,
                            ),
                            mmars_addresses.c.city,
                        ),
                        (
                            pub_addresses.c.PAYMENT_DATE
                            == func.greatest(
                                employees.c.ADDRESS_DATE,
                                mmars_addresses.c.PAYMENT_DATE,
                                pub_addresses.c.PAYMENT_DATE,
                            ),
                            pub_addresses.c.city,
                        ),
                    ]
                ).label("CITY"),
                case(
                    [
                        (
                            employees.c.ADDRESS_DATE
                            == func.greatest(
                                employees.c.ADDRESS_DATE,
                                mmars_addresses.c.PAYMENT_DATE,
                                pub_addresses.c.PAYMENT_DATE,
                            ),
                            employees.c.address6,
                        ),
                        (
                            mmars_addresses.c.PAYMENT_DATE
                            == func.greatest(
                                employees.c.ADDRESS_DATE,
                                mmars_addresses.c.PAYMENT_DATE,
                                pub_addresses.c.PAYMENT_DATE,
                            ),
                            mmars_addresses.c.state,
                        ),
                        (
                            pub_addresses.c.PAYMENT_DATE
                            == func.greatest(
                                employees.c.ADDRESS_DATE,
                                mmars_addresses.c.PAYMENT_DATE,
                                pub_addresses.c.PAYMENT_DATE,
                            ),
                            pub_addresses.c.state,
                        ),
                    ]
                ).label("STATE"),
                case(
                    [
                        (
                            employees.c.ADDRESS_DATE
                            == func.greatest(
                                employees.c.ADDRESS_DATE,
                                mmars_addresses.c.PAYMENT_DATE,
                                pub_addresses.c.PAYMENT_DATE,
                            ),
                            employees.c.postcode,
                        ),
                        (
                            mmars_addresses.c.PAYMENT_DATE
                            == func.greatest(
                                employees.c.ADDRESS_DATE,
                                mmars_addresses.c.PAYMENT_DATE,
                                pub_addresses.c.PAYMENT_DATE,
                            ),
                            mmars_addresses.c.zip_code,
                        ),
                        (
                            pub_addresses.c.PAYMENT_DATE
                            == func.greatest(
                                employees.c.ADDRESS_DATE,
                                mmars_addresses.c.PAYMENT_DATE,
                                pub_addresses.c.PAYMENT_DATE,
                            ),
                            pub_addresses.c.zip_code,
                        ),
                    ]
                ).label("ZIP_CODE"),
            )
            .join(Employee, employees.c.customerno == Employee.fineos_customer_number)
            .outerjoin(payments, Employee.employee_id == payments.c.employee_id)
            .outerjoin(credits, Employee.employee_id == credits.c.employee_id)
            .outerjoin(mmars_payments, Employee.employee_id == mmars_payments.c.employee_id)
            .outerjoin(overpayments, Employee.employee_id == overpayments.c.employee_id)
            .outerjoin(taxes, Employee.employee_id == taxes.c.employee_id)
            .outerjoin(
                mmars_addresses,
                (Employee.employee_id == mmars_addresses.c.employee_id)
                & (mmars_addresses.c.R == 1),
            )
            .outerjoin(
                pub_addresses,
                (Employee.employee_id == pub_addresses.c.employee_id) & (pub_addresses.c.R == 1),
            )
            .filter(employees.c.R == 1)
            .all()
        )

    return irs_1099s


def get_1099_requests(db_session: db.Session) -> List[Pfml1099Request]:

    is_none = None

    requests = (
        db_session.query(Pfml1099Request).filter(Pfml1099Request.pfml_1099_batch_id == is_none)
    ).all()

    logger.info("Number of 1099 Requests: %s", len(requests))

    return requests


def get_current_1099_batch(db_session: db.Session) -> Optional[Pfml1099Batch]:

    year = get_tax_year()

    batches = (
        db_session.query(Pfml1099Batch)
        .filter(Pfml1099Batch.tax_year == year)
        .order_by(Pfml1099Batch.batch_run_date.desc())
    ).all()

    if len(batches) == 0:
        logger.info("No current batch exists")
        return None

    logger.info("Found %s batches in %s", len(batches), year)

    for batch in batches:

        if batch.batch_status in ACTIVE_STATES:
            logger.info(
                "Found an existing batch in state=%s: %s",
                batch.batch_status,
                batch.pfml_1099_batch_id,
                extra={"batch": batch.pfml_1099_batch_id},
            )
            return batch

    return None


def get_last_1099_batch_for_employee(
    db_session: db.Session, employee_id: UUID
) -> Optional[Pfml1099Batch]:

    year = get_tax_year()

    batch = (
        db_session.query(Pfml1099Batch.pfml_1099_batch_id)
        .join(Pfml1099, Pfml1099Batch.pfml_1099_batch_id == Pfml1099.pfml_1099_batch_id)
        .filter(Pfml1099.employee_id == employee_id, Pfml1099Batch.tax_year == year)
        .order_by(Pfml1099Batch.batch_run_date.desc(), Pfml1099Batch.created_at.desc())
        .first()
    )

    if batch is None or len(batch) == 0:
        return None

    return batch


def get_tax_year() -> int:
    return int(os.environ.get("IRS_1099_TAX_YEAR", "0"))


def get_batch_counts(db_session: db.Session) -> Dict[int, int]:
    batches = (
        db_session.query(Pfml1099Batch.tax_year, func.count(Pfml1099Batch.pfml_1099_batch_id))
        .group_by(Pfml1099Batch.tax_year)
        .all()
    )

    batch_counts = {}
    for record in batches:
        year = record[0]
        count = record[1]
        logger.info(
            "Batch year %i has %i entries.", year, count, extra={"tax_year": year, "count": count}
        )
        batch_counts[year] = count

    return batch_counts


def get_payment_counts(db_session: db.Session) -> Dict[str, int]:
    payments = (
        db_session.query(
            Pfml1099Payment.pfml_1099_batch_id, func.count(Pfml1099Payment.pfml_1099_payment_id)
        )
        .group_by(Pfml1099Payment.pfml_1099_batch_id)
        .all()
    )

    payment_counts = {}
    for record in payments:
        batch = record[0]
        count = record[1]
        logger.info(
            "Batch %i has %i payments.", batch, count, extra={"batch": batch, "count": count}
        )
        payment_counts[batch] = count

    return payment_counts


def get_mmars_payment_counts(db_session: db.Session) -> Dict[str, int]:
    payments = (
        db_session.query(
            Pfml1099MMARSPayment.pfml_1099_batch_id,
            func.count(Pfml1099MMARSPayment.pfml_1099_mmars_payment_id),
        )
        .group_by(Pfml1099MMARSPayment.pfml_1099_batch_id)
        .all()
    )

    payment_counts = {}
    for record in payments:
        batch = record[0]
        count = record[1]
        logger.info(
            "Batch %i has %i MMARS payments.", batch, count, extra={"batch": batch, "count": count}
        )
        payment_counts[batch] = count

    return payment_counts


def get_1099_records_to_generate(db_session: db.Session, batchId: str) -> List[Pfml1099]:

    is_none = None

    records = (
        db_session.query(Pfml1099)
        .filter(Pfml1099.pfml_1099_batch_id == batchId, Pfml1099.s3_location == is_none)
        .all()
    )
    if records is not None:
        logger.info("Number of 1099 Records for batch [%s]: %s", batchId, len(records))

    return records


def get_1099_generated_count(db_session: db.Session, batchId: str) -> int:

    is_none = None

    records = (
        db_session.query(Pfml1099)
        .filter(Pfml1099.pfml_1099_batch_id == batchId, Pfml1099.s3_location != is_none)
        .all()
    )
    if records is not None:
        logger.info("Number of 1099 Records generated prior [%s]: %s", batchId, len(records))

    return len(records)


def get_tax_id(db_session: Any, tax_id_str: str) -> str:

    try:
        tax_id = db_session.query(TaxIdentifier).get(tax_id_str)
        if tax_id is not None:
            return tax_id.tax_identifier
        else:
            logger.error("There is no tax id for uuid %s", tax_id_str)
            return ""

    except Exception:
        logger.exception("Error accessing 1099 data")
        raise


def get_upload_max_files_to_fineos() -> int:
    return app.get_config().upload_max_files_to_fineos


def get_generate_1099_max_files() -> int:
    return app.get_config().generate_1099_max_files


def get_1099_record(db_session: db.Session, status: str, batch_id: str) -> Optional[Pfml1099]:
    """Get a 1099 record based on specific status and order by Created_at Asc"""
    return (
        db_session.query(Pfml1099)
        .order_by(Pfml1099.created_at.asc())
        .filter(Pfml1099.pfml_1099_batch_id == batch_id)
        .filter(Pfml1099.fineos_status == status)
        .first()
    )


def is_test_file() -> str:
    if app.get_config().enable_1099_testfile_generation:
        return "T"
    else:
        return ""


def is_correction_batch() -> bool:
    return os.environ.get("`IRS_1099_CORRECTION_IND`", "0") == "1"


def get_1099_records_to_file(db_session: db.Session) -> List[Pfml1099]:

    irs_1099_subquery = (
        db_session.query(
            Pfml1099,
            Pfml1099Batch.batch_run_date,
            func.rank()
            .over(
                order_by=[
                    Pfml1099Batch.batch_run_date.desc(),
                    Pfml1099.created_at.desc(),
                ],
                partition_by=Pfml1099.employee_id,
            )
            .label("R"),
        )
        .join(Pfml1099Batch, Pfml1099Batch.pfml_1099_batch_id == Pfml1099.pfml_1099_batch_id)
        .filter(Pfml1099Batch.tax_year == get_tax_year())
        .subquery()
    )
    irs_1099_records = list(db_session.query(irs_1099_subquery).filter(irs_1099_subquery.c.R == 1))
    logger.info(
        "Filtered records with latest batch run date for each employee is : %s",
        len(irs_1099_records),
    )
    return irs_1099_records


def update_submission_date(db_session: db.Session, tax_data: List[Pfml1099]) -> None:

    for rec in tax_data:

        db_session.query(Pfml1099).filter(
            Pfml1099.pfml_1099_batch_id == rec.pfml_1099_batch_id,
        ).update({Pfml1099.irs_submission_date: get_now_us_eastern()})


def is_correction_submission() -> bool:
    # return os.environ.get("IRS_1099_CORRECTION_SUB", "0") == "1"
    return os.environ.get("`IRS_1099_CORRECTION_IND`", "0") == "1"


def get_1099_corrected_records_to_file(db_session: db.Session) -> List[Corrected1099Data]:

    is_none = None
    is_True = True
    corrected_data_list = []
    latest_irs_submission = (
        db_session.query(
            Pfml1099,
            func.rank()
            .over(
                order_by=[
                    Pfml1099.created_at.desc(),
                ],
                partition_by=Pfml1099.employee_id,
            )
            .label("R"),
        )
        .filter(and_(Pfml1099.tax_year == get_tax_year(), Pfml1099.irs_submission_date != is_none))
        .subquery()
    )
    # logger.info("submission %s", latest_irs_submission)
    latest_irs_generation = (
        db_session.query(
            Pfml1099,
            func.rank()
            .over(
                order_by=[
                    Pfml1099.created_at.desc(),
                ],
                partition_by=Pfml1099.employee_id,
            )
            .label("R"),
        )
        .filter(and_(Pfml1099.tax_year == get_tax_year(), Pfml1099.correction_ind == is_True))
        .subquery()
    )
    # logger.info("latest_irs_generation %s", latest_irs_generation)
    correction_records = list(
        db_session.query(latest_irs_submission)
        .with_entities(
            latest_irs_generation.c.employee_id,
            latest_irs_generation.c.pfml_1099_id.label("latest_pfml_1099_id"),
            latest_irs_submission.c.pfml_1099_id,
            latest_irs_generation.c.pfml_1099_batch_id.label("latest_pfml_batch_id"),
            latest_irs_submission.c.pfml_1099_batch_id,
        )
        .join(
            latest_irs_generation,
            latest_irs_generation.c.employee_id == latest_irs_submission.c.employee_id,
        )
        .filter(
            and_(
                latest_irs_generation.c.created_at > latest_irs_submission.c.created_at,
                latest_irs_generation.c.R == 1,
                latest_irs_submission.c.R == 1,
            )
        )
    )
    if correction_records is not None:
        logger.info("Corrected query length %s", len(correction_records))
        record_iter = iter(correction_records)
        for record in record_iter:
            corrected_data = Corrected1099Data(
                record.employee_id,
                record.latest_pfml_1099_id,
                record.pfml_1099_id,
                record.latest_pfml_batch_id,
                record.pfml_batch_id,
            )
            corrected_data_list.append(corrected_data)
        logger.info("Number of corrected records %s", len(corrected_data_list))

    return correction_records


def get_old_new_1099_record(
    db_session: db.Session, submitted_pfml_1099_id: str, new_pfml_1099_id: str, employee_id: str
) -> List[Optional[Pfml1099]]:

    """Get the previously submitted 1099 record to IRS and the newly generated 1099 record"""
    pfmlRecords = []
    pfmlRecords.append(
        db_session.query(Pfml1099)
        .order_by(Pfml1099.created_at.asc())
        .filter(Pfml1099.pfml_1099_id == submitted_pfml_1099_id)
        .filter(Pfml1099.employee_id == employee_id)
        .first()
    )
    pfmlRecords.append(
        db_session.query(Pfml1099)
        .order_by(Pfml1099.created_at.asc())
        .filter(Pfml1099.pfml_1099_id == new_pfml_1099_id)
        .filter(Pfml1099.employee_id == employee_id)
        .first()
    )

    return pfmlRecords
