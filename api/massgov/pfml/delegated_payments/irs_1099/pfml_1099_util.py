import os
from datetime import date
from typing import Any, Dict, List, NamedTuple, Optional

from sqlalchemy import case, cast, func, or_
from sqlalchemy.sql.sqltypes import Date

import massgov.pfml.api.app as app
import massgov.pfml.db as db
import massgov.pfml.util.logging as logging
from massgov.pfml.db.models.employees import (
    Employee,
    LkPaymentTransactionType,
    Payment,
    PaymentTransactionType,
    State,
    StateLog,
    TaxIdentifier,
)
from massgov.pfml.db.models.payments import (
    FineosExtractEmployeeFeed,
    MmarsPaymentData,
    Pfml1099,
    Pfml1099Batch,
    Pfml1099MMARSPayment,
    Pfml1099Payment,
    Pfml1099Refund,
    Pfml1099Withholding,
    WithholdingType,
)


class Constants:
    CREATED_STATUS = "Created"
    GENERATED_STATUS = "Generated"
    MERGED_STATUS = "Merged"
    COMPLETED_STATUS = "Printed and Mailed"
    REPLACED_STATUS = "Replacement Batch Created: "
    ARCHIVED_STATUS = "Archived: "
    ERRORED_STATUS = "Invalid: "

    TAX_YEAR_CUTOFF = 6

    FEDERAL_WITHHOLDING_TYPE = "FEDERAL"
    STATE_WITHHOLDING_TYPE = "STATE"


ACTIVE_STATES = [
    Constants.CREATED_STATUS,
    Constants.GENERATED_STATUS,
    Constants.MERGED_STATUS,
]

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


def get_pdf_api_generate_endpoint() -> str:
    return f"{__get_pdf_api_endpoint()}/api/pdf/generate"


def get_pdf_api_merge_endpoint() -> str:
    return f"{__get_pdf_api_endpoint()}/api/pdf/merge"


def __get_pdf_api_endpoint() -> Optional[str]:
    if os.environ.get("PDF_API_HOST") is None:
        raise Exception("Env var 'PDF_API_HOST' has not being defined.")

    return os.environ.get("PDF_API_HOST")


def get_payments(db_session: db.Session) -> NamedTuple:

    year = get_tax_year()

    is_none = None

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
        .filter(StateLog.end_state_id == State.DELEGATED_PAYMENT_PUB_TRANSACTION_EFT_SENT.state_id)
        .subquery()
    )
    bank_errors = (
        db_session.query(StateLog.payment_id, cast(StateLog.ended_at, Date).label("ended_at"))
        .filter(StateLog.end_state_id == State.DELEGATED_PAYMENT_ERROR_FROM_BANK.state_id)
        .subquery()
    )

    payments = (
        db_session.query(Payment)
        .add_columns(
            case(
                [
                    (check_payments.c.payment_id != is_none, check_payments.c.ended_at),
                    (eft_payments.c.payment_id != is_none, eft_payments.c.ended_at),
                ]
            ).label("payment_date"),
            case([(bank_errors.c.payment_id != is_none, bank_errors.c.ended_at),]).label(
                "cancel_date"
            ),
        )
        .outerjoin(check_payments, Payment.payment_id == check_payments.c.payment_id)
        .outerjoin(eft_payments, Payment.payment_id == eft_payments.c.payment_id)
        .outerjoin(bank_errors, Payment.payment_id == bank_errors.c.payment_id)
        .filter(or_(check_payments.c.payment_id != is_none, eft_payments.c.payment_id != is_none))
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
                        ),
                    ]
                )
                == year,
            )
        )
        .all()
    )

    logger.info("Number of Payments for %s: %s", year, len(payments))

    return payments


def get_mmars_payments(db_session: db.Session) -> NamedTuple:

    year = get_tax_year()

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
        .join(Employee, MmarsPaymentData.vendor_customer_code == Employee.ctr_vendor_customer_code)
        .filter(
            MmarsPaymentData.warrant_select_date >= date(year, 1, 1),
            MmarsPaymentData.warrant_select_date < date(year + 1, 1, 1),
        )
        .all()
    )

    logger.info("Number of MMARS Payments for %s: %s", year, len(payments))

    return payments


