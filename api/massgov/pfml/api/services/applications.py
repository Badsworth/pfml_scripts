from re import Pattern
from typing import Any, Dict, List, Optional, Tuple, Union

from sqlalchemy.orm.exc import NoResultFound
from werkzeug.exceptions import BadRequest, Forbidden

import massgov.pfml.api.models.applications.common as apps_common_io
import massgov.pfml.db as db
import massgov.pfml.db.lookups as db_lookups
import massgov.pfml.util.datetime as datetime_util
import massgov.pfml.util.logging
import massgov.pfml.util.pydantic.mask as mask
from massgov.pfml.api.models.applications.common import Address as ApiAddress
from massgov.pfml.api.models.applications.requests import ApplicationRequestBody
from massgov.pfml.api.models.applications.responses import DocumentResponse
from massgov.pfml.api.models.common import LookupEnum
from massgov.pfml.api.services.fineos_actions import get_documents
from massgov.pfml.api.util.response import IssueRule, IssueType
from massgov.pfml.api.validation.exceptions import ValidationErrorDetail, ValidationException
from massgov.pfml.db.models.applications import (
    Application,
    ApplicationPaymentPreference,
    ContinuousLeavePeriod,
    DayOfWeek,
    Document,
    IntermittentLeavePeriod,
    ReducedScheduleLeavePeriod,
    TaxIdentifier,
    WorkPattern,
    WorkPatternDay,
    WorkPatternType,
)
from massgov.pfml.db.models.employees import Address, AddressType, GeoState, LkAddressType
from massgov.pfml.util.pydantic.types import Regexes

logger = massgov.pfml.util.logging.get_logger(__name__)

LeaveScheduleDB = Union[ContinuousLeavePeriod, IntermittentLeavePeriod, ReducedScheduleLeavePeriod]


def process_partially_masked_field(
    field_key: str,
    body: Dict[str, Any],
    existing_masked_field: Any,
    masked_regex: Pattern,
    do_delete: bool = True,
    path: Optional[str] = None,  # If body is actually a much larger path (for errors)
) -> List[ValidationErrorDetail]:
    field = body.get(field_key)

    if field and masked_regex.match(field):
        if existing_masked_field != field:
            return [
                ValidationErrorDetail(
                    message=f"Partially masked {field_key} does not match existing value",
                    type=IssueType.invalid_masked_field,
                    rule=IssueRule.disallow_mismatched_masked_field,
                    field=path if path else field_key,
                )
            ]

        # If the new masked field does match when masked, just delete it from the request object (unless otherwise dictated).
        if do_delete:
            del body[field_key]

    # We return a list so this method can be used as: errors += process_partially_masked_field(..)
    return []


def process_fully_masked_field(
    field_key: str,
    body: Dict[str, Any],
    existing_field: Any,
    expected_masked_value: str,
    do_delete: bool = True,
    path: Optional[str] = None,  # If body is actually a much larger path (for errors)
) -> List[ValidationErrorDetail]:
    field = body.get(field_key)

    if field == expected_masked_value:
        # If there isn't already a value in our system, return an error
        if not existing_field:
            return [
                ValidationErrorDetail(
                    message=f"Masked {field_key} provided when field is not currently set",
                    type=IssueType.invalid_masked_field,
                    rule=IssueRule.disallow_fully_masked_no_existing,
                    field=path if path else field_key,
                )
            ]

        # In some scenarios, we may not want to delete the value (addresses)
        if do_delete:
            del body[field_key]
    # We return a list so this method can be used as: errors += process_fully_masked_field(..)
    return []


def process_masked_address(
    field_key: str, body: Dict[str, Any], existing_address: Address
) -> List[ValidationErrorDetail]:
    """ Handle masked addresses (mailing or residential) """
    address = body.get(field_key)
    errors = []
    if address:
        # line_1/line_2 - fully masked
        errors += process_fully_masked_field(
            field_key="line_1",
            body=address,
            existing_field=existing_address and existing_address.address_line_one,
            expected_masked_value=mask.ADDRESS_MASK,
            do_delete=False,
            path=f"{field_key}.line_1",
        )
        errors += process_fully_masked_field(
            field_key="line_2",
            body=address,
            existing_field=existing_address and existing_address.address_line_two,
            expected_masked_value=mask.ADDRESS_MASK,
            do_delete=False,
            path=f"{field_key}.line_2",
        )

        # zip_code - partially masked
        if existing_address:
            masked_existing_zip_code = mask.mask_zip(existing_address.zip_code)
        else:
            masked_existing_zip_code = None
        errors += process_partially_masked_field(
            field_key="zip",
            body=address,
            existing_masked_field=masked_existing_zip_code,
            masked_regex=Regexes.MASKED_ZIP,
            do_delete=False,
            path=f"{field_key}.zip",
        )
    return errors


