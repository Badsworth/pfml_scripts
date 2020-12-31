from dataclasses import dataclass, field
from typing import Callable, Iterable, List, Tuple, Union

import massgov.pfml.api.util.state_log_util as state_log_util
import massgov.pfml.db as pfml_db
import massgov.pfml.payments.data_mart as data_mart
import massgov.pfml.payments.payments_util as payments_util
import massgov.pfml.util.datetime as datetime_util
import massgov.pfml.util.logging as logging
from massgov.pfml.db.models.employees import (
    Address,
    Claim,
    Country,
    Employee,
    GeoState,
    LatestStateLog,
    LkState,
    Payment,
    PaymentMethod,
    State,
    StateLog,
    TaxIdentifier,
)
from massgov.pfml.util import assert_never

logger = logging.get_logger(__name__)


@dataclass
class DataMartIssuesAndUpdates:
    issues: payments_util.ValidationContainer = field(
        default_factory=lambda: payments_util.ValidationContainer(
            "QueryDataMartForIssuesAndUpdates"
        )
    )
    employee_updates: bool = False
    vendor_exists: bool = False


def query_data_mart_for_issues_and_updates(
    data_mart_conn: data_mart.Connection, employee: Employee, tax_id: TaxIdentifier,
) -> DataMartIssuesAndUpdates:
    """Fetch Vendor information from MMARS Data Mart and compare it to existing Employee information.

    This will also update the Employee record with any information that MMARS is
    the authoritative source for.
    """
    result = DataMartIssuesAndUpdates()

    vendor_info = data_mart.get_vendor_info(data_mart_conn, tax_id.tax_identifier)

    if not vendor_info:
        return result

    result.vendor_exists = True

    if vendor_info.vendor_customer_code:
        # Could rely on SQLAlchemy to do the detection of if the value has
        # actually changed, but be explicit for clarity
        if employee.ctr_vendor_customer_code != vendor_info.vendor_customer_code:
            employee.ctr_vendor_customer_code = vendor_info.vendor_customer_code
            result.employee_updates = True
    else:
        result.issues.add_validation_issue(
            payments_util.ValidationReason.MISSING_FIELD, "vendor_customer_code"
        )

    if vendor_info.vendor_active_status is None:
        result.issues.add_validation_issue(
            payments_util.ValidationReason.MISSING_FIELD, "vendor_active_status"
        )
    elif (
        vendor_info.vendor_active_status is data_mart.VendorActiveStatus.INACTIVE
        or vendor_info.vendor_active_status is data_mart.VendorActiveStatus.NULL
        or vendor_info.vendor_active_status is data_mart.VendorActiveStatus.NOT_APPLICABLE
        or vendor_info.vendor_active_status is data_mart.VendorActiveStatus.DELETE
    ):
        result.issues.add_validation_issue(
            payments_util.ValidationReason.UNUSABLE_STATE,
            f"vendor_active_status is {vendor_info.vendor_active_status.name}",
        )
    elif vendor_info.vendor_active_status is data_mart.VendorActiveStatus.ACTIVE:
        # the one happy state we are looking for
        pass
    else:
        assert_never(vendor_info.vendor_active_status)

    if not vendor_info.address_id:
        result.issues.add_validation_issue(
            payments_util.ValidationReason.MISSING_FIELD, "Vendor address does not exist"
        )
    else:
        mmars_address = make_db_address_from_mmars_data(vendor_info)

        if employee.ctr_address_pair is None:
            raise ValueError(
                f"Employee does not have an existing ctr_address_pair. Employee ID: {employee.employee_id}"
            )

        if not payments_util.is_same_address(
            mmars_address, employee.ctr_address_pair.fineos_address
        ):
            result.issues.add_validation_issue(
                payments_util.ValidationReason.MISMATCHED_DATA, "Vendor address does not match"
            )
        else:
            if employee.ctr_address_pair.ctr_address is None:
                employee.ctr_address_pair.ctr_address = mmars_address
                result.employee_updates = True

    if employee.payment_method_id == PaymentMethod.ACH.payment_method_id:
        if not vendor_info.eft_status:
            result.issues.add_validation_issue(
                payments_util.ValidationReason.MISSING_FIELD,
                "No EFT information for Employee with ACH payment method in MMARS",
            )

        employee_eft_info = employee.eft
        if not employee_eft_info:
            raise ValueError(
                f"No EFT information for Employee with ACH payment method in API DB. Employee ID: {employee.employee_id}"
            )

        if vendor_info.aba_no != str(employee_eft_info.routing_nbr):
            result.issues.add_validation_issue(
                payments_util.ValidationReason.MISMATCHED_DATA,
                "Routing number in EFT information for Employee differs",
            )

    return result