def get_overpayments(db_session: db.Session) -> NamedTuple:

    year = get_tax_year()

    # SELECT CURRENT_TIMESTAMP CREATED_AT,
    #     CURRENT_TIMESTAMP UPDATED_AT,
    #     GEN_RANDOM_UUID() PFML_1099_REFUND_ID,
    #     PFML_1099_BATCH_ID,
    #     E.EMPLOYEE_ID EMPLOYEE_ID,
    #     P.PAYMENT_ID PAYMENT_ID,
    #     P.AMOUNT REFUND_AMOUNT
    #     P.PAYMENT_DATE
    # FROM PAYMENT P
    # INNER JOIN EMPLOYEE E ON E.EMPLOYEE_ID = P.EMPLOYEE_ID
    # INNER JOIN LK_PAYMENT_TRANSACTION_TYPE PTT ON P.PAYMENT_TRANSACTION_TYPE_ID = PTT.PAYMENT_TRANSACTION_TYPE_ID
    # WHERE PTT.PAYMENT_TRANSACTION_TYPE_DESCRIPTION IN (Overpayment Actual Recovery,
    #                                                 Overpayment Recovery,
    #                                                 Overpayment Recovery Reverse,
    #                                                 Overpayment Recovery Cancellation)
    overpayments = (
        db_session.query(
            Payment.payment_id.label("payment_id"),
            Payment.amount.label("payment_amount"),
            Employee.employee_id.label("employee_id"),
            Payment.payment_date.label("payment_date"),
            Payment.payment_transaction_type_id,
            Payment.employee_id,
        )
        .join(Employee, Payment.employee_id == Employee.employee_id)
        .join(
            LkPaymentTransactionType,
            Payment.payment_transaction_type_id
            == LkPaymentTransactionType.payment_transaction_type_id,
        )
        .filter(Payment.payment_transaction_type_id.in_(OVERPAYMENT_TYPES_1099_IDS))
        .all()
    )

    logger.info("Number of Overpayments for %s: %s", year, len(overpayments))

    return overpayments


def get_1099s(db_session: db.Session, batch: Pfml1099Batch) -> NamedTuple:

    year = get_tax_year()

    # WITH TXNS           AS (SELECT EMPLOYEE_ID FROM PFML_1099_PAYMENT WHERE PFML_BATCH_ID = ''
    #                         UNION ALL
    #                         SELECT EMPLOYEE_ID FROM PFML_1099_MMARS_PAYMENT WHERE PFML_BATCH_ID = ''
    #                         UNION ALL
    #                         SELECT EMPLOYEE_ID FROM PFML_1099_REFUND WHERE PFML_BATCH_ID = ''
    #                         SELECT EMPLOYEE_ID FROM PFML_1099_WITHHOLDING WHERE PFML_BATCH_ID = ''),
    #     EMPLOYEE_FEED  AS (SELECT E.EMPLOYEE_ID, FEEF.FIRSTNAMES, FEEF.LASTNAME, FEEF.C, FEEF.I, FEEF.CUSTOMERNO, FEEF.ADDRESS1, FEEF.ADDRESS2, FEEF.ADDRESS4, FEEF.ADDRESS6, FEEF.POSTCODE, FEEF.COUNTRY,
    #                             FEEF.FINEOS_EXTRACT_IMPORT_LOG_ID, FEEF.EFFECTIVEFROM, FEEF.EFFECTIVETO, FEEF.CREATED_AT,
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
    # SELECT CURRENT_TIMESTAMP CREATED_AT,
    #                         GROUP BY EMPLOYEE_ID)
    #     CURRENT_TIMESTAMP UPDATED_AT,
    #     GEN_RANDOM_UUID() PFML_1099_ID,
    #     PFML_1099_BATCH_ID,
    #     2021 TAX_YEAR,
    #     E.EMPLOYEE_ID EMPLOYEE_ID,
    #     TAX_IDENTIFIER_ID,
    #     EF.FIRSTNAMES FIRST_NAME,
    #     EF.LASTNAME LAST_NAME,
    #     EF.ADDRESS1 ADDRESS_LINE_1,
    #     EF.ADDRESS2 ADDRESS_LINE_2,
    #     EF.ADDRESS4 CITY,
    #     EF.ADDRESS6 STATE,
    #     EF.POSTCODE ZIP,
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
    # WHERE EF.R = 1
    payments_employees = db_session.query(Pfml1099Payment.employee_id.label("EMPLOYEE_ID")).filter(
        Pfml1099Payment.pfml_1099_batch_id == batch.pfml_1099_batch_id
    )
    mmars_payments_employees = db_session.query(
        Pfml1099MMARSPayment.employee_id.label("EMPLOYEE_ID")
    ).filter(Pfml1099MMARSPayment.pfml_1099_batch_id == batch.pfml_1099_batch_id)
    refunds_employees = db_session.query(Pfml1099Refund.employee_id.label("EMPLOYEE_ID")).filter(
        Pfml1099Refund.pfml_1099_batch_id == batch.pfml_1099_batch_id
    )
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
            func.extract("YEAR", func.coalesce(Pfml1099Payment.cancel_date, "01-01-1999")) != year,
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
            func.extract("YEAR", func.coalesce(Pfml1099Payment.cancel_date, "01-01-1999")) == year,
        )
        .group_by(Pfml1099Payment.employee_id)
        .subquery()
    )

    mmars_payments = (
        db_session.query(
            Pfml1099MMARSPayment.employee_id,
            func.sum(Pfml1099MMARSPayment.payment_amount).label("GROSS_PAYMENTS"),
        )
        .filter(Pfml1099MMARSPayment.pfml_1099_batch_id == batch.pfml_1099_batch_id,)
        .group_by(Pfml1099MMARSPayment.employee_id)
        .subquery()
    )

    overpayments = (
        db_session.query(
            Pfml1099Refund.employee_id,
            func.sum(Pfml1099Refund.refund_amount).label("OVERPAYMENT_REPAYMENTS"),
        )
        .filter(Pfml1099Refund.pfml_1099_batch_id == batch.pfml_1099_batch_id,)
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
        .filter(Pfml1099Withholding.pfml_1099_batch_id == batch.pfml_1099_batch_id,)
        .group_by(Pfml1099Withholding.employee_id)
        .subquery()
    )

    irs_1099s = (
        db_session.query(employees)
        .add_columns(
            payments.c.GROSS_PAYMENTS.label("GROSS_PAYMENTS"),
            mmars_payments.c.GROSS_PAYMENTS.label("GROSS_MMARS_PAYMENTS"),
            taxes.c.STATE_TAX_WITHHOLDINGS,
            taxes.c.FEDERAL_TAX_WITHHOLDINGS,
            overpayments.c.OVERPAYMENT_REPAYMENTS,
            credits.c.OTHER_CREDITS,
        )
        .join(Employee, employees.c.customerno == Employee.fineos_customer_number)
        .outerjoin(payments, Employee.employee_id == payments.c.employee_id)
        .outerjoin(credits, Employee.employee_id == credits.c.employee_id)
        .outerjoin(mmars_payments, Employee.employee_id == mmars_payments.c.employee_id)
        .outerjoin(overpayments, Employee.employee_id == overpayments.c.employee_id)
        .outerjoin(taxes, Employee.employee_id == taxes.c.employee_id)
        .filter(employees.c.R == 1)
        .all()
    )

    return irs_1099s


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


