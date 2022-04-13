from decimal import Decimal
from typing import Dict, List, Optional

import massgov
import massgov.pfml.api.models.applications.common as apps_common_io
import massgov.pfml.api.models.common as common_io
import massgov.pfml.util.logging
import massgov.pfml.util.newrelic.events as newrelic_util
from massgov.pfml import db
from massgov.pfml.api.models.applications.common import Address as ApiAddress
from massgov.pfml.api.models.applications.common import PaymentMethod as CommonPaymentMethod
from massgov.pfml.api.models.applications.common import PaymentPreference
from massgov.pfml.api.services.administrator_fineos_actions import EformTypes
from massgov.pfml.api.services.applications import (
    add_or_update_address,
    add_or_update_payment_preference,
    add_or_update_phone,
    set_concurrent_leave,
    set_employer_benefits,
    set_other_incomes,
    set_previous_leaves,
)
from massgov.pfml.api.validation.exceptions import (
    IssueType,
    ValidationErrorDetail,
    ValidationException,
)
from massgov.pfml.db.models.absences import AbsencePeriodType
from massgov.pfml.db.models.applications import (
    Application,
    ContinuousLeavePeriod,
    DayOfWeek,
    EmploymentStatus,
    IntermittentLeavePeriod,
)
from massgov.pfml.db.models.applications import LeaveReason as DBLeaveReason
from massgov.pfml.db.models.applications import (
    LeaveReasonQualifier,
    LkPhoneType,
    ReducedScheduleLeavePeriod,
    WorkPattern,
    WorkPatternDay,
    WorkPatternType,
)
from massgov.pfml.db.models.employees import (
    AddressType,
    Claim,
    LeaveRequestDecision,
    LkGender,
    MFADeliveryPreference,
    PaymentMethod,
)
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
from massgov.pfml.util.logging.applications import get_absence_period_log_attributes

logger = massgov.pfml.util.logging.get_logger(__name__)

EFORM_CACHE = Dict[int, EForm]
BENEFITS_EFORM_TYPES = [EformTypes.OTHER_INCOME, EformTypes.OTHER_INCOME_V2]


def minutes_from_hours_minutes(hours: int, minutes: int) -> int:
    return hours * 60 + minutes


