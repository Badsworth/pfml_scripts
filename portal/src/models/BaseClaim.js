/* eslint sort-keys: ["error", "asc"] */
/**
 * @file Benefits application model and enum values
 */
import { compact, get, map } from "lodash";
import Address from "./Address";
import BaseModel from "./BaseModel";
import LeaveReason from "./LeaveReason";

class BaseClaim extends BaseModel {
  get defaults() {
    return {
      application_id: null,
      created_at: null,
      date_of_birth: null,
      // array of EmployerBenefit objects. See the EmployerBenefit model
      employer_benefits: [],
      employer_fein: null,
      fineos_absence_id: null,
      first_name: null,
      hours_worked_per_week: null,
      last_name: null,
      leave_details: {
        continuous_leave_periods: null,
        employer_notification_date: null,
        intermittent_leave_periods: null,
        reason: null,
        reduced_schedule_leave_periods: null,
      },
      middle_name: null,
      // array of PreviousLeave objects. See the PreviousLeave model
      previous_leaves: [],
      residential_address: new Address(),
      status: null,
      tax_identifier: null,
    };
  }

  /**
   * Determine if claim is a Bonding Leave claim
   * @returns {boolean}
   */
  get isBondingLeave() {
    return get(this, "leave_details.reason") === LeaveReason.bonding;
  }

  /**
   * Determine if claim is a continuous leave claim
   * @returns {boolean}
   */
  get isContinuous() {
    return !!get(this, "leave_details.continuous_leave_periods[0]");
  }

  /**
   * Determine if claim is an intermittent leave claim
   * @returns {boolean}
   */
  get isIntermittent() {
    return !!get(this, "leave_details.intermittent_leave_periods[0]");
  }

  /**
   * Determine if claim is a reduced schedule leave claim
   * @returns {boolean}
   */
  get isReducedSchedule() {
    return !!get(this, "leave_details.reduced_schedule_leave_periods[0]");
  }

  /**
   * Returns full name accounting for any false values
   * @returns {string}
   */
  get fullName() {
    return compact([this.first_name, this.middle_name, this.last_name]).join(
      " "
    );
  }

  /**
   * Returns earliest start date across all leave periods
   * @returns {string}
   */
  get leaveStartDate() {
    const periods = [
      get(this, "leave_details.continuous_leave_periods"),
      get(this, "leave_details.intermittent_leave_periods"),
      get(this, "leave_details.reduced_schedule_leave_periods"),
    ].flat();

    const startDates = map(compact(periods), "start_date").sort();

    if (!startDates.length) return null;

    return startDates[0];
  }

  /**
   * Returns latest end date across all leave periods
   * @returns {string}
   */
  get leaveEndDate() {
    const periods = [
      get(this, "leave_details.continuous_leave_periods"),
      get(this, "leave_details.intermittent_leave_periods"),
      get(this, "leave_details.reduced_schedule_leave_periods"),
    ].flat();

    const endDates = map(compact(periods), "end_date").sort();

    if (!endDates.length) return null;

    return endDates[endDates.length - 1];
  }
}

/**
 * Enums for status field
 * @enum {string}
 */
export const AdjudicationStatusType = {
  approved: "Approved",
  pending: "Undecided",
  denied: "Declined",
};

export default BaseClaim;