def get_tax_year() -> int:
    if date.today().month > Constants.TAX_YEAR_CUTOFF:
        return date.today().year
    else:
        return date.today().year - 1


def get_batch_counts(db_session: db.Session) -> Dict[int, int]:
    batches = (
        db_session.query(Pfml1099Batch.tax_year, func.count(Pfml1099Batch.pfml_1099_batch_id),)
        .group_by(Pfml1099Batch.tax_year)
        .all()
    )

    batch_counts = {}
    for record in batches:
        year = record[0]
        count = record[1]
        logger.info(
            "[%i][%i]: %i", year, count, extra={"tax_year": year, "count": count},
        )
        batch_counts[year] = count

    return batch_counts


def get_payment_counts(db_session: db.Session) -> Dict[str, int]:
    payments = (
        db_session.query(
            Pfml1099Payment.pfml_1099_batch_id, func.count(Pfml1099Payment.pfml_1099_payment_id),
        )
        .group_by(Pfml1099Payment.pfml_1099_batch_id)
        .all()
    )

    payment_counts = {}
    for record in payments:
        batch = record[0]
        count = record[1]
        logger.info(
            "[%i][%i]: %i", batch, count, extra={"batch": batch, "count": count},
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
            "[%i][%i]: %i", batch, count, extra={"batch": batch, "count": count},
        )
        payment_counts[batch] = count

    return payment_counts


def get_1099_records(db_session: db.Session, batchId: str) -> List[Pfml1099]:

    records = db_session.query(Pfml1099).filter(Pfml1099.pfml_1099_batch_id == batchId).all()
    records = records[:1000]
    if records is not None:
        logger.info(
            "Number of 1099 Records for batch [%s]: %s", batchId, len(records),
        )

    return records


def get_tax_id(db_session: Any, tax_id_str: str) -> str:
    logger.info("Incoming tax uuid is, %s", tax_id_str)
    tax_identifer=""
    #tax_id_str = 'c588edbd-c203-4dfb-a240-75c3d63e5846'
    try:
        tax_id = (
            db_session.query(TaxIdentifier)
            .filter(TaxIdentifier.tax_identifier_id == tax_id_str)
            .one_or_none()
        )
        if tax_id :
            logger.info("tax id is %s", tax_id.tax_identifier)
            tax_identifer = tax_id.tax_identifier
        else:
            logger.info("could not find tax id for the uuid %s",tax_id_str)
            
        return tax_identifer

    except Exception:
        logger.exception("Error accessing 1099 data")
        raise
    
def is_test_file() -> str:
    if os.environ.get("TEST_FILE_1099_ORG", "0") == "1":
        return "T"
    else:
        return ""

