import { compact, get } from "lodash";
import LeaveReason from "./LeaveReason";
import formatDateRange from "../utils/formatDateRange";
import tracker from "../services/tracker";

export interface BaseLeavePeriod {
  start_date: string | null;
  end_date: string | null;
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
    reason: string | null;
  };

  /**
   * Determine if claim is a Bonding Leave claim
   */
  get isBondingLeave(): boolean {
    return get(this, "leave_details.reason") === LeaveReason.bonding;
  }

  /**
   * Determine if claim is a continuous leave claim
   */
  get isContinuous(): boolean {
    return !!get(this, "leave_details.continuous_leave_periods[0]");
  }

  /**
   * Returns the start and end dates of the specific continuous leave period in a
   * human-readable format. Ex: "1/1/2021 - 6/1/2021".
   * @returns a representation of the leave period
   */
  continuousLeaveDateRange() {
    const { start_date, end_date } = get(
      this,
      `leave_details.continuous_leave_periods[0]`
    );
    return formatDateRange(start_date, end_date);
  }

  /**
   * Determine if claim is an intermittent leave claim
   */
  get isIntermittent(): boolean {
    return !!get(this, "leave_details.intermittent_leave_periods[0]");
  }

  /**
   * Returns the start and end dates of the specific intermittent leave period in a
   * human-readable format. Ex: "1/1/2021 - 6/1/2021".
   * @returns a representation of the leave period
   */
  intermittentLeaveDateRange() {
    const { start_date, end_date } = get(
      this,
      `leave_details.intermittent_leave_periods[0]`
    );
    return formatDateRange(start_date, end_date);
  }

  /**
   * Determine if claim is a reduced schedule leave claim
   */
  get isReducedSchedule(): boolean {
    return !!get(this, "leave_details.reduced_schedule_leave_periods[0]");
  }

  /**
   * Returns the start and end dates of the specific reduced schedule leave period in a
   * human-readable format. Ex: "1/1/2021 - 6/1/2021".
   * @returns a representation of the leave period
   */
  reducedLeaveDateRange() {
    const { start_date, end_date } = get(
      this,
      `leave_details.reduced_schedule_leave_periods[0]`
    );
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
   */
  get leaveStartDate() {
    const periods = [
      get(this, "leave_details.continuous_leave_periods"),
      get(this, "leave_details.intermittent_leave_periods"),
      get(this, "leave_details.reduced_schedule_leave_periods"),
    ].flat();

    const startDates: string[] = compact(periods)
      .map((period) => period.start_date)
      .sort();

    if (!startDates.length) return null;

    return startDates[0];
  }

  /**
   * Returns latest end date across all leave periods
   */
  get leaveEndDate() {
    const periods = [
      get(this, "leave_details.continuous_leave_periods"),
      get(this, "leave_details.intermittent_leave_periods"),
      get(this, "leave_details.reduced_schedule_leave_periods"),
    ].flat();

    const endDates: string[] = compact(periods)
      .map((period) => period.end_date)
      .sort();

    if (!endDates.length) return null;

    return endDates[endDates.length - 1];
  }

  /**
   * Returns a date a year before the start date (or Jan 1, 2021)
   */
  get otherLeaveStartDate(): string {
    const programLaunch = new Date("2021-01-01");
    const d = new Date(
      this.leaveStartDate ? this.leaveStartDate : programLaunch.toISOString()
    );
    console.log(d);
    if (!this.leaveStartDate) {
      return programLaunch.toISOString().split("T")[0];
    }

    // Handle invalid date edge-cases
    if (!(d instanceof Date) || isNaN(d.getTime())) {
      tracker.trackEvent("otherLeaveStartDate calculated invalid", {
        leaveStartDate: this.leaveStartDate,
      });
      return programLaunch.toISOString().split("T")[0];
    }

    // calculate a year before given date if given date is sunday
    // otherwise calculate a year before sunday prior to given date
    d.setDate(
      d.getDate() -
        d.getDay() - // minus days since Sunday
        364 // minus 52 weeks
    );

    // If calculated date is earlier, return the program start date
    if (d < programLaunch) {
      return programLaunch.toISOString().split("T")[0];
    }

    return d.toISOString().split("T")[0];
  }
}

export default BaseBenefitsApplication;