def make_db_address_from_mmars_data(mmars_data: data_mart.VendorInfoResult) -> Address:
    mmars_geo_state_id = None
    mmars_geo_state_text = None

    try:
        mmars_geo_state_id = GeoState.get_id(mmars_data.state)
    except Exception:
        logger.warning(
            f"GeoState {mmars_data.state} does not exist in the API DB",
            extra={"not_found_geo_state": mmars_data.state},
        )
        mmars_geo_state_text = mmars_data.state

    mmars_country_id = None
    try:
        mmars_country_id = Country.get_id(mmars_data.country_code)
    except Exception:
        logger.warning(
            f"Country {mmars_data.country_code} does not exist in the API DB",
            extra={"not_found_country": mmars_data.country_code},
        )

    return Address(
        address_line_one=mmars_data.street_1,
        address_line_two=mmars_data.street_2,
        city=mmars_data.city,
        geo_state_id=mmars_geo_state_id,
        geo_state_text=mmars_geo_state_text,
        zip_code=mmars_data.zip_code,
        country_id=mmars_country_id,
    )


def process_data_mart_issues(
    pfml_db_session: pfml_db.Session,
    state_log: StateLog,
    employee: Employee,
    issues_and_updates: DataMartIssuesAndUpdates,
    missing_vendor_state: Union[LkState, BaseException],
    mismatched_data_state: LkState,
) -> None:
    if issues_and_updates.vendor_exists is False:
        if isinstance(missing_vendor_state, BaseException):
            raise missing_vendor_state

        state_log_util.finish_state_log(
            state_log=state_log,
            end_state=missing_vendor_state,
            outcome=state_log_util.build_outcome("Queried Data Mart: Vendor does not exist yet"),
            db_session=pfml_db_session,
        )
        return

    if issues_and_updates.issues.has_validation_issues():
        state_log_util.finish_state_log(
            state_log=state_log,
            end_state=mismatched_data_state,
            outcome=state_log_util.build_outcome(
                "Queried Data Mart: Vendor does not match", issues_and_updates.issues
            ),
            db_session=pfml_db_session,
        )
    else:
        state_log_util.finish_state_log(
            state_log=state_log,
            end_state=State.MMARS_STATUS_CONFIRMED,
            outcome=state_log_util.build_outcome("Vendor confirmed in MMARS."),
            db_session=pfml_db_session,
        )

        # If we've successfully confirmed the Employee info with what's in
        # MMARS, look for any payments for the Employee that have been waiting
        # on this confirmation.
        process_payments_waiting_on_vendor_confirmation(pfml_db_session, employee)


def process_payments_waiting_on_vendor_confirmation(
    pfml_db_session: pfml_db.Session, confirmed_employee: Employee
) -> List[StateLog]:
    payment_state_logs: List[StateLog] = (
        pfml_db_session.query(StateLog)
        .join(LatestStateLog)
        .filter(
            StateLog.end_state_id == State.CONFIRM_VENDOR_STATUS_IN_MMARS.state_id,
            LatestStateLog.payment_id.in_(
                pfml_db_session.query(Payment.payment_id)
                .join(Claim)
                .filter(Claim.employee_id == confirmed_employee.employee_id)
            ),
        )
        .all()
    )

    # If there are no pending payments, then we're done
    if not payment_state_logs:
        return []

    # If there *are* pending payments, we need to move them along
    new_payment_state_logs = []
    for payment_state_log in payment_state_logs:
        payment = payment_state_log.payment

        # This should never happen, but just in case...
        if not payment:
            logger.error(
                "Payment state log doesn't have associated payment. Can not advance to ADD_TO_GAX state.",
                extra={
                    "state_log_id": payment_state_log.state_log_id,
                    "employee_id": confirmed_employee.employee_id,
                },
            )
            continue

        # Create and finish state log entry to move the payment along to ADD_TO_GAX
        new_payment_state_log = state_log_util.create_state_log(
            start_state=State.CONFIRM_VENDOR_STATUS_IN_MMARS,
            associated_model=payment,
            db_session=pfml_db_session,
            commit=False,
        )

        state_log_util.finish_state_log(
            state_log=new_payment_state_log,
            end_state=State.ADD_TO_GAX,
            outcome=state_log_util.build_outcome("Vendor confirmed in MMARS."),
            db_session=pfml_db_session,
            commit=True,
        )

        new_payment_state_logs.append(new_payment_state_log)

    return new_payment_state_logs


