import { LeaveReasonType } from "./LeaveReason";
import { ValuesOf } from "../../types/common";
import { groupBy } from "lodash";

export const AbsencePeriodRequestDecision = {
  approved: "Approved",
  cancelled: "Cancelled",
  denied: "Denied",
  inReview: "In Review",
  pending: "Pending",
  // Projected is (at least) used for Bonding Leave periods created automatically
  // for periods with Birth Disability as the reason qualifier
  projected: "Projected",
  voided: "Voided",
  withdrawn: "Withdrawn",
} as const;

export type AbsencePeriodRequestDecisionEnum = ValuesOf<
  typeof AbsencePeriodRequestDecision
>;

export type AbsencePeriodTypes =
  | "Continuous"
  | "Intermittent"
  | "Reduced Schedule";

export class AbsencePeriod {
  absence_period_end_date: string;
  absence_period_start_date: string;
  fineos_leave_request_id: string | null = null;
  period_type: AbsencePeriodTypes;
  reason: LeaveReasonType;
  reason_qualifier_one = "";
  reason_qualifier_two = "";
  request_decision: AbsencePeriodRequestDecisionEnum;

  constructor(attrs: Partial<AbsencePeriod> = {}) {
    Object.assign(this, attrs);
  }

  static groupByReason(absence_periods: AbsencePeriod[]): {
    [reason: string]: AbsencePeriod[];
  } {
    return groupBy(absence_periods, "reason");
  }

  /**
   * @returns periods sorted newest to oldest (by start date)
   */
  static sortNewToOld(absence_periods: AbsencePeriod[]): AbsencePeriod[] {
    const periods = absence_periods.slice(); // avoids mutating the original array
    return periods.sort((a, b) => {
      return a.absence_period_start_date > b.absence_period_start_date ? -1 : 1;
    });
  }
}
