from dataclasses import dataclass
from datetime import date
from typing import Any, Dict, List, Optional, Set

from pydantic.types import UUID4

import massgov.pfml.util.datetime as datetime_util
import massgov.pfml.util.logging
from massgov.pfml.db.models.employees import AbsencePeriod, BenefitYear, Employer

logger = massgov.pfml.util.logging.get_logger(__name__)

AbsencePeriodID = UUID4
BenefitYearID = UUID4
EmployerID = UUID4


@dataclass
class LeaveDurationResult:
    benefit_year_id: BenefitYearID
    benefit_year_start_date: date
    benefit_year_end_date: date
    employer_id: EmployerID
    fineos_employer_id: Optional[int]
    duration: int


class LeaveCalculator:
    """
        Calculate leave data per benefit year for an employee
    """

    benefit_year_absences: Dict[BenefitYearID, Set[AbsencePeriodID]]
    consolidated_leave: Dict[BenefitYearID, Dict[EmployerID, int]]
    benefit_years: Dict[BenefitYearID, BenefitYear]
    employers: Dict[EmployerID, Employer]

    def __init__(
        self,
        benefit_years: Optional[List[BenefitYear]] = None,
        log_extra: Optional[Dict[str, Optional[Any]]] = None,
    ):
        self.benefit_year_absences = {}
        self.consolidated_leave = {}
        self.log_extra = log_extra if log_extra else {}

        # Allows BenefitYear and Employer data to be readily available
        # in benefit years exceeding threshold results
        self.benefit_years = (
            {by.benefit_year_id: by for by in benefit_years} if benefit_years else {}
        )
        self.employers = {}

    def set_benefit_year_absence_periods(self, absence_periods: List[AbsencePeriod]) -> None:
        """
        For each benefit year track absence periods and the total leave
        duration per employer.
        """
        for benefit_year in self.benefit_years.values():
            for absence_period in absence_periods:
                self.set_benefit_year_absence_period(benefit_year, absence_period)

    def set_benefit_year_absence_period(
        self, benefit_year: BenefitYear, absence_period: AbsencePeriod
    ) -> None:
        """
        If the absence period start and end dates listed on the claim
        associated with the absence period are fully contained within the
        start and end dates of the benefit year, track the absence period
        and the total leave duration per employer with the benefit year.
        """

        if (
            not absence_period.claim
            or not absence_period.claim.absence_period_start_date
            or not absence_period.claim.employer_id
            or not absence_period.claim.employer
            or not absence_period.claim.employer.fineos_employer_id
            or not absence_period.absence_period_start_date
            or not absence_period.absence_period_end_date
        ):
            self.log_extra["absence_period_id"] = absence_period.absence_period_id
            logger.warning(
                "Skipping absence period with missing data", self.log_extra,
            )
            return

        if not datetime_util.is_date_contained(
            (benefit_year.start_date, benefit_year.end_date),
            absence_period.claim.absence_period_start_date,
        ):
            return

        # Track benefit years that have been seen in the case this
        # benefit year was not provided during initialization.
        benefit_year_id = benefit_year.benefit_year_id
        if benefit_year_id not in self.benefit_years:
            self.benefit_years[benefit_year_id] = benefit_year

        # Track absence periods by benefit year to prevent recounting
        # the leave duration for an absence period
        if benefit_year_id not in self.benefit_year_absences:
            self.benefit_year_absences[benefit_year_id] = set()

        if absence_period.absence_period_id in self.benefit_year_absences[benefit_year_id]:
            return
        self.benefit_year_absences[benefit_year_id].add(absence_period.absence_period_id)

        # Track leave duration per employee by benefit year
        if benefit_year_id not in self.consolidated_leave:
            self.consolidated_leave[benefit_year_id] = dict()
        employer_id: UUID4 = absence_period.claim.employer_id

        absence_period_start_date = absence_period.absence_period_start_date
        absence_period_end_date = absence_period.absence_period_end_date

        if employer_id not in self.consolidated_leave[benefit_year_id]:
            self.consolidated_leave[benefit_year_id][employer_id] = 0
        duration = absence_period_end_date - absence_period_start_date

        # Additional day added to include the first day of leave in the duration
        self.consolidated_leave[benefit_year_id][employer_id] += duration.days + 1

        # Track employers that have been seen
        if employer_id not in self.employers:
            self.employers[employer_id] = absence_period.claim.employer

    def benefit_years_exceeding_threshold(self, threshold: int) -> List[LeaveDurationResult]:
        """ For each benefit year, check if the total leave durations for any employer
            exceeds the maximum total leave duration threshold.
        """

        benefit_years_exceeding_threshold: List[LeaveDurationResult] = []
        for benefit_year_id, employers_leave_duration in self.consolidated_leave.items():
            if benefit_year_id not in self.benefit_years:
                continue
            benefit_year = self.benefit_years[benefit_year_id]
            for employer_id, days_leave in employers_leave_duration.items():
                if employer_id not in self.employers:
                    continue
                employer = self.employers[employer_id]
                if days_leave > threshold:
                    benefit_years_exceeding_threshold.append(
                        LeaveDurationResult(
                            benefit_year_id,
                            benefit_year.start_date,
                            benefit_year.end_date,
                            employer_id,
                            employer.fineos_employer_id,
                            days_leave,
                        )
                    )
        return benefit_years_exceeding_threshold