class ApplicationImportService:
    def __init__(
        self,
        fineos_client: AbstractFINEOSClient,
        fineos_web_id: str,
        application: Application,
        db_session: db.Session,
        claim: Claim,
        absence_case_id: str,
    ):
        self.fineos_client = fineos_client
        self.fineos_web_id = fineos_web_id
        self.application = application
        self.db_session = db_session
        self.claim = claim
        self.absence_case_id = absence_case_id

    def import_data(self):
        """
        Top level handler for executing application import
        """
        self._set_application_fields_from_db_claim()
        self._set_application_absence_and_leave_period()
        self._set_customer_detail_fields()
        self._set_customer_contact_detail_fields()
        self._set_employment_status_and_occupations()
        self._set_payment_preference_fields()
        eform_summaries = self.fineos_client.customer_get_eform_summary(
            self.fineos_web_id, self.absence_case_id
        )
        eform_cache: EFORM_CACHE = {}
        self._set_other_leaves(eform_summaries, eform_cache)
        self._set_employer_benefits_from_fineos(eform_summaries, eform_cache)
        self._set_other_incomes_from_fineos(eform_summaries, eform_cache)

    def _set_application_fields_from_db_claim(self) -> None:
        self.application.claim_id = self.claim.claim_id
        self.application.tax_identifier_id = self.claim.employee.tax_identifier_id
        self.application.tax_identifier = self.claim.employee.tax_identifier  # type: ignore
        self.application.employer_fein = self.claim.employer_fein
        self.application.imported_from_fineos_at = utcnow()

    def _set_application_absence_and_leave_period(self) -> None:
        absence_details = self.fineos_client.get_absence(self.fineos_web_id, self.absence_case_id)

        absence_period = self._get_absence_period_from_absence_details(absence_details)
        if absence_period is not None:
            if absence_period.reason is not None:
                try:
                    leave_reason_id = DBLeaveReason.get_id(absence_period.reason)
                except KeyError:
                    logger.warning(
                        "Unsupported leave reason on absence period from FINEOS",
                        extra={
                            "fineos_web_id": self.fineos_web_id,
                            "reason": absence_period.reason,
                            "absence_case_id": (
                                self.application.claim.fineos_absence_id
                                if self.application.claim
                                else None
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
                self.application.leave_reason_id = leave_reason_id
            if absence_period.reasonQualifier1 is not None:
                self.application.leave_reason_qualifier_id = LeaveReasonQualifier.get_id(
                    absence_period.reasonQualifier1
                )
            self.application.pregnant_or_recent_birth = (
                self.application.leave_reason_id
                == DBLeaveReason.PREGNANCY_MATERNITY.leave_reason_id
            )
            self._set_has_future_child_date(absence_period)

        # TODO (PORTAL-2009) Use same absence period(s) as the one selected above
        self._set_continuous_leave_periods(absence_details)
        self._set_intermittent_leave_periods(absence_details)
        self._set_reduced_leave_periods(absence_details)
        self.application.submitted_time = absence_details.creationDate

    def _get_absence_period_from_absence_details(
        self, absence_details: AbsenceDetails
    ) -> Optional[AbsencePeriod]:
        """
        return Open Absence Period if there is one
        if there isn't an open absence period the application is considered
        completed and the function returns the latest closed absence period
        if there is one
        """
        if absence_details.absencePeriods is None:
            return None
        absence_period = self._get_open_absence_period(absence_details)
        if absence_period is None:
            self.application.completed_time = utcnow()
            absence_period = self._get_latest_absence_period(absence_details)

        if len(absence_details.absencePeriods) > 1:
            logger.info(
                "multiple absence periods found during application import",
                extra={
                    "application_id": self.application.application_id,
                    "absence_case_id": (
                        self.application.claim.fineos_absence_id if self.application.claim else None
                    ),
                    "absence_period_attributes": get_absence_period_log_attributes(
                        absence_details.absencePeriods, absence_period
                    ),
                },
            )

        return absence_period

    def _set_has_future_child_date(self, imported_absence_period: AbsencePeriod) -> None:
        if (
            self.application.leave_reason_id == DBLeaveReason.CHILD_BONDING.leave_reason_id
            and imported_absence_period.status == AbsencePeriodStatus.ESTIMATED.value
        ):
            self.application.has_future_child_date = True
        else:
            self.application.has_future_child_date = False

    def _set_continuous_leave_periods(self, absence_details: AbsenceDetails) -> None:

        continuous_leave_periods: List[ContinuousLeavePeriod] = []

        if absence_details.absencePeriods:
            for absence_period in absence_details.absencePeriods:
                if (
                    absence_period.absenceType
                    == AbsencePeriodType.CONTINUOUS.absence_period_type_description
                ):
                    continuous_leave = self._parse_continuous_leave_period(absence_period)
                    continuous_leave_periods.append(continuous_leave)

        self.application.continuous_leave_periods = continuous_leave_periods
        self.application.has_continuous_leave_periods = len(continuous_leave_periods) > 0

    def _parse_intermittent_leave_period(
        self, absence_period: AbsencePeriod
    ) -> IntermittentLeavePeriod:
        leave_period = IntermittentLeavePeriod()
        if absence_period.episodicLeavePeriodDetail is None:
            error = ValueError("Episodic absence period is missing episodicLeavePeriodDetail")
            raise error
        leave_period.application_id = self.application.application_id
        leave_period.start_date = absence_period.startDate
        leave_period.end_date = absence_period.endDate

        episodic_detail = absence_period.episodicLeavePeriodDetail
        leave_period.frequency = episodic_detail.frequency
        leave_period.frequency_interval = episodic_detail.frequencyInterval
        leave_period.frequency_interval_basis = episodic_detail.frequencyIntervalBasis
        leave_period.duration = episodic_detail.duration
        leave_period.duration_basis = episodic_detail.durationBasis

        return leave_period

    def _set_intermittent_leave_periods(self, absence_details: AbsenceDetails) -> None:
        intermittent_leave_periods: List[IntermittentLeavePeriod] = []

        if absence_details.absencePeriods:
            for absence_period in absence_details.absencePeriods:
                if (
                    absence_period.absenceType
                    == AbsencePeriodType.INTERMITTENT.absence_period_type_description
                    or absence_period.absenceType
                    == AbsencePeriodType.EPISODIC.absence_period_type_description
                ):

                    intermittent_leave = self._parse_intermittent_leave_period(absence_period)
                    intermittent_leave_periods.append(intermittent_leave)
        self.application.intermittent_leave_periods = intermittent_leave_periods
        self.application.has_intermittent_leave_periods = len(intermittent_leave_periods) > 0

    def _set_reduced_leave_periods(self, absence_details: AbsenceDetails) -> None:
        reduced_schedule_leave_periods: List[ReducedScheduleLeavePeriod] = []

        if absence_details.absencePeriods:
            for absence_period in absence_details.absencePeriods:
                if (
                    absence_period.absenceType
                    == AbsencePeriodType.REDUCED_SCHEDULE.absence_period_type_description
                    and absence_details.absenceDays
                ):
                    reduced_leave = self._parse_reduced_leave_period(
                        absence_period,
                        absence_details.absenceDays,
                        bool(len(absence_details.absencePeriods)),
                    )
                    reduced_schedule_leave_periods.append(reduced_leave)

        self.application.has_reduced_schedule_leave_periods = (
            len(reduced_schedule_leave_periods) > 0
        )
        self.application.reduced_schedule_leave_periods = reduced_schedule_leave_periods

    def _get_open_absence_period(self, absence_details: AbsenceDetails) -> Optional[AbsencePeriod]:
        if absence_details.absencePeriods:
            for absence_period in absence_details.absencePeriods:
                if (
                    absence_period.requestStatus
                    == LeaveRequestDecision.PENDING.leave_request_decision_description
                ):
                    return absence_period
        return None

    def _get_latest_absence_period(
        self, absence_details: AbsenceDetails
    ) -> Optional[AbsencePeriod]:
        if absence_details.absencePeriods is None:
            return None
        absence_periods = sorted(absence_details.absencePeriods, key=lambda x: x.startDate)  # type: ignore
        if len(absence_periods) > 0:
            return absence_periods[-1]
        return None

    def _parse_continuous_leave_period(
        self, absence_period: AbsencePeriod
    ) -> ContinuousLeavePeriod:
        return ContinuousLeavePeriod(
            application_id=self.application.application_id,
            start_date=absence_period.startDate,
            end_date=absence_period.endDate,
        )

    def _parse_reduced_leave_period(
        self,
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
                    extra={"application_id": self.application.application_id},
                )

        return ReducedScheduleLeavePeriod(
            application_id=self.application.application_id,
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

    def _set_customer_detail_fields(self) -> None:
        """
        Retrieve customer details from FINEOS and set for application fields
        """
        details = self.fineos_client.read_customer_details(self.fineos_web_id)

        self.application.first_name = details.firstName
        self.application.middle_name = details.secondName
        self.application.last_name = details.lastName
        self.application.date_of_birth = details.dateOfBirth

        if details.gender is not None:
            db_gender = (
                self.db_session.query(LkGender)
                .filter(LkGender.fineos_gender_description == details.gender)
                .one_or_none()
            )
            if db_gender is not None:
                self.application.gender_id = db_gender.gender_id

        has_state_id = False
        if details.classExtensionInformation is not None:
            mass_id = next(
                (
                    info
                    for info in details.classExtensionInformation
                    if info.name == "MassachusettsID"
                ),
                None,
            )
            if (
                mass_id is not None
                and mass_id.stringValue != ""
                and mass_id.stringValue is not None
            ):
                self.application.mass_id = str(mass_id.stringValue).upper()
                has_state_id = True
        self.application.has_state_id = has_state_id

        if isinstance(
            details.customerAddress, massgov.pfml.fineos.models.customer_api.CustomerAddress
        ):
            # Convert CustomerAddress to ApiAddress, in order to use add_or_update_address
            address_to_create = ApiAddress(
                line_1=details.customerAddress.address.addressLine1,
                line_2=details.customerAddress.address.addressLine2,
                city=details.customerAddress.address.addressLine4,
                state=details.customerAddress.address.addressLine6,
                zip=details.customerAddress.address.postCode,
            )
            add_or_update_address(
                self.db_session, address_to_create, AddressType.RESIDENTIAL, self.application
            )

    def _set_customer_contact_detail_fields(self) -> None:
        """
        Retrieves customer contact details from FINEOS, creates a new phone record,
        and associates the phone record with the application being imported
        """
        contact_details = self.fineos_client.read_customer_contact_details(self.fineos_web_id)

        if not contact_details or not contact_details.phoneNumbers:
            logger.info("No contact details returned from FINEOS")
            return

        mfa_phone_number = None
        for phone_num in contact_details.phoneNumbers:
            country_code = phone_num.intCode if phone_num.intCode else "1"
            fineos_phone = f"+{country_code}{phone_num.areaCode}{phone_num.telephoneNo}"
            if self.application.user.mfa_phone_number == fineos_phone:
                mfa_phone_number = fineos_phone

        preferred_phone_number = next(
            (phone_num for phone_num in contact_details.phoneNumbers if phone_num.preferred),
            contact_details.phoneNumbers[0],
        )
        if (
            mfa_phone_number is None
            or self.application.user.mfa_delivery_preference_id
            != MFADeliveryPreference.SMS.mfa_delivery_preference_id
        ):
            logger.info(
                "application import failure - phone number mismatch / no SMS phone available ",
                extra={
                    "absence_case_id": self.application.claim.fineos_absence_id
                    if self.application.claim
                    else None,
                    "mfa_delivery_preference_id": self.application.user.mfa_delivery_preference_id,
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

        phone_to_create = self._create_common_io_phone_from_fineos(preferred_phone_number)
        add_or_update_phone(self.db_session, phone_to_create, self.application)

    def _create_common_io_phone_from_fineos(self, phone: PhoneNumber) -> Optional[common_io.Phone]:
        """
        Creates common.io Phone object from FINEOS PhoneNumber object
        """
        db_phone = (
            self.db_session.query(LkPhoneType)
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

    def _set_employment_status_and_occupations(self) -> None:
        occupations = self.fineos_client.get_customer_occupations_customer_api(
            self.fineos_web_id, self.application.tax_identifier.tax_identifier
        )
        if len(occupations) == 0:
            return
        occupation = occupations[0]
        if occupation.employmentStatus is not None:
            if occupation.employmentStatus != EmploymentStatus.EMPLOYED.fineos_label:
                logger.info(
                    "Did not import unsupported employment status from FINEOS",
                    extra={
                        "fineos_web_id": self.fineos_web_id,
                        "status": occupation.employmentStatus,
                        "absence_case_id": (
                            self.application.claim.fineos_absence_id
                            if self.application.claim
                            else None
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
                self.application.employment_status_id = (
                    EmploymentStatus.EMPLOYED.employment_status_id
                )
        if occupation.hoursWorkedPerWeek is not None:
            self.application.hours_worked_per_week = Decimal(occupation.hoursWorkedPerWeek)
        if occupation.occupationId is None:
            return

        fineos_work_patterns = None
        try:
            fineos_work_patterns = self.fineos_client.get_week_based_work_pattern(
                self.fineos_web_id, occupation.occupationId
            )
        except exception.FINEOSForbidden:
            # Known FINEOS limitation, where it responds with a 403 for Variable work pattern types
            logger.info(
                "Received FINEOS forbidden response when getting week-based work pattern.",
                extra={
                    "absence_case_id": self.application.claim.fineos_absence_id
                    if self.application.claim
                    else None,
                    "occupationId": occupation.occupationId,
                },
            )

        if fineos_work_patterns is None:
            return

        if (
            fineos_work_patterns.workPatternType
            != WorkPatternType.FIXED.work_pattern_type_description
        ):
            logger.warning(
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
        self.application.work_pattern = work_pattern

    def _set_payment_preference_fields(self) -> None:
        """
        Retrieve payment preferences from FINEOS and set for imported application fields
        """
        preferences = self.fineos_client.get_payment_preferences(self.fineos_web_id)

        if not preferences:
            self.application.has_submitted_payment_preference = False
            return

        # Take the one with isDefault=True, otherwise take first one
        preference = next(
            (pref for pref in preferences if pref.isDefault and pref.paymentMethod),
            preferences[0],
        )

        payment_preference = None
        has_submitted_payment_preference = False
        if preference.accountDetails is not None:
            payment_preference = PaymentPreference(
                account_number=preference.accountDetails.accountNo,
                routing_number=preference.accountDetails.routingNumber,  # type: ignore
                bank_account_type=preference.accountDetails.accountType,  # type: ignore
                payment_method=preference.paymentMethod,  # type: ignore
            )
        elif preference.paymentMethod == PaymentMethod.CHECK.payment_method_description:
            payment_preference = PaymentPreference(
                payment_method=CommonPaymentMethod(preference.paymentMethod),
            )
        if payment_preference is not None:
            add_or_update_payment_preference(self.db_session, payment_preference, self.application)
            has_submitted_payment_preference = True
        self.application.has_submitted_payment_preference = has_submitted_payment_preference

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
            add_or_update_address(
                self.db_session, address_to_create, AddressType.MAILING, self.application
            )
            has_mailing_address = True

        if not preference.paymentMethod:
            self.application.has_submitted_payment_preference = False

        self.application.has_mailing_address = has_mailing_address

    def _set_other_leaves(
        self,
        eform_summaries: Optional[List[EFormSummary]] = None,
        eform_cache: Optional[EFORM_CACHE] = None,
    ) -> None:
        """
        Retrieve other leaves from FINEOS and set for imported application fields
        """
        if eform_summaries is None:
            eform_summaries = self.fineos_client.customer_get_eform_summary(
                self.fineos_web_id, self.absence_case_id
            )

        if eform_cache is None:
            eform_cache = {}

        for summary in eform_summaries:
            if summary.eformType != EformTypes.OTHER_LEAVES:
                continue

            previous_leaves: List[common_io.PreviousLeave] = []
            concurrent_leave: Optional[common_io.ConcurrentLeave] = None

            eform = self._customer_get_eform(summary.eformId, eform_cache)

            concurrent_leave = TransformConcurrentLeaveFromOtherLeaveEform.from_fineos(eform)
            self.application.has_concurrent_leave = concurrent_leave is not None
            set_concurrent_leave(self.db_session, concurrent_leave, self.application)

            previous_leaves = TransformPreviousLeaveFromOtherLeaveEform.from_fineos(eform)
            # Separate previous leaves according to type
            other_leaves: List[common_io.PreviousLeave] = []
            same_leaves: List[common_io.PreviousLeave] = []
            for previous_leave in previous_leaves:
                if previous_leave.type == "other_reason":
                    other_leaves.append(previous_leave)
                elif previous_leave.type == "same_reason":
                    same_leaves.append(previous_leave)

            self.application.has_previous_leaves_other_reason = len(other_leaves) > 0
            self.application.has_previous_leaves_same_reason = len(same_leaves) > 0
            set_previous_leaves(
                self.db_session,
                other_leaves,
                self.application,
                "other_reason",
            )
            set_previous_leaves(
                self.db_session,
                same_leaves,
                self.application,
                "same_reason",
            )

    def _customer_get_eform(
        self,
        eform_id: int,
        eform_cache: EFORM_CACHE,
    ) -> EForm:
        if eform_id in eform_cache:
            return eform_cache[eform_id]
        eform = self.fineos_client.customer_get_eform(
            self.fineos_web_id, self.absence_case_id, eform_id
        )
        eform_cache[eform_id] = eform
        return eform

    def _set_employer_benefits_from_fineos(
        self,
        eform_summaries: Optional[List[EFormSummary]] = None,
        eform_cache: Optional[EFORM_CACHE] = None,
    ) -> None:
        employer_benefits: List[common_io.EmployerBenefit] = []
        if eform_summaries is None:
            eform_summaries = self.fineos_client.customer_get_eform_summary(
                self.fineos_web_id, self.absence_case_id
            )

        if eform_cache is None:
            eform_cache = {}

        for eform_summary in eform_summaries:
            if eform_summary.eformType not in BENEFITS_EFORM_TYPES:
                continue

            eform = self._customer_get_eform(eform_summary.eformId, eform_cache)

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
        self.application.has_employer_benefits = len(employer_benefits) > 0
        set_employer_benefits(self.db_session, employer_benefits, self.application)

    def _set_other_incomes_from_fineos(
        self,
        eform_summaries: Optional[List[EFormSummary]] = None,
        eform_cache: Optional[EFORM_CACHE] = None,
    ) -> None:
        other_incomes: List[apps_common_io.OtherIncome] = []
        if eform_summaries is None:
            eform_summaries = self.fineos_client.customer_get_eform_summary(
                self.fineos_web_id, self.absence_case_id
            )

        if eform_cache is None:
            eform_cache = {}

        for eform_summary in eform_summaries:
            if eform_summary.eformType != EformTypes.OTHER_INCOME_V2:
                continue

            eform = self._customer_get_eform(eform_summary.eformId, eform_cache)
            other_incomes.extend(
                [
                    income
                    for income in TransformOtherIncomeNonEmployerEform.from_fineos(eform)
                    if income.income_type in set(apps_common_io.OtherIncomeType)
                ]
            )
        self.application.has_other_incomes = len(other_incomes) > 0
        set_other_incomes(self.db_session, other_incomes, self.application)
