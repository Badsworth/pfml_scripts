from typing import Any, List, Optional, Union

from werkzeug.exceptions import BadRequest, Forbidden

import massgov.pfml.api.models.applications.common as apps_common_io
import massgov.pfml.db as db
import massgov.pfml.db.lookups as db_lookups
import massgov.pfml.util.datetime as datetime_util
import massgov.pfml.util.logging
from massgov.pfml.api.models.applications.common import Address as ApiAddress
from massgov.pfml.api.models.applications.requests import ApplicationRequestBody
from massgov.pfml.api.models.common import LookupEnum
from massgov.pfml.db.models.applications import (
    Application,
    ApplicationPaymentPreference,
    ContinuousLeavePeriod,
    IntermittentLeavePeriod,
    ReducedScheduleLeavePeriod,
    TaxIdentifier,
)
from massgov.pfml.db.models.employees import Address, AddressType, GeoState, LkAddressType

logger = massgov.pfml.util.logging.get_logger(__name__)

LeaveScheduleDB = Union[ContinuousLeavePeriod, IntermittentLeavePeriod, ReducedScheduleLeavePeriod]


def update_from_request(
    db_session: db.Session, body: ApplicationRequestBody, application: Application
) -> Application:
    # TODO: generalize this update functionality, considering only explicitly
    # set keys, LookupEnum handling, alias/map field names, etc.
    for key in body.__fields_set__:
        value = getattr(body, key)

        if key in ("leave_details", "payment_preferences", "employee_ssn", "tax_identifier"):
            continue

        if key == "mailing_address":
            add_or_update_address(
                db_session, body.mailing_address, AddressType.MAILING, application
            )
            continue

        if key == "residential_address":
            add_or_update_address(
                db_session, body.residential_address, AddressType.RESIDENTIAL, application
            )
            continue

        if key == "application_nickname":
            key = "nickname"

        if isinstance(value, LookupEnum):
            lookup_model = db_lookups.by_value(db_session, value.get_lookup_model(), value)

            if lookup_model:
                if key == "reason":
                    key = "leave_reason"

                if key == "reason_qualifier":
                    key = "leave_reason_qualifier"

                value = lookup_model

        setattr(application, key, value)

    leave_schedules = update_leave_details(db_session, body, application)
    payment_preferences = update_payment_preferences(db_session, body, application)

    tax_id = get_or_add_tax_identifier(db_session, body)
    if tax_id is not None:
        db_session.add(tax_id)
        application.tax_identifier = tax_id

    application.updated_time = datetime_util.utcnow()
    db_session.add(application)

    for leave_schedule in leave_schedules:
        db_session.add(leave_schedule)

    if payment_preferences:
        db_session.add(payment_preferences)
    db_session.flush()
    db_session.commit()

    return application


def update_leave_details(
    db_session: db.Session, body: ApplicationRequestBody, application: Application
) -> List[LeaveScheduleDB]:
    leave_details_json = body.leave_details

    if leave_details_json is None:
        return []

    leave_schedules = []

    for key in leave_details_json.__fields_set__:
        value = getattr(leave_details_json, key)

        if (
            key == "continuous_leave_periods"
            or key == "intermittent_leave_periods"
            or key == "reduced_schedule_leave_periods"
        ):
            leave_schedule = update_leave_schedule(db_session, value, application)
            if leave_schedule:
                leave_schedules.append(leave_schedule)
            continue

        if isinstance(value, LookupEnum):
            lookup_model = db_lookups.by_value(db_session, value.get_lookup_model(), value)
            if lookup_model:
                if key == "reason":
                    key = "leave_reason"

                if key == "reason_qualifier":
                    key = "leave_reason_qualifier"

                value = lookup_model

        setattr(application, key, value)

    return leave_schedules


LeaveScheduleRequest = List[
    Union[
        apps_common_io.ReducedScheduleLeavePeriods,
        apps_common_io.ContinuousLeavePeriods,
        apps_common_io.IntermittentLeavePeriods,
    ]
]


def update_leave_schedule(
    db_session: db.Session, leave_schedule: Optional[LeaveScheduleRequest], application: Application
) -> Optional[LeaveScheduleDB]:
    # To be improved in next iteration
    if leave_schedule is None or len(leave_schedule) == 0:
        return None

    leave_schedule_item = leave_schedule[0]

    def update_leave_period(leave_input: Any, leave_cls: Any) -> Optional[LeaveScheduleDB]:
        if leave_input.leave_period_id:
            # look up existing leave period to update if pointed to one
            leave_period = db_session.query(leave_cls).get(leave_input.leave_period_id)

            # if we don't find it, client messed up
            if leave_period is None:
                raise BadRequest(
                    f"Referenced leave period with id {leave_input.leave_period_id} does not exist or you do not have access to edit it."
                )

            # but ensure the leave period actually belongs to this application
            if leave_period.application_id != application.application_id:
                logger.info(
                    "Attempted to update a leave period that did not belong to Application being updated.",
                    extra={
                        "application_id": application.application_id,
                        "leave_period_id": leave_period.leave_period_id,
                        "leave_period_class": leave_cls,
                        "leave_period_application_id": leave_period.application_id,
                    },
                )
                # TODO: should we be throwing HTTP exceptions from services?
                # should we provide a better, more detailed message?
                raise Forbidden()
        else:
            leave_period = leave_cls()
            leave_period.application_id = application.application_id

        for key in leave_input.__fields_set__:
            value = getattr(leave_input, key)
            setattr(leave_period, key, value)

        return leave_period

    if isinstance(leave_schedule_item, apps_common_io.ContinuousLeavePeriods):
        return update_leave_period(leave_schedule_item, ContinuousLeavePeriod)
    elif isinstance(leave_schedule_item, apps_common_io.IntermittentLeavePeriods):
        return update_leave_period(leave_schedule_item, IntermittentLeavePeriod)
    else:
        return update_leave_period(leave_schedule_item, ReducedScheduleLeavePeriod)


