import BaseBenefitsApplication, {
  BaseLeavePeriod,
} from "./BaseBenefitsApplication";
import Address from "./Address";
import ConcurrentLeave from "./ConcurrentLeave";
import EmployerBenefit from "./EmployerBenefit";
import { IntermittentLeavePeriod } from "./BenefitsApplication";
import PreviousLeave from "./PreviousLeave";
import { merge } from "lodash";

/**
 * This model represents a Claim record that is formed from data directly pulled
 * from the Claims Processing System (CPS). This should not be confused with a record
 * from the API's Claims table, which is represented by the Claim model.
 * TODO (EMPLOYER-1130): Rename this model to clarify this nuance.
 */
class EmployerClaim extends BaseBenefitsApplication {
  employer_id: string;
  fineos_absence_id: string;
  created_at: string;

  first_name: string | null = null;
  middle_name: string | null = null;
  last_name: string | null = null;
  concurrent_leave: ConcurrentLeave | null = null;
  employer_benefits: EmployerBenefit[] = [];
  date_of_birth: string | null = null;
  employer_fein: string;
  employer_dba: string;
  follow_up_date: string | null = null;
  hours_worked_per_week: number | null = null;
  is_reviewable: boolean | null = null;
  residential_address: Address = new Address({});
  status: string | null = null;
  tax_identifier: string | null = null;
  previous_leaves: PreviousLeave[] = [];
  // does this claim use the old or new version of other leave / income eforms?
  // Todo(EMPLOYER-1453): remove V1 eform functionality
  uses_second_eform_version: boolean;

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
  }
}

export default EmployerClaim;