def remove_masked_fields_from_request(
    body: Dict[str, Any], existing_application: Application
) -> Dict[str, Any]:
    """ Handle masked inputs, which varies depending on a few factors.

        This is done by checking against regexes/static strings to see if the value is masked.

        - Input is partially masked
          - If the visible portion matches what's in the DB - drop the field from the input, it's considered a non-change
          - If the visible portion does not match, throw a BadRequest error
          - If the DB does not contain any value yet, throw a BadRequest error

        - Input is fully masked
          - If correctly masked, drop the field from the input, it's considered a non-change
          - If not correctly masked, it'll pass through this logic, and should fail on later validation

        Note address fields (line_1, line_2, zip) behave differently because their update logic assumes
        a value not being set should be deleted unlike every other example. So, we instead just do the
        validation bit for those and have seperate logic in the add_or_update_address method for those.
    """
    errors = []
    # tax identifier - partially masked field
    masked_existing_tax_identifier = mask.mask_tax_identifier(existing_application.tax_identifier)
    errors += process_partially_masked_field(
        field_key="tax_identifier",
        body=body,
        existing_masked_field=masked_existing_tax_identifier,
        masked_regex=Regexes.TAX_ID_MASKED,
    )

    # mass ID - fully masked field
    errors += process_fully_masked_field(
        field_key="mass_id",
        body=body,
        existing_field=existing_application.mass_id,
        expected_masked_value=mask.MASS_ID_MASK,
    )

    # date of birth - partially masked
    masked_existing_date_of_birth = mask.mask_date(existing_application.date_of_birth)
    errors += process_partially_masked_field(
        field_key="date_of_birth",
        body=body,
        existing_masked_field=masked_existing_date_of_birth,
        masked_regex=Regexes.DATE_OF_BIRTH,
    )

    # Leave details
    leave_details = body.get("leave_details")
    if leave_details:
        # child date of birth - partially masked
        masked_existing_child_dob = mask.mask_date(existing_application.child_birth_date)
        errors += process_partially_masked_field(
            field_key="child_birth_date",
            body=leave_details,
            existing_masked_field=masked_existing_child_dob,
            masked_regex=Regexes.DATE_OF_BIRTH,
            path="leave_details.child_birth_date",
        )

        # child placement date - partially masked
        masked_existing_child_placement_date = mask.mask_date(
            existing_application.child_placement_date
        )
        errors += process_partially_masked_field(
            field_key="child_placement_date",
            body=leave_details,
            existing_masked_field=masked_existing_child_placement_date,
            masked_regex=Regexes.DATE_OF_BIRTH,
            path="leave_details.child_placement_date",
        )

    # mailing address + residential address
    errors += process_masked_address("mailing_address", body, existing_application.mailing_address)
    errors += process_masked_address(
        "residential_address", body, existing_application.residential_address
    )

    payment_preferences = body.get("payment_preferences")
    if payment_preferences:
        existing_payment_preferences = existing_application.payment_preferences
        for index, payment_preference in enumerate(payment_preferences):
            # All masked fields are in the account details, if not present, skip this record.
            account_details = payment_preference.get("account_details")
            if not account_details:
                continue
            # If the new payment preference does not have an ID, it's a new one
            # If there are no existing payment preferences, it can't be a (valid) update
            # Let these through and don't try to compare, if it's masked/invalid, later validation will error.
            payment_preference_id = payment_preference.get("payment_preference_id")
            if not payment_preference_id or not existing_payment_preferences:
                continue

            # Find the existing payment preference
            # If it doesn't match or doesn't belong to the application, it'll error later in validation.
            for existing_payment_preference in existing_payment_preferences:
                if str(existing_payment_preference.payment_pref_id) == payment_preference_id:
                    # routing number - fully masked
                    errors += process_fully_masked_field(
                        field_key="routing_number",
                        body=account_details,
                        existing_field=existing_payment_preference.routing_number,
                        expected_masked_value=mask.ROUTING_NUMBER_MASK,
                        path=f"payment_preferences[{index}].account_details.routing_number",
                    )

                    # account number - partially masked
                    masked_existing_acct_num = mask.mask_financial_account_number(
                        existing_payment_preference.account_number
                    )
                    errors += process_partially_masked_field(
                        field_key="account_number",
                        body=account_details,
                        existing_masked_field=masked_existing_acct_num,
                        masked_regex=Regexes.MASKED_ACCOUNT_NUMBER,
                        path=f"payment_preferences[{index}].account_details.account_number",
                    )

    if errors:
        raise ValidationException(
            errors=errors, message="Error validating masked fields", data=body
        )

    return body


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

        if key == "work_pattern":
            add_or_update_work_pattern(db_session, body.work_pattern, application)
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
    db_session.refresh(application)

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
) -> None:
    # Add more checks here as we add more Address types
    if address_type not in [AddressType.MAILING, AddressType.RESIDENTIAL]:
        raise ValueError("Invalid address type")

    state_id = None
    address_to_update = None
    if address is not None:
        if address.state:
            state_id = GeoState.get_id(address.state)

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

        if address is None:
            setattr(application, address_id_field_name, None)
        elif db_address is not None and state_id is not None:
            db_address.address_line_one = (
                address.line_1
                if address.line_1 != mask.ADDRESS_MASK
                else db_address.address_line_one
            )
            db_address.address_line_two = (
                address.line_2
                if address.line_2 != mask.ADDRESS_MASK
                else db_address.address_line_two
            )
            db_address.city = address.city
            db_address.geo_state_id = state_id
            db_address.zip_code = (
                address.zip
                if address.zip and not Regexes.MASKED_ZIP.match(address.zip)
                else db_address.zip_code
            )
    # If we don't have an existing address but have a body, add an address.
    elif address_to_update is not None:
        db_session.add(address_to_update)
        setattr(application, address_field_name, address_to_update)


