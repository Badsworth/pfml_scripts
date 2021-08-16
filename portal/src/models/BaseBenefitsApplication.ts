/* eslint sort-keys: ["error", "asc"] */
import { compact, get, map } from "lodash";

import Address from "./Address";
import BaseModel from "./BaseModel";
import LeaveReason from "./LeaveReason";
import formatDateRange from "../utils/formatDateRange";

/**
 * The API's Applications table and the data we return for the Leave Admin
 * info request flow share a common set of fields, which this model represents.
 * Separate models then extend this.
 */
class BaseBenefitsApplication extends BaseModel {
  // @ts-expect-error ts-migrate(2416) FIXME: Property 'defaults' in type 'BaseBenefitsApplicati... Remove this comment to see the full error message
  get defaults() {
    return {
      application_id: null,
      concurrent_leave: null,
      created_at: null,
      date_of_birth: null,
      // array of EmployerBenefit objects. See the EmployerBenefit model
      employer_benefits: [],
      employer_fein: null,
      fineos_absence_id: null,
      first_name: null,
      gender: null,
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
      // @ts-expect-error ts-migrate(2554) FIXME: Expected 1 arguments, but got 0.
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
   * Returns the start and end dates of the specific continuous leave period in a
   * human-readable format. Ex: "1/1/2021 - 6/1/2021".
   * @returns {string} a representation of the leave period
   */
  continuousLeaveDateRange() {
    const { start_date, end_date } = get(
      this,
      `leave_details.continuous_leave_periods[0]`
    );
    // @ts-expect-error ts-migrate(2554) FIXME: Expected 3 arguments, but got 2.
    return formatDateRange(start_date, end_date);
  }

  /**
   * Determine if claim is an intermittent leave claim
   * @returns {boolean}
   */
  get isIntermittent() {
    return !!get(this, "leave_details.intermittent_leave_periods[0]");
  }

  /**
   * Returns the start and end dates of the specific intermittent leave period in a
   * human-readable format. Ex: "1/1/2021 - 6/1/2021".
   * @returns {string} a representation of the leave period
   */
  intermittentLeaveDateRange() {
    const { start_date, end_date } = get(
      this,
      `leave_details.intermittent_leave_periods[0]`
    );
    // @ts-expect-error ts-migrate(2554) FIXME: Expected 3 arguments, but got 2.
    return formatDateRange(start_date, end_date);
  }

  /**
   * Determine if claim is a reduced schedule leave claim
   * @returns {boolean}
   */
  get isReducedSchedule() {
    return !!get(this, "leave_details.reduced_schedule_leave_periods[0]");
  }

  /**
   * Returns the start and end dates of the specific reduced schedule leave period in a
   * human-readable format. Ex: "1/1/2021 - 6/1/2021".
   * @returns {string} a representation of the leave period
   */
  reducedLeaveDateRange() {
    const { start_date, end_date } = get(
      this,
      `leave_details.reduced_schedule_leave_periods[0]`
    );
    // @ts-expect-error ts-migrate(2554) FIXME: Expected 3 arguments, but got 2.
    return formatDateRange(start_date, end_date);
  }

  /**
   * Returns full name accounting for any false values
   * @returns {string}
   */
  get fullName() {
    // @ts-expect-error ts-migrate(2339) FIXME: Property 'first_name' does not exist on type 'Base... Remove this comment to see the full error message
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

export default BaseBenefitsApplication;
