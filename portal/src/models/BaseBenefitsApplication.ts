import { compact, get, map } from "lodash";
import LeaveReason from "./LeaveReason";
import formatDateRange from "../utils/formatDateRange";

export interface BaseLeavePeriod {
  start_date: string;
  end_date: string;
}

/**
 * The API's Applications table and the data we return for the Leave Admin
 * info request flow share a few common fields, which this model includes
 * helper methods for. Separate models then extend this.
 */
abstract class BaseBenefitsApplication {
  abstract first_name: string | null;
  abstract middle_name: string | null;
  abstract last_name: string | null;
  abstract leave_details: {
    continuous_leave_periods: BaseLeavePeriod[];
    intermittent_leave_periods: BaseLeavePeriod[];
    reduced_schedule_leave_periods: BaseLeavePeriod[];
    reason: string;
  };

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

export default BaseBenefitsApplication;
