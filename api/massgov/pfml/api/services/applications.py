from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from re import Pattern
from typing import Any, Dict, List, Literal, Optional, Tuple, Type, Union
from uuid import UUID

import phonenumbers
from phonenumbers.phonenumberutil import region_code_for_number
from sqlalchemy.orm.exc import NoResultFound
from werkzeug.exceptions import BadRequest, Conflict, Forbidden

import massgov.pfml.api.models.applications.common as apps_common_io
import massgov.pfml.api.models.common as common_io
import massgov.pfml.api.util.response as response_util
import massgov.pfml.db as db
import massgov.pfml.db.lookups as db_lookups
import massgov.pfml.util.logging
import massgov.pfml.util.newrelic.events as newrelic_util
import massgov.pfml.util.pydantic.mask as mask
from massgov.pfml.api.models.applications.common import Address as ApiAddress
from massgov.pfml.api.models.applications.common import (
    BankAccountType,
    DocumentResponse,
    LeaveReason,
)
from massgov.pfml.api.models.applications.common import PaymentMethod as CommonPaymentMethod
from massgov.pfml.api.models.applications.common import PaymentPreference
from massgov.pfml.api.models.applications.requests import ApplicationRequestBody
from massgov.pfml.api.models.common import (
    LookupEnum,
    get_earliest_start_date,
    get_earliest_submission_date,
    get_latest_end_date,
)
from massgov.pfml.api.services.administrator_fineos_actions import EformTypes
from massgov.pfml.api.services.fineos_actions import get_documents
from massgov.pfml.api.util.response import Response
from massgov.pfml.api.validation.exceptions import (
    IssueRule,
    IssueType,
    ValidationErrorDetail,
    ValidationException,
)
from massgov.pfml.db.models.absences import AbsencePeriodType
from massgov.pfml.db.models.applications import (
    AmountFrequency,
    Application,
    ApplicationPaymentPreference,
    CaringLeaveMetadata,
    ConcurrentLeave,
    ContinuousLeavePeriod,
    DayOfWeek,
    Document,
    EmployerBenefit,
    EmployerBenefitType,
    EmploymentStatus,
    IntermittentLeavePeriod,
)
from massgov.pfml.db.models.applications import LeaveReason as DBLeaveReason
from massgov.pfml.db.models.applications import (
    LeaveReasonQualifier,
    LkAmountFrequency,
    LkPhoneType,
    OtherIncome,
    OtherIncomeType,
    Phone,
    PhoneType,
    PreviousLeave,
    PreviousLeaveOtherReason,
    PreviousLeaveQualifyingReason,
    PreviousLeaveSameReason,
    ReducedScheduleLeavePeriod,
    TaxIdentifier,
    WorkPattern,
    WorkPatternDay,
    WorkPatternType,
)
from massgov.pfml.db.models.employees import (
    Address,
    AddressType,
    BenefitYear,
    Claim,
    LeaveRequestDecision,
    LkAddressType,
    LkGender,
    MFADeliveryPreference,
    PaymentMethod,
    User,
)
from massgov.pfml.db.models.geo import GeoState
from massgov.pfml.fineos import AbstractFINEOSClient, exception
from massgov.pfml.fineos.models.customer_api import AbsencePeriodStatus, PhoneNumber
from massgov.pfml.fineos.models.customer_api.spec import (
    AbsenceDay,
    AbsenceDetails,
    AbsencePeriod,
    EForm,
    EFormSummary,
)
from massgov.pfml.fineos.transforms.from_fineos.eforms import (
    TransformConcurrentLeaveFromOtherLeaveEform,
    TransformEmployerBenefitsFromOtherIncomeEform,
    TransformOtherIncomeEform,
    TransformOtherIncomeNonEmployerEform,
    TransformPreviousLeaveFromOtherLeaveEform,
)
from massgov.pfml.util.datetime import is_date_contained, utcnow
from massgov.pfml.util.logging.applications import (
    get_absence_period_log_attributes,
    get_application_log_attributes,
)
from massgov.pfml.util.pydantic.types import FinancialRoutingNumber, Regexes

logger = massgov.pfml.util.logging.get_logger(__name__)

LeaveScheduleDB = Union[ContinuousLeavePeriod, IntermittentLeavePeriod, ReducedScheduleLeavePeriod]
OtherBenefitsDB = Union[EmployerBenefit, OtherIncome, PreviousLeave, ConcurrentLeave]
EFORM_CACHE = Dict[int, EForm]


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
    """Handle masked addresses (mailing or residential)"""
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


def process_masked_phone_number(
    field_key: str, body: Dict[str, Any], existing_phone: Phone
) -> List[ValidationErrorDetail]:
    """Handle masked phone number"""
    phone = body.get(field_key)
    errors = []

    if phone:
        masked_existing_phone_number = None
        if existing_phone and existing_phone.phone_number:
            # convert existing phone (in E.164) to masked version of front-end format (***-***-####) to compare masked values
            parsed_existing_phone_number = phonenumbers.parse(existing_phone.phone_number)
            region_code = region_code_for_number(parsed_existing_phone_number)
            if region_code:
                locally_formatted_number = phonenumbers.format_in_original_format(
                    parsed_existing_phone_number, region_code
                )
                masked_existing_phone_number = mask.mask_phone(locally_formatted_number)
            else:
                masked_existing_phone_number = mask.mask_phone(existing_phone.phone_number)

            errors += process_partially_masked_field(
                field_key="phone_number",
                body=phone,
                existing_masked_field=masked_existing_phone_number,
                masked_regex=Regexes.MASKED_PHONE,
                path=f"{field_key}.phone_number",
            )
    return errors