def update_payment_preferences(
    db_session: db.Session, body: ApplicationRequestBody, application: Application
) -> Optional[ApplicationPaymentPreference]:
    payment_preferences_json = body.payment_preferences
    if payment_preferences_json is None or len(payment_preferences_json) == 0:
        return None

    # To be improved to deal with array
    payment_preferences_item = payment_preferences_json[0]

    if payment_preferences_item.payment_preference_id:
        # look up existing payment preference to update if pointed to one
        payment_preference = db_session.query(ApplicationPaymentPreference).get(
            payment_preferences_item.payment_preference_id
        )

        # if we don't find it, client messed up
        if payment_preference is None:
            raise BadRequest(
                f"Referenced payment preference with id {payment_preferences_item.payment_preference_id} does not exist or you do not have access to edit it."
            )

        # but ensure it actually belongs to this application
        if payment_preference.application_id != application.application_id:
            logger.info(
                "Attempted to update a payment preference that did not belong to Application being updated.",
                extra={
                    "application_id": application.application_id,
                    "payment_preference_id": payment_preference.payment_pref_id,
                    "payment_preference_application_id": payment_preference.application_id,
                },
            )
            # TODO: should we be throwing HTTP exceptions from services?
            # should we provide a better, more detailed message?
            raise Forbidden()
    else:
        payment_preference = ApplicationPaymentPreference()
        payment_preference.application_id = application.application_id

    for key in payment_preferences_item.__fields_set__:
        value = getattr(payment_preferences_item, key)

        if key == "account_details" or key == "cheque_details":
            continue

        if isinstance(value, LookupEnum):
            lookup_model = db_lookups.by_value(db_session, value.get_lookup_model(), value)
            if lookup_model:
                if key == "payment_method":
                    key = "payment_type"

                value = lookup_model

        setattr(payment_preference, key, value)

    if payment_preferences_item.account_details is not None:
        for key in payment_preferences_item.account_details.__fields_set__:
            value = getattr(payment_preferences_item.account_details, key)

            if key == "account_type":
                key = "type_of_account"

            setattr(payment_preference, key, value)

    if payment_preferences_item.cheque_details is not None:
        for key in payment_preferences_item.cheque_details.__fields_set__:
            value = getattr(payment_preferences_item.cheque_details, key)

            if key == "name_to_print_on_check":
                key = "name_in_check"

            setattr(payment_preference, key, value)

    return payment_preference


def add_or_update_address(
    db_session: db.Session,
    address: Optional[ApiAddress],
    address_type: LkAddressType,
    application: Application,
) -> Optional[Address]:
    # Add more checks here as we add more Address types
    if address_type not in [AddressType.MAILING, AddressType.RESIDENTIAL]:
        raise ValueError("Invalid address type")

    state_id = None
    address_to_update = None
    if address is not None:
        state_id = GeoState.get_id(address.state)

        if state_id is None:
            raise ValueError("Invalid state code provided")
        else:
            address_to_update = Address(
                address_line_one=address.line_1,
                address_line_two=address.line_2,
                city=address.city,
                geo_state_id=state_id,
                zip_code=address.zip,
            )

    address_field_name, address_id_field_name, address_type_id = address_type_mapping(address_type)

    if address_to_update is not None:
        address_to_update.address_type_id = address_type_id

    existing_address_id = getattr(application, address_id_field_name)

    # If an address exists, update with what we have
    if existing_address_id is not None:
        db_address = (
            db_session.query(Address)
            .filter(Address.address_id == existing_address_id)
            .one_or_none()
        )

        # If we had an address and there's none in the request, remove the association.
        if address is None:
            setattr(application, address_id_field_name, None)
        elif db_address is not None and state_id is not None:
            db_address.address_line_one = address.line_1
            db_address.address_line_two = address.line_2
            db_address.city = address.city
            db_address.geo_state_id = state_id
            db_address.zip_code = address.zip
    # If we don't have an existing address but have a body, add an address.
    elif address_to_update is not None:
        db_session.add(address_to_update)
        setattr(application, address_field_name, address_to_update)

    return address_to_update


def get_or_add_tax_identifier(
    db_session: db.Session, body: ApplicationRequestBody
) -> Optional[TaxIdentifier]:
    tax_identifier = body.tax_identifier or body.employee_ssn

    if tax_identifier is None:
        return None

    tax_id = (
        db_session.query(TaxIdentifier)
        .filter(TaxIdentifier.tax_identifier == tax_identifier)
        .one_or_none()
    )

    if tax_id is None:
        tax_id = TaxIdentifier(tax_identifier=tax_identifier)

    return tax_id


def address_type_mapping(address_type):
    if address_type == AddressType.MAILING:
        return ("mailing_address", "mailing_address_id", AddressType.MAILING.address_type_id)
    elif address_type == AddressType.RESIDENTIAL:
        return (
            "residential_address",
            "residential_address_id",
            AddressType.RESIDENTIAL.address_type_id,
        )