def add_or_update_work_pattern(
    db_session: db.Session,
    api_work_pattern: Optional[apps_common_io.WorkPattern],
    application: Application,
) -> None:
    if api_work_pattern is None:
        return None

    # Consider only explicitly set fields
    fieldset = api_work_pattern.__fields_set__
    work_pattern = application.work_pattern or WorkPattern()

    if "work_pattern_days" in fieldset:
        validate_work_pattern_days(api_work_pattern.work_pattern_days)

        if work_pattern.work_pattern_days:
            for work_pattern_day in work_pattern.work_pattern_days:
                db_session.delete(work_pattern_day)

            work_pattern.work_pattern_days = []

        if api_work_pattern.work_pattern_days:
            work_pattern_days = []

            for api_work_pattern_day in api_work_pattern.work_pattern_days:
                work_pattern_days.append(
                    WorkPatternDay(
                        day_of_week_id=DayOfWeek.get_id(api_work_pattern_day.day_of_week.value),
                        week_number=api_work_pattern_day.week_number,
                        minutes=api_work_pattern_day.minutes,
                    )
                )

                work_pattern.work_pattern_days = work_pattern_days
    if "work_week_starts" in fieldset:
        if api_work_pattern.work_week_starts:
            work_pattern.work_week_starts_id = DayOfWeek.get_id(
                api_work_pattern.work_week_starts.value
            )
        else:
            work_pattern.work_week_starts_id = None

    if "work_pattern_type" in fieldset:
        if api_work_pattern.work_pattern_type:
            work_pattern.work_pattern_type_id = WorkPatternType.get_id(
                api_work_pattern.work_pattern_type.value
            )
        else:
            work_pattern.work_pattern_type_id = None

    if "pattern_start_date" in fieldset:
        if api_work_pattern.pattern_start_date is not None:
            pattern_start_week_day_id = api_work_pattern.pattern_start_date.isoweekday()
            if pattern_start_week_day_id != work_pattern.work_week_starts_id:
                raise BadRequest(
                    "pattern_start_date must be on the same day of the week that the work week starts."
                )

        work_pattern.pattern_start_date = api_work_pattern.pattern_start_date

    db_session.add(work_pattern)
    application.work_pattern = work_pattern


def validate_work_pattern_days(
    api_work_pattern_days: Optional[List[apps_common_io.WorkPatternDay]],
) -> None:
    """Validate work pattern. These errors should not be the result of bad user input"""
    if api_work_pattern_days is None:
        return None

    weeks: Tuple[
        List[apps_common_io.WorkPatternDay],
        List[apps_common_io.WorkPatternDay],
        List[apps_common_io.WorkPatternDay],
        List[apps_common_io.WorkPatternDay],
    ] = ([], [], [], [])
    for day in api_work_pattern_days:
        # week_number 1 - 4 is enforced through OpenAPI spec
        weeks[day.week_number - 1].append(day)

    for i, week in enumerate(weeks):
        number_of_days = len(week)

        if number_of_days == 0:
            continue

        provided_week_days = {day.day_of_week.value for day in week}
        week_days = {"Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"}
        missing_days = week_days - provided_week_days
        if len(missing_days) > 0:
            raise BadRequest(
                f"Week number {i+1} for provided work_pattern_days is missing {', '.join(sorted(missing_days))}."
            )

        if number_of_days != 7:
            raise BadRequest(
                f"Week number {i+1} for provided work_pattern_days has {number_of_days} days. There should be 7 days."
            )

        # Check if work pattern weeks aren't consecutive, as in request provides
        # 7 days for week number 3 but 0 days for week number 2
        if i > 0 and len(weeks[i - 1]) == 0:
            raise BadRequest(
                f"Week number {i} for provided work_pattern_days has 0 days, but you are attempting to add days for week number {i+1}. All provided weeks should be consecutive."
            )


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


def get_document_by_id(
    db_session: db.Session, document_id: str, application: Application
) -> Optional[Union[Document, DocumentResponse]]:
    document = None
    try:
        # check whether document metadata exists in database
        document = db_session.query(Document).filter(Document.fineos_id == document_id).one()
    except NoResultFound:
        # if not, retrieve the document using fineos_actions
        # this will return a DocumentResponse rather than a document
        documents = get_documents(application, db_session)
        for d in documents:
            if d.fineos_document_id == document_id:
                return d
        logger.warning("No document found for ID %s", document_id)

    return document
