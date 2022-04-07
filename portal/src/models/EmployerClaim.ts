import BaseBenefitsApplication, {
  BaseLeavePeriod,
} from "./BaseBenefitsApplication";
import { AbsencePeriod } from "./AbsencePeriod";
import Address from "./Address";
import ConcurrentLeave from "./ConcurrentLeave";
import EmployerBenefit from "./EmployerBenefit";
import { IntermittentLeavePeriod } from "./BenefitsApplication";
import { ManagedRequirement } from "../models/ManagedRequirement";
import PreviousLeave from "./PreviousLeave";
import isBlank from "../utils/isBlank";
import { isReviewable } from "src/utils/isReviewable";
import { merge } from "lodash";

/**
 * This model represents a Claim record that is formed from data directly pulled
 * from the Claims Processing System (CPS). This should not be confused with a record
 * from the API's Claims table, which is represented by the Claim model.
 * TODO (PORTAL-477): Rename this model to clarify this nuance.
 */
class EmployerClaim extends BaseBenefitsApplication {
  absence_periods: AbsencePeriod[];
  employer_id: string;
  fineos_absence_id: string;
  created_at: string;
  first_name: string | null = null;
  middle_name: string | null = null;
  last_name: string | null = null;
  concurrent_leave: ConcurrentLeave | null = null;
  employer_benefits: EmployerBenefit[];
  date_of_birth: string | null = null;
  employer_fein: string;
  employer_dba: string | null;
  hours_worked_per_week: number | null = null;
  managed_requirements: ManagedRequirement[] = [];
  residential_address: Address;
  status: string;
  tax_identifier: string | null = null;
  previous_leaves: PreviousLeave[];
  // does this claim use the old or new version of other leave / income eforms?
  // Todo(EMPLOYER-1453): remove V1 eform functionality
  uses_second_eform_version: boolean;

  computed_start_dates: {
    other_reason: string | null;
    same_reason: string | null;
  };

  leave_details: {
    continuous_leave_periods: BaseLeavePeriod[];
    employer_notification_date: string | null;
    intermittent_leave_periods: IntermittentLeavePeriod[];
    reason: string | null;
    reduced_schedule_leave_periods: BaseLeavePeriod[];
  };

  constructor(attrs: Partial<EmployerClaim>) {
    super();
    // Recursively merge with the defaults
    merge(this, attrs);

    this.absence_periods = this.absence_periods.map(
      (absence_period) => new AbsencePeriod(absence_period)
    );
  }

  /**
   * Note we use a utility method to share logic across EmployerClaim and Claim
   * until such time where we combine these methods (PORTAL-477 pending)
   */
  get is_reviewable() {
    return isReviewable(this.absence_periods, this.managed_requirements);
  }

  get lastReviewedAt(): string | undefined {
    if (this.managed_requirements?.length) {
      const nonBlankDates = this.managed_requirements
        .map((managedRequirement) => managedRequirement.responded_at)
        .filter((date): date is string => !isBlank(date))
        .sort();

      return nonBlankDates.length ? nonBlankDates[0] : undefined;
    }
  }

  get wasPreviouslyReviewed(): boolean {
    if (this.managed_requirements?.length) {
      return this.managed_requirements.some((managedRequirement) => {
        // "Suppressed" indicates the managed requirement has been been closed, but doesn't mean it was *reviewed*
        return managedRequirement.status === "Complete";
      });
    }

    return false;
  }

  /**
   * Returns earliest start date across all absence periods
   */
  get leaveStartDate() {
    const startDates: string[] = this.absence_periods
      .map((period) => period.absence_period_start_date)
      .sort();

    if (!startDates.length) return null;

    return startDates[0];
  }

  /**
   * Returns latest end date across all absence periods
   */
  get leaveEndDate() {
    const endDates: string[] = this.absence_periods
      .map((period) => period.absence_period_end_date)
      .sort();

    if (!endDates.length) return null;

    return endDates[endDates.length - 1];
  }
}

export default EmployerClaim;