def process_employees_in_state(
    pfml_db_session: pfml_db.Session,
    data_mart_engine: data_mart.Engine,
    end_state: LkState,
    process_state_log: Callable[
        [pfml_db.Session, data_mart.Connection, StateLog, Employee, TaxIdentifier], None
    ],
) -> None:
    logger.info(
        f"Starting processing of {end_state.state_description} records",
        extra={"start_state": end_state.state_description},
    )

    state_logs_for_employees = get_latest_state_logs_with_employees_in_state_for_processing(
        db_session=pfml_db_session, end_state=end_state
    )

    with data_mart_engine.connect() as data_mart_conn:
        for _prev_state_log, employee in state_logs_for_employees:
            try:
                with state_log_util.process_state(
                    start_state=end_state, associated_model=employee, db_session=pfml_db_session,
                ) as state_log:

                    tax_id = employee.tax_identifier

                    if not tax_id:
                        logger.error(
                            "Employee does not have a tax id. Skipping.",
                            extra={
                                "employee_id": employee.employee_id,
                                "state_log_id": state_log.state_log_id,
                            },
                        )
                        raise ValueError("Employee does not have a tax id. Skipping.")

                    process_state_log(pfml_db_session, data_mart_conn, state_log, employee, tax_id)
            except Exception:
                extra = {"start_state": end_state.state_description}

                if employee:
                    extra["employee_id"] = employee.employee_id

                if state_log:
                    extra["state_log_id"] = state_log.state_log_id

                logger.exception("Hit error processing record", extra=extra)

    logger.info(
        f"Done processing {end_state.state_description} records",
        extra={"start_state": end_state.state_description},
    )


def get_latest_state_logs_with_employees_in_state_for_processing(
    db_session: pfml_db.Session, end_state: LkState
) -> Iterable[Tuple[StateLog, Employee]]:
    state_logs_for_employees = state_log_util.get_all_latest_state_logs_in_end_state(
        associated_class=state_log_util.AssociatedClass.EMPLOYEE,
        end_state=end_state,
        db_session=db_session,
    )

    if not state_logs_for_employees:
        logger.info("No records in {end_state.state_description}")
        return []

    state_logs_for_employees_with_logging = logging.log_every(
        logger,
        state_logs_for_employees,
        item_name=f"Employee in {end_state.state_description} state",
        total_count=len(state_logs_for_employees),
        start_time=datetime_util.utcnow(),
        extra={"start_state": end_state.state_description},
    )

    return only_state_logs_with_employees(state_logs_for_employees_with_logging)


def only_state_logs_with_employees(
    state_logs: Iterable[StateLog],
) -> Iterable[Tuple[StateLog, Employee]]:
    """Skip state log records in the collection that don't have an Employee associated."""

    for state_log in state_logs:
        employee = state_log.employee

        if not employee:
            # Should never happen (*crosses fingers*)
            #
            # But if it does we can't really update the state log since
            # the new entry will have the same issue. Requires manual
            # intervention. The DB is broken.
            logger.error(
                "No employee for given state log. Skipping.",
                extra={
                    "state_log_id": state_log.state_log_id,
                    "start_state": state_log.start_state.state_description,
                },
            )
            continue

        yield state_log, employee