def remove_masked_fields_from_request(
    body: Dict[str, Any], existing_application: Application
) -> Dict[str, Any]:
    """Handle masked inputs, which varies depending on a few factors.

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
    masked_existing_tax_identifier = (
        mask.mask_tax_identifier(existing_application.tax_identifier.tax_identifier)
        if existing_application.tax_identifier
        else None
    )
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

    # Phone
    errors += process_masked_phone_number("phone", body, existing_application.phone)

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

        # family member date of birth - partially masked
        if existing_application.caring_leave_metadata and leave_details.get(
            "caring_leave_metadata"
        ):
            masked_existing_family_member_dob = mask.mask_date(
                existing_application.caring_leave_metadata.family_member_date_of_birth
            )
            errors += process_partially_masked_field(
                field_key="family_member_date_of_birth",
                body=leave_details.get("caring_leave_metadata"),
                existing_masked_field=masked_existing_family_member_dob,
                masked_regex=Regexes.DATE_OF_BIRTH,
                path="leave_details.caring_leave_metadata.family_member_date_of_birth",
            )

    # mailing address + residential address
    errors += process_masked_address("mailing_address", body, existing_application.mailing_address)
    errors += process_masked_address(
        "residential_address", body, existing_application.residential_address
    )

    payment_preference = body.get("payment_preference")
    if payment_preference:
        existing_payment_preference = existing_application.payment_preference

        # If there is no existing payment preference,
        # this is a new payment preference and should not be masked.
        if existing_payment_preference is not None:
            # routing number - fully masked
            errors += process_fully_masked_field(
                field_key="routing_number",
                body=payment_preference,
                existing_field=existing_payment_preference.routing_number,
                expected_masked_value=mask.ROUTING_NUMBER_MASK,
                path="payment_preference.routing_number",
            )

            # account number - partially masked
            masked_existing_acct_num = mask.mask_financial_account_number(
                existing_payment_preference.account_number
            )
            errors += process_partially_masked_field(
                field_key="account_number",
                body=payment_preference,
                existing_masked_field=masked_existing_acct_num,
                masked_regex=Regexes.MASKED_ACCOUNT_NUMBER,
                path="payment_preference.account_number",
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

        if key in ("leave_details", "tax_identifier"):
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

        if key == "employer_benefits":
            set_employer_benefits(db_session, body.employer_benefits, application)
            continue

        if key == "other_incomes":
            set_other_incomes(db_session, body.other_incomes, application)
            continue

        if key == "concurrent_leave":
            set_concurrent_leave(db_session, body.concurrent_leave, application)
            continue

        if key == "previous_leaves_other_reason":
            set_previous_leaves(
                db_session, body.previous_leaves_other_reason, application, "other_reason"
            )
            continue

        if key == "previous_leaves_same_reason":
            set_previous_leaves(
                db_session, body.previous_leaves_same_reason, application, "same_reason"
            )
            continue

        if key == "phone":
            add_or_update_phone(db_session, body.phone, application)
            continue
        if isinstance(value, LookupEnum):
            lookup_model = db_lookups.by_value(db_session, value.get_lookup_model(), value)

            if lookup_model:
                value = lookup_model

        setattr(application, key, value)

    leave_schedules = update_leave_details(db_session, body, application)

    tax_id = get_or_add_tax_identifier(db_session, body)
    if tax_id is not None:
        db_session.add(tax_id)
        application.tax_identifier = tax_id

    db_session.add(application)

    for leave_schedule in leave_schedules:
        db_session.add(leave_schedule)

    db_session.commit()
    db_session.refresh(application)
    if application.work_pattern is not None:
        db_session.refresh(application.work_pattern)

    return application


leave_period_class_for_label: Dict[str, Type[LeaveScheduleDB]] = {
    "continuous_leave_periods": ContinuousLeavePeriod,
    "intermittent_leave_periods": IntermittentLeavePeriod,
    "reduced_schedule_leave_periods": ReducedScheduleLeavePeriod,
}


def add_or_update_caring_leave_metadata(
    db_session: db.Session,
    api_caring_leave_metadata: Optional[apps_common_io.CaringLeaveMetadata],
    application: Application,
) -> None:
    if not api_caring_leave_metadata:
        return None

    caring_leave_metadata = application.caring_leave_metadata or CaringLeaveMetadata()

    for key in api_caring_leave_metadata.__fields_set__:
        value = getattr(api_caring_leave_metadata, key)

        if key == "relationship_to_caregiver" and value is not None:
            relationship_to_caregiver_model = db_lookups.by_value(
                db_session, value.get_lookup_model(), value
            )
            if relationship_to_caregiver_model:
                value = relationship_to_caregiver_model
        setattr(caring_leave_metadata, key, value)

    application.caring_leave_metadata = caring_leave_metadata


def update_leave_details(
    db_session: db.Session, body: ApplicationRequestBody, application: Application
) -> List[LeaveScheduleDB]:
    leave_details_json = body.leave_details

    if leave_details_json is None:
        return []

    leave_schedules = []

    for key in leave_details_json.__fields_set__:
        value = getattr(leave_details_json, key)

        if key in leave_period_class_for_label:
            leave_schedule = update_leave_schedule(
                db_session, value, application, leave_period_class_for_label[key]
            )
            if leave_schedule:
                leave_schedules.append(leave_schedule)
            continue

        if key == "caring_leave_metadata":
            add_or_update_caring_leave_metadata(db_session, value, application)
            continue

        if isinstance(value, LookupEnum):
            lookup_model = db_lookups.by_value(db_session, value.get_lookup_model(), value)
            if lookup_model:
                if key == "reason":
                    key = "leave_reason"

                    # If leave reason changes from Caring Leave, delete CaringLeaveMetadata record if it exists
                    if (
                        value != LeaveReason.caring_leave
                        and application.leave_reason
                        and application.leave_reason.leave_reason_description
                        == LeaveReason.caring_leave
                        and application.caring_leave_metadata is not None
                    ):
                        db_session.delete(application.caring_leave_metadata)

                if key == "reason_qualifier":
                    key = "leave_reason_qualifier"

                value = lookup_model
        if key == "reason_qualifier" and not value:
            key = "leave_reason_qualifier"
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
    db_session: db.Session,
    leave_schedule: Optional[LeaveScheduleRequest],
    application: Application,
    leave_cls: Type[LeaveScheduleDB],
) -> Optional[LeaveScheduleDB]:
    if leave_schedule is None or len(leave_schedule) == 0:
        # Leave periods are removed by sending a PATCH request with an
        # empty array (or null value) for that category of leave.
        if leave_cls == ContinuousLeavePeriod:
            application.continuous_leave_periods = []
        elif leave_cls == IntermittentLeavePeriod:
            application.intermittent_leave_periods = []
        elif leave_cls == ReducedScheduleLeavePeriod:
            application.reduced_schedule_leave_periods = []

        return None

    # We expect only a single period of leave in the array for the time being.
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

    return update_leave_period(leave_schedule_item, leave_cls)


def add_or_update_payment_preference(
    db_session: db.Session,
    payment_preference_json: Optional[PaymentPreference],
    application: Application,
) -> None:
    if payment_preference_json is None:
        db_session.delete(application.payment_preference)
        db_session.commit()
        del application.payment_preference
        return None

    if application.payment_preference_id is None:
        payment_preference = ApplicationPaymentPreference()
    else:
        payment_preference = application.payment_preference

    for key in payment_preference_json.__fields_set__:
        value = getattr(payment_preference_json, key)

        if isinstance(value, LookupEnum):
            lookup_model = db_lookups.by_value(db_session, value.get_lookup_model(), value)
            value = lookup_model

        setattr(payment_preference, key, value)

    application.payment_preference = payment_preference
    return None


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
    fields_to_update = set()

    if address is not None:
        if address.state:
            try:
                state_id = GeoState.get_id(address.state)
            except KeyError as error:
                message = f"'{error.args[0]}' is not a valid state"
                # Guard clause is included here to satisfy the linter...
                address_description = (
                    address_type.address_description and address_type.address_description.lower()
                )
                error_detail = ValidationErrorDetail(
                    type=IssueType.invalid,
                    message=message,
                    field=f"{address_description}_address.state",
                )
                raise ValidationException([error_detail], message, {})

        address_to_update = Address(
            address_line_one=address.line_1,
            address_line_two=address.line_2,
            city=address.city,
            geo_state_id=state_id,
            zip_code=address.zip,
        )
        fields_to_update = address.__fields_set__

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
        elif db_address is not None:
            db_address.address_line_one = (
                address.line_1
                if address.line_1 != mask.ADDRESS_MASK and "line_1" in fields_to_update
                else db_address.address_line_one
            )
            db_address.address_line_two = (
                address.line_2
                if address.line_2 != mask.ADDRESS_MASK and "line_2" in fields_to_update
                else db_address.address_line_two
            )
            if "city" in fields_to_update:
                db_address.city = address.city
            if "state" in fields_to_update:
                db_address.geo_state_id = state_id
            if "zip" in fields_to_update and address.zip:
                # re-use the db value if zip is masked, otherwise, use the new value
                if not Regexes.MASKED_ZIP.match(address.zip):
                    db_address.zip_code = address.zip

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
                        minutes=api_work_pattern_day.minutes,
                    )
                )

            work_pattern.work_pattern_days = work_pattern_days

    if "work_pattern_type" in fieldset:
        if api_work_pattern.work_pattern_type:
            work_pattern.work_pattern_type_id = WorkPatternType.get_id(
                api_work_pattern.work_pattern_type.value
            )
        else:
            work_pattern.work_pattern_type_id = None

    db_session.add(work_pattern)
    application.work_pattern = work_pattern


def delete_application_other_benefits(
    benefit: Type[OtherBenefitsDB], application: Application, db_session: db.Session
) -> None:
    db_session.query(benefit).filter(benefit.application_id == application.application_id).delete(
        synchronize_session=False
    )
    db_session.refresh(application)


def set_employer_benefits(
    db_session: db.Session,
    api_employer_benefits: Optional[List[common_io.EmployerBenefit]],
    application: Application,
) -> None:

    benefits: List[EmployerBenefit] = []

    if application.employer_benefits:
        delete_application_other_benefits(EmployerBenefit, application, db_session)

    if not api_employer_benefits:
        return

    for api_employer_benefit in api_employer_benefits:
        new_employer_benefit = EmployerBenefit(
            application_id=application.application_id,
            benefit_start_date=api_employer_benefit.benefit_start_date,
            benefit_end_date=api_employer_benefit.benefit_end_date,
            benefit_amount_dollars=api_employer_benefit.benefit_amount_dollars,
            is_full_salary_continuous=api_employer_benefit.is_full_salary_continuous,
        )

        if api_employer_benefit.benefit_type:
            new_employer_benefit.benefit_type_id = EmployerBenefitType.get_id(
                api_employer_benefit.benefit_type.value
            )
        if api_employer_benefit.benefit_amount_frequency:
            new_employer_benefit.benefit_amount_frequency_id = AmountFrequency.get_id(
                api_employer_benefit.benefit_amount_frequency.value
            )
        benefits.append(new_employer_benefit)
        db_session.add(new_employer_benefit)
    application.employer_benefits = benefits


def set_other_incomes(
    db_session: db.Session,
    api_other_incomes: Optional[List[apps_common_io.OtherIncome]],
    application: Application,
) -> None:
    other_incomes: List[OtherIncome] = []
    if application.other_incomes:
        delete_application_other_benefits(OtherIncome, application, db_session)

    if not api_other_incomes:
        return

    for api_other_income in api_other_incomes:
        new_other_income = OtherIncome(
            application_id=application.application_id,
            income_start_date=api_other_income.income_start_date,
            income_end_date=api_other_income.income_end_date,
            income_amount_dollars=api_other_income.income_amount_dollars,
        )

        if api_other_income.income_type:
            new_other_income.income_type_id = OtherIncomeType.get_id(
                api_other_income.income_type.value
            )
        if api_other_income.income_amount_frequency:
            new_other_income.income_amount_frequency_id = AmountFrequency.get_id(
                api_other_income.income_amount_frequency.value
            )
        other_incomes.append(new_other_income)
        db_session.add(new_other_income)
    application.other_incomes = other_incomes


def set_concurrent_leave(
    db_session: db.Session,
    api_concurrent_leave: Optional[massgov.pfml.api.models.common.ConcurrentLeave],
    application: Application,
) -> None:
    if application.concurrent_leave:
        delete_application_other_benefits(ConcurrentLeave, application, db_session)

    if not api_concurrent_leave:
        return

    concurrent_leave = ConcurrentLeave(
        application_id=application.application_id,
        is_for_current_employer=api_concurrent_leave.is_for_current_employer,
        leave_start_date=api_concurrent_leave.leave_start_date,
        leave_end_date=api_concurrent_leave.leave_end_date,
    )
    db_session.add(concurrent_leave)


def set_previous_leaves(
    db_session: db.Session,
    api_previous_leaves: Optional[List[common_io.PreviousLeave]],
    application: Application,
    type: Literal["same_reason", "other_reason"],
) -> None:
    previous_leave_type = {
        "same_reason": PreviousLeaveSameReason,
        "other_reason": PreviousLeaveOtherReason,
    }[type]

    if getattr(application, f"previous_leaves_{type}"):
        db_session.query(PreviousLeave).filter(
            PreviousLeave.application_id == application.application_id
        ).filter(PreviousLeave.type == type).delete(synchronize_session=False)
        db_session.refresh(application)

    if not api_previous_leaves:
        return

    for api_previous_leave in api_previous_leaves:
        new_previous_leave = previous_leave_type(
            application_id=application.application_id,
            leave_start_date=api_previous_leave.leave_start_date,
            leave_end_date=api_previous_leave.leave_end_date,
            is_for_current_employer=api_previous_leave.is_for_current_employer,
            worked_per_week_minutes=api_previous_leave.worked_per_week_minutes,
            leave_minutes=api_previous_leave.leave_minutes,
        )

        # We only care about the leave reason for PreviousLeaveOtherReason objects
        if previous_leave_type == PreviousLeaveOtherReason and api_previous_leave.leave_reason:
            new_previous_leave.leave_reason_id = PreviousLeaveQualifyingReason.get_id(
                api_previous_leave.leave_reason
            )

        db_session.add(new_previous_leave)


def add_or_update_phone(
    db_session: db.Session, phone: Optional[common_io.Phone], application: Application
) -> None:
    if not phone:
        return

    internationalized_phone_number = phone.e164

    # If Phone exists, update with what we have, otherwise, create a new Phone
    # if process_masked_phone_number did not remove the phone_number field, update the db
    if not application.phone:
        application.phone = Phone()

    application.phone.phone_type_id = (
        PhoneType.get_id(phone.phone_type) if phone.phone_type else None
    )
    if internationalized_phone_number:
        # This check is here because if the phone_number was removed by de-masking, this value would still be None
        # As a result, this field can't be set to None, because there is ambiguity in whether a None is intentional or
        # the result of de-masking. Investigate making fields like this nullable in TODO (CP-1530)
        application.phone.phone_number = internationalized_phone_number

    db_session.add(application.phone)


def get_or_add_tax_identifier(
    db_session: db.Session, body: ApplicationRequestBody
) -> Optional[TaxIdentifier]:
    tax_identifier = body.tax_identifier

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


def claim_is_valid_for_application_import(
    db_session: db.Session, user: User, claim: Optional[Claim]
) -> Optional[Response]:
    if claim is not None and (claim.employee_tax_identifier is None or claim.employer_fein is None):
        message = "Claim data incomplete for application import."
        validation_error = ValidationErrorDetail(message=message, type=IssueType.conflicting)
        error = response_util.error_response(Conflict, message=message, errors=[validation_error])
        return error
    if claim:
        existing_application = (
            db_session.query(Application)
            .filter(Application.claim_id == claim.claim_id)
            .one_or_none()
        )
        if existing_application and existing_application.user_id != user.user_id:
            message = "An application linked to a different account already exists for this claim."
            validation_error = ValidationErrorDetail(
                message=message, type=IssueType.exists, field="absence_case_id"
            )
            logger.info(
                "applications_import failure - exists_different_account",
                extra=get_application_log_attributes(existing_application),
            )
            return response_util.error_response(
                Forbidden, message=message, errors=[validation_error]
            )

        if existing_application:
            message = "An application already exists for this claim."
            validation_error = ValidationErrorDetail(
                message=message, type=IssueType.duplicate, field="absence_case_id"
            )
            logger.info(
                "applications_import failure - exists_same_account",
                extra=get_application_log_attributes(existing_application),
            )
            return response_util.error_response(
                Forbidden, message=message, errors=[validation_error]
            )
    return None


def set_application_fields_from_db_claim(
    fineos: AbstractFINEOSClient, application: Application, claim: Claim, db_session: db.Session
) -> None:
    """
    Set Application core fields using Claim
    """
    application.claim_id = claim.claim_id
    application.tax_identifier_id = claim.employee.tax_identifier_id
    application.tax_identifier = claim.employee.tax_identifier  # type: ignore
    application.employer_fein = claim.employer_fein
    application.imported_from_fineos_at = utcnow()


def set_customer_detail_fields(
    fineos: AbstractFINEOSClient,
    fineos_web_id: str,
    application: Application,
    db_session: db.Session,
) -> None:
    """
    Retrieve customer details from FINEOS and set for application fields
    """
    details = fineos.read_customer_details(fineos_web_id)

    application.first_name = details.firstName
    application.middle_name = details.secondName
    application.last_name = details.lastName
    application.date_of_birth = details.dateOfBirth

    if details.gender is not None:
        db_gender = (
            db_session.query(LkGender)
            .filter(LkGender.fineos_gender_description == details.gender)
            .one_or_none()
        )
        if db_gender is not None:
            application.gender_id = db_gender.gender_id

    has_state_id = False
    if details.classExtensionInformation is not None:
        mass_id = next(
            (info for info in details.classExtensionInformation if info.name == "MassachusettsID"),
            None,
        )
        if mass_id is not None and mass_id.stringValue != "" and mass_id.stringValue is not None:
            application.mass_id = str(mass_id.stringValue).upper()
            has_state_id = True
    application.has_state_id = has_state_id

    if isinstance(details.customerAddress, massgov.pfml.fineos.models.customer_api.CustomerAddress):
        # Convert CustomerAddress to ApiAddress, in order to use add_or_update_address
        address_to_create = ApiAddress(
            line_1=details.customerAddress.address.addressLine1,
            line_2=details.customerAddress.address.addressLine2,
            city=details.customerAddress.address.addressLine4,
            state=details.customerAddress.address.addressLine6,
            zip=details.customerAddress.address.postCode,
        )
        add_or_update_address(db_session, address_to_create, AddressType.RESIDENTIAL, application)


def _parse_continuous_leave_period(
    application_id: UUID, absence_period: AbsencePeriod
) -> ContinuousLeavePeriod:
    return ContinuousLeavePeriod(
        application_id=application_id,
        start_date=absence_period.startDate,
        end_date=absence_period.endDate,
    )


def _parse_intermittent_leave_period(
    application_id: UUID, absence_period: AbsencePeriod
) -> IntermittentLeavePeriod:
    leave_period = IntermittentLeavePeriod()
    if absence_period.episodicLeavePeriodDetail is None:
        error = ValueError("Episodic absence period is missing episodicLeavePeriodDetail")
        raise error
    leave_period.application_id = application_id
    leave_period.start_date = absence_period.startDate
    leave_period.end_date = absence_period.endDate

    episodic_detail = absence_period.episodicLeavePeriodDetail
    leave_period.frequency = episodic_detail.frequency
    leave_period.frequency_interval = episodic_detail.frequencyInterval
    leave_period.frequency_interval_basis = episodic_detail.frequencyIntervalBasis
    leave_period.duration = episodic_detail.duration
    leave_period.duration_basis = episodic_detail.durationBasis

    return leave_period


def _parse_reduced_leave_period(
    application_id: UUID,
    absence_period: AbsencePeriod,
    absenceDays: List[AbsenceDay],
    is_multiple_leave: bool,
) -> ReducedScheduleLeavePeriod:
    # set default to 0
    off_minutes: Dict[str, int] = {
        "Sunday": 0,
        "Monday": 0,
        "Tuesday": 0,
        "Wednesday": 0,
        "Thursday": 0,
        "Friday": 0,
        "Saturday": 0,
    }
    start_date = absence_period.startDate
    end_date = absence_period.endDate
    week_list = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]

    for absence_day in absenceDays:
        if not week_list:
            break
        if not absence_day.date or not start_date or not end_date:
            break

        target_date = absence_day.date
        if is_date_contained((start_date, end_date), target_date):
            weekday = target_date.strftime("%A")
            if absence_day.timeRequested:
                off_minutes[weekday] = round(float(absence_day.timeRequested) * 60)
                if weekday in week_list:
                    week_list.remove(weekday)
        elif not is_multiple_leave:
            newrelic_util.log_and_capture_exception(
                "Parse reduced leave: absence_day.date is outside the date range of the leave",
                extra={"application_id": application_id},
            )

    return ReducedScheduleLeavePeriod(
        application_id=application_id,
        start_date=absence_period.startDate,
        end_date=absence_period.endDate,
        sunday_off_minutes=off_minutes["Sunday"],
        monday_off_minutes=off_minutes["Monday"],
        tuesday_off_minutes=off_minutes["Tuesday"],
        wednesday_off_minutes=off_minutes["Wednesday"],
        thursday_off_minutes=off_minutes["Thursday"],
        friday_off_minutes=off_minutes["Friday"],
        saturday_off_minutes=off_minutes["Saturday"],
    )


def _set_continuous_leave_periods(
    application: Application, absence_details: AbsenceDetails
) -> None:

    continuous_leave_periods: List[ContinuousLeavePeriod] = []

    if absence_details.absencePeriods:
        for absence_period in absence_details.absencePeriods:
            if (
                absence_period.absenceType
                == AbsencePeriodType.CONTINUOUS.absence_period_type_description
            ):
                continuous_leave = _parse_continuous_leave_period(
                    application.application_id, absence_period
                )
                continuous_leave_periods.append(continuous_leave)

    application.continuous_leave_periods = continuous_leave_periods
    application.has_continuous_leave_periods = len(continuous_leave_periods) > 0


def _set_intermittent_leave_periods(
    application: Application, absence_details: AbsenceDetails
) -> None:
    intermittent_leave_periods: List[IntermittentLeavePeriod] = []

    if absence_details.absencePeriods:
        for absence_period in absence_details.absencePeriods:
            if (
                absence_period.absenceType
                == AbsencePeriodType.INTERMITTENT.absence_period_type_description
                or absence_period.absenceType
                == AbsencePeriodType.EPISODIC.absence_period_type_description
            ):

                intermittent_leave = _parse_intermittent_leave_period(
                    application.application_id, absence_period
                )
                intermittent_leave_periods.append(intermittent_leave)
    application.intermittent_leave_periods = intermittent_leave_periods
    application.has_intermittent_leave_periods = len(intermittent_leave_periods) > 0


def _set_reduced_leave_periods(application: Application, absence_details: AbsenceDetails) -> None:
    reduced_schedule_leave_periods: List[ReducedScheduleLeavePeriod] = []

    if absence_details.absencePeriods:
        for absence_period in absence_details.absencePeriods:
            if (
                absence_period.absenceType
                == AbsencePeriodType.REDUCED_SCHEDULE.absence_period_type_description
                and absence_details.absenceDays
            ):
                reduced_leave = _parse_reduced_leave_period(
                    application.application_id,
                    absence_period,
                    absence_details.absenceDays,
                    bool(len(absence_details.absencePeriods)),
                )
                reduced_schedule_leave_periods.append(reduced_leave)

    application.has_reduced_schedule_leave_periods = len(reduced_schedule_leave_periods) > 0
    application.reduced_schedule_leave_periods = reduced_schedule_leave_periods


def _set_has_future_child_date(
    application: Application, imported_absence_period: AbsencePeriod
) -> None:
    if (
        application.leave_reason_id == DBLeaveReason.CHILD_BONDING.leave_reason_id
        and imported_absence_period.status == AbsencePeriodStatus.ESTIMATED.value
    ):
        application.has_future_child_date = True
    else:
        application.has_future_child_date = False


def _get_open_absence_period(absence_details: AbsenceDetails) -> Optional[AbsencePeriod]:
    if absence_details.absencePeriods:
        for absence_period in absence_details.absencePeriods:
            if (
                absence_period.requestStatus
                == LeaveRequestDecision.PENDING.leave_request_decision_description
            ):
                return absence_period
    return None


def _get_latest_absence_period(absence_details: AbsenceDetails) -> Optional[AbsencePeriod]:
    if absence_details.absencePeriods is None:
        return None
    absence_periods = sorted(absence_details.absencePeriods, key=lambda x: x.startDate)  # type: ignore
    if len(absence_periods) > 0:
        return absence_periods[-1]
    return None


def _get_absence_period_from_absence_details(
    absence_details: AbsenceDetails, application: Application
) -> Optional[AbsencePeriod]:
    """
    return Open Absence Period if there is one
    if there isn't an open absence period the application is considered
    completed and the function returns the latest closed absence period
    if there is one
    """
    if absence_details.absencePeriods is None:
        return None
    absence_period = _get_open_absence_period(absence_details)
    if absence_period is None:
        application.completed_time = utcnow()
        absence_period = _get_latest_absence_period(absence_details)

    if len(absence_details.absencePeriods) > 1:
        logger.info(
            "multiple absence periods found during application import",
            extra={
                "application_id": application.application_id,
                "absence_case_id": (
                    application.claim.fineos_absence_id if application.claim else None
                ),
                "absence_period_attributes": get_absence_period_log_attributes(
                    absence_details.absencePeriods, absence_period
                ),
            },
        )

    return absence_period


def set_application_absence_and_leave_period(
    fineos: AbstractFINEOSClient, fineos_web_id: str, application: Application, absence_id: str
) -> None:
    absence_details = fineos.get_absence(fineos_web_id, absence_id)

    absence_period = _get_absence_period_from_absence_details(absence_details, application)
    if absence_period is not None:
        if absence_period.reason is not None:
            try:
                leave_reason_id = DBLeaveReason.get_id(absence_period.reason)
            except KeyError:
                logger.warning(
                    "Unsupported leave reason on absence period from FINEOS",
                    extra={
                        "fineos_web_id": fineos_web_id,
                        "reason": absence_period.reason,
                        "absence_case_id": (
                            application.claim.fineos_absence_id if application.claim else None
                        ),
                    },
                    exc_info=True,
                )
                raise ValidationException(
                    errors=[
                        ValidationErrorDetail(
                            type=IssueType.invalid,
                            message="Absence period reason is not supported.",
                            field="leave_details.reason",
                        )
                    ]
                )
            application.leave_reason_id = leave_reason_id
        if absence_period.reasonQualifier1 is not None:
            application.leave_reason_qualifier_id = LeaveReasonQualifier.get_id(
                absence_period.reasonQualifier1
            )
        application.pregnant_or_recent_birth = (
            application.leave_reason_id == DBLeaveReason.PREGNANCY_MATERNITY.leave_reason_id
        )
        _set_has_future_child_date(application, absence_period)

    # TODO (PORTAL-2009) Use same absence period(s) as the one selected above
    _set_continuous_leave_periods(application, absence_details)
    _set_intermittent_leave_periods(application, absence_details)
    _set_reduced_leave_periods(application, absence_details)
    application.submitted_time = absence_details.creationDate


def minutes_from_hours_minutes(hours: int, minutes: int) -> int:
    return hours * 60 + minutes


def set_employment_status_and_occupations(
    fineos_client: AbstractFINEOSClient, fineos_web_id: str, application: Application
) -> None:
    occupations = fineos_client.get_customer_occupations_customer_api(
        fineos_web_id, application.tax_identifier.tax_identifier
    )
    if len(occupations) == 0:
        return
    occupation = occupations[0]
    if occupation.employmentStatus is not None:
        if occupation.employmentStatus != EmploymentStatus.EMPLOYED.fineos_label:
            logger.info(
                "Did not import unsupported employment status from FINEOS",
                extra={
                    "fineos_web_id": fineos_web_id,
                    "status": occupation.employmentStatus,
                    "absence_case_id": (
                        application.claim.fineos_absence_id if application.claim else None
                    ),
                },
            )
            raise ValidationException(
                errors=[
                    ValidationErrorDetail(
                        type=IssueType.invalid,
                        message="Employment Status must be Active",
                        field="employment_status",
                    )
                ]
            )
        else:
            application.employment_status_id = EmploymentStatus.EMPLOYED.employment_status_id
    if occupation.hoursWorkedPerWeek is not None:
        application.hours_worked_per_week = Decimal(occupation.hoursWorkedPerWeek)
    if occupation.occupationId is None:
        return

    fineos_work_patterns = None
    try:
        fineos_work_patterns = fineos_client.get_week_based_work_pattern(
            fineos_web_id, occupation.occupationId
        )
    except exception.FINEOSForbidden:
        # Known FINEOS limitation, where it responds with a 403 for Variable work pattern types
        logger.info(
            "Received FINEOS forbidden response when getting week-based work pattern.",
            extra={
                "absence_case_id": application.claim.fineos_absence_id
                if application.claim
                else None,
                "occupationId": occupation.occupationId,
            },
        )

    if fineos_work_patterns is None:
        return

    if fineos_work_patterns.workPatternType != WorkPatternType.FIXED.work_pattern_type_description:
        newrelic_util.log_and_capture_exception(
            f"Application work pattern type is not {WorkPatternType.FIXED.work_pattern_type_description}",
            extra={"fineos_work_pattern_type": fineos_work_patterns.workPatternType},
        )
        return
    db_work_pattern_days = []
    work_pattern = WorkPattern(work_pattern_type_id=WorkPatternType.FIXED.work_pattern_type_id)
    for pattern in fineos_work_patterns.workPatternDays:
        db_work_pattern_days.append(
            WorkPatternDay(
                day_of_week_id=DayOfWeek.get_id(pattern.dayOfWeek),
                minutes=minutes_from_hours_minutes(pattern.hours, pattern.minutes),
            )
        )
    work_pattern.work_pattern_days = db_work_pattern_days
    application.work_pattern = work_pattern


def set_payment_preference_fields(
    fineos: massgov.pfml.fineos.AbstractFINEOSClient,
    fineos_web_id: str,
    application: Application,
    db_session: db.Session,
) -> None:
    """
    Retrieve payment preferences from FINEOS and set for imported application fields
    """
    preferences = fineos.get_payment_preferences(fineos_web_id)

    if not preferences:
        application.has_submitted_payment_preference = False
        return

    # Take the one with isDefault=True, otherwise take first one
    preference = next(
        (pref for pref in preferences if pref.isDefault and pref.paymentMethod != ""),
        preferences[0],
    )

    payment_preference = None
    has_submitted_payment_preference = False
    if preference.accountDetails is not None:
        payment_preference = PaymentPreference(
            account_number=preference.accountDetails.accountNo,
            routing_number=FinancialRoutingNumber(preference.accountDetails.routingNumber),
            bank_account_type=BankAccountType(preference.accountDetails.accountType),
            payment_method=CommonPaymentMethod(preference.paymentMethod),
        )
    elif preference.paymentMethod == PaymentMethod.CHECK.payment_method_description:
        payment_preference = PaymentPreference(
            payment_method=CommonPaymentMethod(preference.paymentMethod),
        )
    if payment_preference is not None:
        add_or_update_payment_preference(db_session, payment_preference, application)
        has_submitted_payment_preference = True
    application.has_submitted_payment_preference = has_submitted_payment_preference

    has_mailing_address = False
    if isinstance(
        preference.customerAddress, massgov.pfml.fineos.models.customer_api.CustomerAddress
    ):
        # Convert CustomerAddress to ApiAddress, in order to use add_or_update_address
        address_to_create = ApiAddress(
            line_1=preference.customerAddress.address.addressLine1,
            line_2=preference.customerAddress.address.addressLine2,
            city=preference.customerAddress.address.addressLine4,
            state=preference.customerAddress.address.addressLine6,
            zip=preference.customerAddress.address.postCode,
        )
        add_or_update_address(db_session, address_to_create, AddressType.MAILING, application)
        has_mailing_address = True

    if preference.paymentMethod is None:
        application.has_submitted_payment_preference = False

    application.has_mailing_address = has_mailing_address


def create_common_io_phone_from_fineos(
    phone: PhoneNumber, db_session: db.Session
) -> Optional[common_io.Phone]:
    """
    Creates common.io Phone object from FINEOS PhoneNumber object
    """
    db_phone = (
        db_session.query(LkPhoneType)
        .filter(LkPhoneType.phone_type_description == phone.phoneNumberType)
        .one_or_none()
    )

    if not db_phone:
        newrelic_util.log_and_capture_exception(
            f"Unable to find phone_type: {phone.phoneNumberType}",
            extra={"phone_type": phone.phoneNumberType},
        )
        return None

    phone_to_create = common_io.Phone(
        int_code=phone.intCode,
        phone_number=f"{phone.areaCode}{phone.telephoneNo}",
        phone_type=db_phone.phone_type_description,
    )
    return phone_to_create


def set_customer_contact_detail_fields(
    fineos: massgov.pfml.fineos.AbstractFINEOSClient,
    fineos_web_id: str,
    application: Application,
    db_session: db.Session,
) -> None:
    """
    Retrieves customer contact details from FINEOS, creates a new phone record,
    and associates the phone record with the application being imported
    """
    contact_details = fineos.read_customer_contact_details(fineos_web_id)

    if not contact_details or not contact_details.phoneNumbers:
        logger.info("No contact details returned from FINEOS")
        return

    mfa_phone_number = None
    for phone_num in contact_details.phoneNumbers:
        country_code = phone_num.intCode if phone_num.intCode else "1"
        fineos_phone = f"+{country_code}{phone_num.areaCode}{phone_num.telephoneNo}"
        if application.user.mfa_phone_number == fineos_phone:
            mfa_phone_number = fineos_phone

    preferred_phone_number = next(
        (phone_num for phone_num in contact_details.phoneNumbers if phone_num.preferred),
        contact_details.phoneNumbers[0],
    )

    if (
        mfa_phone_number is None
        or application.user.mfa_delivery_preference_id
        != MFADeliveryPreference.SMS.mfa_delivery_preference_id
    ):
        logger.info(
            "application import failure - phone number mismatch / no SMS phone available ",
            extra={
                "absence_case_id": application.claim.fineos_absence_id
                if application.claim
                else None,
                "mfa_delivery_preference_id": application.user.mfa_delivery_preference_id,
            },
        )
        raise ValidationException(
            errors=[
                ValidationErrorDetail(
                    type=IssueType.incorrect,
                    message="Code 3: An issue occurred while trying to import the application.",
                )
            ]
        )

    # Handles the potential case of a phone number list existing, but phone fields are null
    if not (
        preferred_phone_number.intCode
        or preferred_phone_number.areaCode
        or preferred_phone_number.telephoneNo
    ):
        logger.info(
            "Field missing from FINEOS phoneNumber list",
            extra={"phoneNumbers": str(preferred_phone_number)},
        )
        return

    phone_to_create = create_common_io_phone_from_fineos(preferred_phone_number, db_session)
    add_or_update_phone(db_session, phone_to_create, application)


def customer_get_eform(
    fineos: AbstractFINEOSClient,
    fineos_web_id: str,
    absence_id: str,
    eform_id: int,
    eform_cache: EFORM_CACHE,
) -> EForm:
    if eform_id in eform_cache:
        return eform_cache[eform_id]
    eform = fineos.customer_get_eform(fineos_web_id, absence_id, eform_id)
    eform_cache[eform_id] = eform
    return eform


def set_other_leaves(
    fineos: AbstractFINEOSClient,
    fineos_web_id: str,
    application: Application,
    db_session: db.Session,
    absence_id: str,
    eform_summaries: Optional[List[EFormSummary]] = None,
    eform_cache: Optional[EFORM_CACHE] = None,
) -> None:
    """
    Retrieve other leaves from FINEOS and set for imported application fields
    """
    if eform_summaries is None:
        eform_summaries = fineos.customer_get_eform_summary(fineos_web_id, absence_id)

    if eform_cache is None:
        eform_cache = {}

    for summary in eform_summaries:
        if summary.eformType != EformTypes.OTHER_LEAVES:
            continue

        previous_leaves: List[common_io.PreviousLeave] = []
        concurrent_leave: Optional[common_io.ConcurrentLeave] = None

        eform = customer_get_eform(fineos, fineos_web_id, absence_id, summary.eformId, eform_cache)

        concurrent_leave = TransformConcurrentLeaveFromOtherLeaveEform.from_fineos(eform)
        application.has_concurrent_leave = concurrent_leave is not None
        set_concurrent_leave(db_session, concurrent_leave, application)

        previous_leaves = TransformPreviousLeaveFromOtherLeaveEform.from_fineos(eform)
        # Separate previous leaves according to type
        other_leaves: List[common_io.PreviousLeave] = []
        same_leaves: List[common_io.PreviousLeave] = []
        for previous_leave in previous_leaves:
            if previous_leave.type == "other_reason":
                other_leaves.append(previous_leave)
            elif previous_leave.type == "same_reason":
                same_leaves.append(previous_leave)

        application.has_previous_leaves_other_reason = len(other_leaves) > 0
        application.has_previous_leaves_same_reason = len(same_leaves) > 0
        set_previous_leaves(
            db_session,
            other_leaves,
            application,
            "other_reason",
        )
        set_previous_leaves(
            db_session,
            same_leaves,
            application,
            "same_reason",
        )


BENEFITS_EFORM_TYPES = [EformTypes.OTHER_INCOME, EformTypes.OTHER_INCOME_V2]


def set_employer_benefits_from_fineos(
    fineos: AbstractFINEOSClient,
    fineos_web_id: str,
    application: Application,
    db_session: db.Session,
    absence_id: str,
    eform_summaries: Optional[List[EFormSummary]] = None,
    eform_cache: Optional[EFORM_CACHE] = None,
) -> None:
    employer_benefits: List[common_io.EmployerBenefit] = []
    if eform_summaries is None:
        eform_summaries = fineos.customer_get_eform_summary(fineos_web_id, absence_id)

    if eform_cache is None:
        eform_cache = {}

    for eform_summary in eform_summaries:
        if eform_summary.eformType not in BENEFITS_EFORM_TYPES:
            continue

        eform = customer_get_eform(
            fineos, fineos_web_id, absence_id, eform_summary.eformId, eform_cache
        )

        if eform_summary.eformType == EformTypes.OTHER_INCOME:
            employer_benefits.extend(
                other_income
                for other_income in TransformOtherIncomeEform.from_fineos(eform)
                if other_income.program_type == "Employer"
            )

        elif eform_summary.eformType == EformTypes.OTHER_INCOME_V2:
            employer_benefits.extend(
                TransformEmployerBenefitsFromOtherIncomeEform.from_fineos(eform)
            )
    application.has_employer_benefits = len(employer_benefits) > 0
    set_employer_benefits(db_session, employer_benefits, application)


def set_other_incomes_from_fineos(
    fineos: AbstractFINEOSClient,
    fineos_web_id: str,
    application: Application,
    db_session: db.Session,
    absence_id: str,
    eform_summaries: Optional[List[EFormSummary]] = None,
    eform_cache: Optional[EFORM_CACHE] = None,
) -> None:
    other_incomes: List[apps_common_io.OtherIncome] = []
    if eform_summaries is None:
        eform_summaries = fineos.customer_get_eform_summary(fineos_web_id, absence_id)

    if eform_cache is None:
        eform_cache = {}

    for eform_summary in eform_summaries:
        if eform_summary.eformType != EformTypes.OTHER_INCOME_V2:
            continue

        eform = customer_get_eform(
            fineos, fineos_web_id, absence_id, eform_summary.eformId, eform_cache
        )
        other_incomes.extend(
            [
                income
                for income in TransformOtherIncomeNonEmployerEform.from_fineos(eform)
                if income.income_type in set(apps_common_io.OtherIncomeType)
            ]
        )
    application.has_other_incomes = len(other_incomes) > 0
    set_other_incomes(db_session, other_incomes, application)


LeavePeriod = Union[
    ContinuousLeavePeriod, IntermittentLeavePeriod, ReducedScheduleLeavePeriod, ConcurrentLeave
]


def _split_leave_period(
    leave_period: LeavePeriod, split_date: date, new_application: Application
) -> Tuple[Optional[LeavePeriod], Optional[LeavePeriod]]:
    start_date: Optional[date]
    end_date: Optional[date]

    if isinstance(leave_period, ConcurrentLeave):
        start_date = leave_period.leave_start_date
        end_date = leave_period.leave_end_date
    else:
        start_date = leave_period.start_date
        end_date = leave_period.end_date

    if not start_date or not end_date:
        # This case should not be encountered in reality, but columns are technically nullable
        # If any values are missing, the leave period cannot be split
        raise Exception("Leave period cannot be split as it does not have start and end dates")

    (start_end_dates_before_split, start_end_dates_after_split) = split_start_end_dates(
        start_date, end_date, split_date
    )

    if not start_end_dates_after_split:
        return (leave_period, None)

    new_leave_period: LeavePeriod
    if isinstance(leave_period, ConcurrentLeave):
        new_leave_period = leave_period.copy(
            leave_start_date=start_end_dates_after_split.start_date,
            leave_end_date=start_end_dates_after_split.end_date,
            application_id=new_application.application_id,
        )
    else:
        new_leave_period = leave_period.copy(
            start_date=start_end_dates_after_split.start_date,
            end_date=start_end_dates_after_split.end_date,
            application_id=new_application.application_id,
        )

    if not start_end_dates_before_split:
        return (None, new_leave_period)

    if isinstance(leave_period, ConcurrentLeave):
        leave_period.leave_start_date = start_end_dates_before_split.start_date
        leave_period.leave_end_date = start_end_dates_before_split.end_date
    else:
        leave_period.start_date = start_end_dates_before_split.start_date
        leave_period.end_date = start_end_dates_before_split.end_date
    return (leave_period, new_leave_period)


def _split_benefit(
    benefit: Union[EmployerBenefit, OtherIncome], split_date: date, new_application: Application
) -> Tuple[
    Optional[Union[EmployerBenefit, OtherIncome]], Optional[Union[EmployerBenefit, OtherIncome]]
]:
    start_date: Optional[date]
    end_date: Optional[date]
    amount: Optional[Decimal]
    frequency: LkAmountFrequency
    if isinstance(benefit, EmployerBenefit):
        start_date = benefit.benefit_start_date
        end_date = benefit.benefit_end_date
        amount = benefit.benefit_amount_dollars
        frequency = benefit.benefit_amount_frequency
    else:
        start_date = benefit.income_start_date
        end_date = benefit.income_end_date
        amount = benefit.income_amount_dollars
        frequency = benefit.income_amount_frequency

    if not start_date or not end_date or not amount or not frequency:
        # This case should not be encountered in reality, but columns are technically nullable
        # If any values are missing, the benefit cannot be split
        raise Exception("Unable to split benefit or income as it was missing the required fields")

    (start_end_dates_before_split, start_end_dates_after_split) = split_start_end_dates(
        start_date, end_date, split_date
    )

    if not start_end_dates_after_split:
        return (benefit, None)

    new_benefit: Union[EmployerBenefit, OtherIncome]
    if isinstance(benefit, EmployerBenefit):
        new_benefit = benefit.copy(
            benefit_start_date=start_end_dates_after_split.start_date,
            benefit_end_date=start_end_dates_after_split.end_date,
            application_id=new_application.application_id,
        )
    else:
        new_benefit = benefit.copy(
            income_start_date=start_end_dates_after_split.start_date,
            income_end_date=start_end_dates_after_split.end_date,
            application_id=new_application.application_id,
        )

    if not start_end_dates_before_split:
        return (None, new_benefit)

    before_split_amount: Optional[Decimal] = None
    after_split_amount: Optional[Decimal] = None
    if frequency.amount_frequency_id == AmountFrequency.ALL_AT_ONCE.amount_frequency_id:
        totals_days_in_benefit = (end_date - start_date).days + 1
        days_before_split = (
            start_end_dates_before_split.end_date - start_end_dates_before_split.start_date
        ).days + 1
        days_after_split = days_after_split = (
            start_end_dates_after_split.end_date - start_end_dates_after_split.start_date
        ).days + 1
        before_split_amount = round(amount * Decimal(days_before_split / totals_days_in_benefit), 2)
        after_split_amount = round(amount * Decimal(days_after_split / totals_days_in_benefit), 2)

    if isinstance(benefit, EmployerBenefit) and isinstance(new_benefit, EmployerBenefit):
        benefit.benefit_start_date = start_end_dates_before_split.start_date
        benefit.benefit_end_date = start_end_dates_before_split.end_date
        if before_split_amount and after_split_amount:
            benefit.benefit_amount_dollars = before_split_amount
            new_benefit.benefit_amount_dollars = after_split_amount
    elif isinstance(benefit, OtherIncome) and isinstance(new_benefit, OtherIncome):
        benefit.income_start_date = start_end_dates_before_split.start_date
        benefit.income_end_date = start_end_dates_before_split.end_date
        if before_split_amount and after_split_amount:
            benefit.income_amount_dollars = before_split_amount
            new_benefit.income_amount_dollars = after_split_amount

    return (benefit, new_benefit)


def split_application_by_date(
    db_session: db.Session, application: Application, date_to_split_on: date
) -> Tuple[Application, Application]:
    application_after_split_date = application.copy()
    db_session.add(application_after_split_date)
    # Flush the new application to the database so it has an id
    db_session.flush()
    application_before_split_date = application

    # Set the split by
    application_after_split_date.split_from_application_id = (
        application_before_split_date.application_id
    )

    continuous_leave_periods_after_split_date = []
    intermittent_leave_periods_after_split_date = []
    reduced_schedule_leave_periods_after_split_date = []
    for leave_period in application_before_split_date.all_leave_periods:
        try:
            (leave_period_before_split_date, leave_period_after_split_date) = _split_leave_period(
                leave_period, date_to_split_on, application_after_split_date
            )
        except Exception:
            logger.exception("Unable to split leave period")
            continue
        if isinstance(leave_period, ContinuousLeavePeriod):
            if leave_period_after_split_date:
                continuous_leave_periods_after_split_date.append(leave_period_after_split_date)
            if not leave_period_before_split_date:
                db_session.delete(leave_period)
                application_before_split_date.continuous_leave_periods.remove(leave_period)
        elif isinstance(leave_period, IntermittentLeavePeriod):
            if leave_period_after_split_date:
                intermittent_leave_periods_after_split_date.append(leave_period_after_split_date)
            if not leave_period_before_split_date:
                db_session.delete(leave_period)
                application_before_split_date.intermittent_leave_periods.remove(leave_period)
        elif isinstance(leave_period, ReducedScheduleLeavePeriod):
            if leave_period_after_split_date:
                reduced_schedule_leave_periods_after_split_date.append(
                    leave_period_after_split_date
                )
            if not leave_period_before_split_date:
                db_session.delete(leave_period)
                application_before_split_date.reduced_schedule_leave_periods.remove(leave_period)
    application_after_split_date.continuous_leave_periods = (
        continuous_leave_periods_after_split_date
    )
    application_after_split_date.intermittent_leave_periods = (
        intermittent_leave_periods_after_split_date
    )
    application_after_split_date.reduced_schedule_leave_periods = (
        reduced_schedule_leave_periods_after_split_date
    )

    # Re-calcuate the boolean values after splitting the leave periods
    application_after_split_date.has_continuous_leave_periods = (
        len(application_after_split_date.continuous_leave_periods) != 0
    )
    application_after_split_date.has_intermittent_leave_periods = (
        len(application_after_split_date.intermittent_leave_periods) != 0
    )
    application_after_split_date.has_reduced_schedule_leave_periods = (
        len(application_after_split_date.reduced_schedule_leave_periods) != 0
    )

    application_before_split_date.has_continuous_leave_periods = (
        len(application_before_split_date.continuous_leave_periods) != 0
    )
    application_before_split_date.has_intermittent_leave_periods = (
        len(application_before_split_date.intermittent_leave_periods) != 0
    )
    application_before_split_date.has_reduced_schedule_leave_periods = (
        len(application_before_split_date.reduced_schedule_leave_periods) != 0
    )

    # an application can only have a single concurrent leave
    # and is not returned by Application.all_leave_periods
    if application_before_split_date.has_concurrent_leave:
        try:
            (leave_period_before_split_date, leave_period_after_split_date) = _split_leave_period(
                application_before_split_date.concurrent_leave,
                date_to_split_on,
                application_after_split_date,
            )
        except Exception:
            logger.exception("Unable to split concurrent leave")
        if leave_period_after_split_date:
            application_after_split_date.concurrent_leave = leave_period_after_split_date
            application_after_split_date.has_concurrent_leave = True
        else:
            application_after_split_date.has_concurrent_leave = False

        if not leave_period_before_split_date:
            db_session.delete(application_before_split_date.concurrent_leave)
            application_before_split_date.concurrent_leave = None  # type: ignore
            application_before_split_date.has_concurrent_leave = False

    for benefit in application_before_split_date.employer_benefits:
        try:
            (benefit_before_split_date, benefit_after_split_date) = _split_benefit(
                benefit, date_to_split_on, application_after_split_date
            )
        except Exception:
            logger.exception("Unable to split employer benefit")
            continue
        if benefit_after_split_date and isinstance(benefit_after_split_date, EmployerBenefit):
            application_after_split_date.employer_benefits.append(benefit_after_split_date)
        if not benefit_before_split_date:
            db_session.delete(benefit)
            application_before_split_date.employer_benefits.remove(benefit)

    # Re-calculate the has_employer benefits boolean
    application_after_split_date.has_employer_benefits = (
        len(application_after_split_date.employer_benefits) != 0
    )
    application_before_split_date.has_employer_benefits = (
        len(application_before_split_date.employer_benefits) != 0
    )

    for income in application_before_split_date.other_incomes:
        try:
            (income_before_split_date, income_after_split_date) = _split_benefit(
                income, date_to_split_on, application_after_split_date
            )
        except Exception:
            logger.exception("Unable to split other income")
            continue
        if income_after_split_date and isinstance(income_after_split_date, OtherIncome):
            application_after_split_date.other_incomes.append(income_after_split_date)
        if not income_before_split_date:
            db_session.delete(income)
            application_before_split_date.other_incomes.remove(income)

    application_after_split_date.has_other_incomes = (
        len(application_after_split_date.other_incomes) != 0
    )
    application_before_split_date.has_other_incomes = (
        len(application_before_split_date.other_incomes) != 0
    )

    return (application_before_split_date, application_after_split_date)


@dataclass
class StartEndDates:
    start_date: date
    end_date: date


SplitLeaveResults = Tuple[Optional[StartEndDates], Optional[StartEndDates]]


def split_start_end_dates(start_date: date, end_date: date, split_date: date) -> SplitLeaveResults:
    """
    Splits a start and end date into two separate date ranges around the past in split_date.
    If the start date comes after the end date the dates cannot be split.
    """
    if start_date > end_date:
        return (None, None)

    if start_date > split_date and end_date > split_date:
        return (None, StartEndDates(start_date, end_date))
    elif start_date <= split_date and end_date <= split_date:
        return (StartEndDates(start_date, end_date), None)
    elif start_date == split_date:
        return (
            StartEndDates(start_date, start_date),
            StartEndDates(start_date + timedelta(days=1), end_date),
        )
    else:
        return (
            StartEndDates(start_date, split_date),
            StartEndDates(split_date + timedelta(days=1), end_date),
        )


@dataclass
class ApplicationSplit:
    crossed_benefit_year: BenefitYear
    application_dates_in_benefit_year: StartEndDates
    application_dates_outside_benefit_year: StartEndDates
    application_outside_benefit_year_submittable_on: date


def get_application_split(
    application: Application,
    db_session: db.Session,
) -> Optional[ApplicationSplit]:
    """
    If a leave period spans a benefit year, the application needs to be broken up into
    separate ones that will each get submitted.
    """
    if application.split_from_application_id is not None:
        return None

    latest_end_date = get_latest_end_date(application)
    earliest_start_date = get_earliest_start_date(application)
    if earliest_start_date is None or latest_end_date is None:
        return None

    if not application.employee:
        return None

    crossed_benefit_year = get_crossed_benefit_year(
        application.employee.employee_id, earliest_start_date, latest_end_date, db_session
    )

    if crossed_benefit_year is None:
        return None

    [dates_in_benefit_year, dates_outside_benefit_year] = split_start_end_dates(
        earliest_start_date, latest_end_date, crossed_benefit_year.end_date
    )
    if dates_in_benefit_year is None or dates_outside_benefit_year is None:
        return None

    return ApplicationSplit(
        crossed_benefit_year=crossed_benefit_year,
        application_dates_in_benefit_year=dates_in_benefit_year,
        application_dates_outside_benefit_year=dates_outside_benefit_year,
        application_outside_benefit_year_submittable_on=get_earliest_submission_date(
            dates_outside_benefit_year.start_date
        ),
    )


def get_crossed_benefit_year(
    employee_id: UUID, start_date: date, end_date: date, db_session: db.Session
) -> Optional[BenefitYear]:

    # Find any benefit year for the employee where the end_date falls between
    # the leave start and end dates, excluding a benefit year end_date equals
    # the leave end_date since benefit years are inclusive
    by = (
        db_session.query(BenefitYear)
        .filter(
            BenefitYear.employee_id == employee_id,
            BenefitYear.end_date.between(start_date, end_date),
            BenefitYear.end_date != end_date,
        )
        .one_or_none()
    )

    return by
